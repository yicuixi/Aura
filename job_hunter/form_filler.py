"""
网页简历自动填写 — CDP + 单次LLM映射

1. CDP 连接用户 Edge → Playwright 打开目标页
2. JS 提取所有表单字段（label、type、options）
3. 一次 LLM 调用完成「简历 → 字段」映射
4. Playwright 逐字段填写

单次 LLM 调用，不截图，纯 DOM 操作。
"""

import asyncio
import json
import logging
import re
from typing import Optional

from playwright.async_api import async_playwright
from langchain_ollama import ChatOllama

from .config import Config, load_resume_data, DATA_DIR
from .models import Job

logger = logging.getLogger("job_hunter.form_filler")

# JS: 视觉位置匹配 label + 独立星号检测 required + 读取已有值
EXTRACT_JS = r"""
(() => {
    // Phase 1: label 候选池
    const labelPool = [];
    const tags = 'span,div,label,td,th,p,em,strong,b,dt,li,h1,h2,h3,h4,h5,h6,a';
    document.querySelectorAll(tags).forEach(el => {
        if (el.querySelector('input, select, textarea, button')) return;
        const text = (el.innerText || '').trim().replace(/\s+/g, ' ');
        if (text.length < 1 || text.length > 40) return;
        const rect = el.getBoundingClientRect();
        if (rect.width < 1 || rect.height < 1 || rect.width > 350) return;
        labelPool.push({
            text: text.replace(/^\*\s*/, '').trim(),
            right: rect.right, left: rect.left,
            top: rect.top, bottom: rect.bottom,
            cy: rect.top + rect.height / 2,
        });
    });

    // Phase 1.5: 独立收集「*」星号标记的位置（用于 required 检测）
    const starPool = [];
    document.querySelectorAll('span, em, i, b, strong, label, div').forEach(el => {
        const t = (el.innerText || '').trim();
        if (t !== '*' && t !== '＊' && !/^\*[^\*]/.test(t)) return;
        if (el.querySelector('input, select, textarea')) return;
        const rect = el.getBoundingClientRect();
        if (rect.width < 1) return;
        starPool.push({ cy: rect.top + rect.height / 2, right: rect.right, left: rect.left });
    });

    // Phase 2: 提取表单字段
    const fields = [];
    let idx = 0;

    document.querySelectorAll('input, select, textarea').forEach(el => {
        const type = (el.type || 'text').toLowerCase();
        if (['hidden', 'submit', 'button', 'image', 'reset', 'file'].includes(type)) return;
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0 && type !== 'radio' && type !== 'checkbox') return;

        el.setAttribute('data-jh', String(idx));
        const inputCy = rect.top + rect.height / 2;

        // 找最近 label
        let bestLabel = '', bestScore = 9999;
        for (const lbl of labelPool) {
            const vDist = Math.abs(lbl.cy - inputCy);
            const hDist = rect.left - lbl.right;
            if (vDist < 25 && hDist > -30 && hDist < 350) {
                const score = Math.abs(hDist) + vDist * 3;
                if (score < bestScore) { bestScore = score; bestLabel = lbl.text; }
            }
        }
        if (!bestLabel) {
            for (const lbl of labelPool) {
                const vDist = rect.top - lbl.bottom;
                const hAlign = Math.abs(rect.left - lbl.left);
                if (vDist > -5 && vDist < 60 && hAlign < 100) {
                    const score = vDist + hAlign;
                    if (score < bestScore) { bestScore = score; bestLabel = lbl.text; }
                }
            }
        }
        if (!bestLabel) bestLabel = el.getAttribute('aria-label') || '';

        // required: HTML属性 或 同行有 * 星号元素
        const hasStarNearby = starPool.some(s => {
            const vDist = Math.abs(s.cy - inputCy);
            const hDist = rect.left - s.right;
            return vDist < 25 && hDist > -30 && hDist < 400;
        });
        const isRequired = hasStarNearby || el.required || el.getAttribute('aria-required') === 'true';

        // 读取当前已有值
        let currentValue = '';
        if (el.tagName === 'SELECT') {
            const sel = el.options[el.selectedIndex];
            currentValue = sel && sel.value ? sel.text.trim() : '';
        } else if (type === 'radio' || type === 'checkbox') {
            currentValue = el.checked ? el.value : '';
        } else {
            currentValue = el.value || '';
        }

        // 检测自定义 select 组件（phoenix-select / el-select / ant-select 等）
        let isCustomSelect = false;
        let ancestor = el.parentElement;
        for (let i = 0; i < 5 && ancestor; i++, ancestor = ancestor.parentElement) {
            if (/select/i.test(ancestor.className || '')) { isCustomSelect = true; break; }
        }
        if (el.tagName === 'SELECT') isCustomSelect = false; // 原生 select 不算

        const f = {
            idx, tag: el.tagName.toLowerCase(), type,
            name: el.name || '', placeholder: el.placeholder || '',
            label: bestLabel.slice(0, 80), required: isRequired,
            value: currentValue, options: [],
            customSelect: isCustomSelect,
        };
        if (el.tagName === 'SELECT') {
            f.options = [...el.options].filter(o => o.value)
                .map(o => ({v: o.value, t: o.text.trim()}));
        }
        idx++;
        fields.push(f);
    });
    return JSON.stringify(fields);
})()
"""


def _resume_to_kv(resume: dict) -> str:
    """简历 → 紧凑 key:value"""
    lines = []
    p = resume.get("personal", {})
    for k, v in p.items():
        if v:
            lines.append(f"{k}: {v}")

    for i, e in enumerate(resume.get("education", [])):
        for k, v in e.items():
            if v and k not in ("is_985", "is_211"):
                lines.append(f"edu{i}_{k}: {v}")

    for i, x in enumerate(resume.get("experience", [])):
        for k, v in x.items():
            if v:
                lines.append(f"exp{i}_{k}: {v}")

    skills = resume.get("skills", {})
    for cat, items in skills.items():
        if isinstance(items, list):
            lines.append(f"skills_{cat}: {', '.join(str(s) for s in items)}")

    for lang in resume.get("languages", []):
        lines.append(f"lang_{lang.get('name', '')}: {lang.get('level', '')}")

    pref = resume.get("preferences", {})
    for k, v in pref.items():
        if v:
            lines.append(f"pref_{k}: {', '.join(v) if isinstance(v, list) else v}")

    return "\n".join(lines)


def _build_prompt(fields: list, resume: dict, job: Optional[Job] = None) -> str:
    # 有标签的字段（含已有值，让 LLM 判断是否需要纠正）
    labeled = [
        f for f in fields
        if f.get("label") or f.get("name") or f.get("placeholder")
    ]

    compact = []
    for f in labeled:
        label = f["label"] or f["name"] or f["placeholder"]
        req = " *必填" if f.get("required") else ""
        desc = f'[{f["idx"]}] "{label}"{req} ({f["type"]})'
        if f.get("options"):
            opts = ", ".join(o["t"] for o in f["options"][:15])
            desc += f" 可选:[{opts}]"
        if f.get("value"):
            desc += f" 当前值:\"{f['value'][:30]}\""
        compact.append(desc)

    prompt = (
        "你是表单填写助手。将简历信息映射到表单字段。\n\n"
        "## 表单字段\n" + "\n".join(compact) + "\n\n"
        "## 简历\n" + _resume_to_kv(resume) + "\n\n"
        "## 要求\n"
        '返回JSON数组: [{"idx": 字段编号, "value": "填入值"}, ...]\n'
        "- 有「当前值」的字段：若当前值与简历一致且格式正确则跳过（不要输出该字段），若有误或格式不对则输出纠正后的值\n"
        "- 没有当前值的字段：从简历中匹配后填入\n"
        "- 标记 *必填 的字段优先填写\n"
        "- select 类型用可选项里最匹配的 v 值\n"
        "- radio 类型填写对应选项的 value\n"
        "- 不确定的字段不要填\n"
        "- 只返回JSON，不要任何解释\n\n/no_think"
    )
    if job:
        prompt += f"\n\n目标岗位: {job.company} - {job.title}"
    return prompt


def _parse_mapping(text: str) -> list:
    """从 LLM 响应提取 JSON 映射，兼容 think 标签和 markdown 代码块"""
    text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1)
    m = re.search(r"\[[\s\S]*\]", text)
    if m:
        text = m.group(0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"LLM 返回无法解析: {text[:500]}")
        return []


async def _connect_cdp(config: Config):
    """连接 CDP，返回 (playwright, browser) 或抛异常"""
    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.connect_over_cdp(config.cdp_url)
        return pw, browser
    except Exception:
        await pw.stop()
        raise


async def _find_or_open_page(browser, url: str):
    """优先找已打开的匹配页面（保留用户数据），找不到才开新标签"""
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    base = parsed.netloc + parsed.path

    for ctx in browser.contexts:
        for page in ctx.pages:
            page_parsed = urlparse(page.url)
            page_base = page_parsed.netloc + page_parsed.path
            if page_base == base:
                logger.info(f"找到已打开的页面: {page.url[:80]}")
                await page.bring_to_front()
                return page, False

    logger.info("未找到已打开的页面，开新标签")
    page = await browser.contexts[0].new_page()
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)
    return page, True


class FormFiller:
    """网页表单自动填写器 — CDP + 单次LLM"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()
        self.llm = ChatOllama(
            model=self.config.model,
            base_url=self.config.ollama_url,
            temperature=0.1,
            num_ctx=self.config.num_ctx,
        )
        self.resume = load_resume_data()

    async def diagnose(self, url: str) -> list:
        """只提取字段，不填写，用于诊断。优先读取已打开的页面"""
        pw, browser = await _connect_cdp(self.config)
        try:
            page, is_new = await _find_or_open_page(browser, url)
            if not is_new:
                await page.wait_for_timeout(500)
            fields_json = await page.evaluate(EXTRACT_JS)
            return json.loads(fields_json)
        finally:
            await pw.stop()

    async def fill(self, url: str, job: Optional[Job] = None) -> dict:
        try:
            pw, browser = await _connect_cdp(self.config)
        except Exception as e:
            return {
                "success": False,
                "message": f"CDP 连接失败 ({self.config.cdp_url}): {e}\n请先运行: python -m job_hunter login",
            }

        try:
            page, is_new = await _find_or_open_page(browser, url)
            if is_new:
                logger.info(f"已打开新标签: {url}")
            else:
                logger.info("使用已打开的页面（保留已有数据）")

            # 1. 提取表单字段
            fields_json = await page.evaluate(EXTRACT_JS)
            fields = json.loads(fields_json)
            if not fields:
                return {"success": False, "message": "页面未找到可填写的表单字段"}

            labeled = [f for f in fields if f.get("label") or f.get("name") or f.get("placeholder")]
            prefilled = sum(1 for f in labeled if f.get("value"))
            req_count = sum(1 for f in fields if f.get("required"))
            logger.info(f"找到 {len(fields)} 个字段: {prefilled} 个已有值(LLM核查), {len(labeled)-prefilled} 个待填, {req_count} 个必填")
            if not labeled:
                return {"success": False, "message": "页面未找到有标签的表单字段"}

            # 2. 单次 LLM 映射（/no_think 跳过推理）
            logger.info("AI 映射中...")
            prompt = _build_prompt(fields, self.resume, job)
            resp = self.llm.invoke(prompt)
            raw = resp.content
            logger.debug(f"LLM 原始输出: {raw[:500]}")
            mapping = _parse_mapping(raw)
            if not mapping:
                return {"success": False, "message": "AI 未生成有效映射"}
            logger.info(f"AI 映射了 {len(mapping)} 个字段")

            # 3. 并发填写（semaphore 限制同时操作数，避免 Vue/React 响应式冲突）
            sem = asyncio.Semaphore(4)
            custom_select_lock = asyncio.Lock()  # 自定义下拉必须串行，否则互相关闭
            field_map = {f["idx"]: f for f in fields}
            results = []

            async def _fill_one(item):
                idx = item.get("idx")
                value = str(item.get("value", "")).strip()
                if idx is None or not value:
                    return False
                selector = f'[data-jh="{idx}"]'
                is_custom = field_map.get(idx, {}).get("customSelect", False)
                ctx = custom_select_lock if is_custom else sem
                async with ctx:
                    try:
                        loc = page.locator(selector)
                        if await loc.count() == 0:
                            return False
                        tag = await loc.evaluate("el => el.tagName.toLowerCase()")
                        el_type = await loc.evaluate("el => (el.type || '').toLowerCase()")

                        f_info = field_map.get(idx, {})
                        if tag == "select":
                            await loc.select_option(value=value)
                            await loc.evaluate("el => el.dispatchEvent(new Event('change', {bubbles:true}))")
                        elif el_type in ("radio", "checkbox"):
                            name = await loc.get_attribute("name")
                            target = page.locator(f'input[name="{name}"][value="{value}"]')
                            if await target.count() > 0:
                                await target.click()
                        elif f_info.get("customSelect"):
                            # 自定义下拉：点击打开 → 输入过滤 → 点击匹配选项
                            await loc.click()
                            await loc.fill(value)
                            await page.wait_for_timeout(400)
                            # 通用选项选择器（覆盖主流组件库）
                            option_sel = (
                                "[class*='select__option']:not([class*='disabled']),"
                                "[class*='select-item']:not([class*='disabled']),"
                                "[class*='dropdown__item']:not([class*='disabled']),"
                                "li[class*='option']:not([class*='disabled'])"
                            )
                            opts = page.locator(option_sel)
                            matched = False
                            for i in range(await opts.count()):
                                opt = opts.nth(i)
                                if not await opt.is_visible():
                                    continue
                                text = (await opt.inner_text()).strip()
                                if value in text or text in value:
                                    await opt.click()
                                    matched = True
                                    break
                            if not matched:
                                # 没找到匹配项，按 Escape 关闭下拉
                                await page.keyboard.press("Escape")
                                logger.warning(f"  ✗ [{idx}] 自定义下拉未找到选项: {value}")
                                return False
                        else:
                            await loc.evaluate("""(el, v) => {
                                el.focus();
                                // 直接赋值
                                el.value = v;
                                // 绕过 Vue Proxy：用原生属性描述符的 setter
                                const proto = Object.getPrototypeOf(el);
                                const desc = Object.getOwnPropertyDescriptor(proto, 'value');
                                if (desc && desc.set) desc.set.call(el, v);
                                // React 内部值追踪器
                                if (el._valueTracker) el._valueTracker.setValue(v);
                                // 触发完整事件链
                                ['keydown','keypress','input','change','keyup','blur'].forEach(t =>
                                    el.dispatchEvent(new Event(t, {bubbles:true, cancelable:true}))
                                );
                            }""", value)

                        f = field_map.get(idx, {})
                        lbl = f.get("label") or f.get("name") or f"#{idx}"
                        logger.info(f"  ✓ {lbl} = {value[:40]}")
                        return True
                    except Exception as e:
                        logger.warning(f"  ✗ [{idx}] 填写失败: {e}")
                        return False

            results = await asyncio.gather(*[_fill_one(item) for item in mapping])
            filled = sum(results)

            msg = f"完成！已填写 {filled}/{len(mapping)} 个字段，请在浏览器中检查确认"
            logger.info(msg)
            return {"success": True, "message": msg}

        except Exception as e:
            logger.error(f"填写失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            await pw.stop()


async def quick_fill(url: str):
    filler = FormFiller()
    result = await filler.fill(url)
    print(f"结果: {result['message']}")
    return result


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://httpbin.org/forms/post"
    asyncio.run(quick_fill(url))
