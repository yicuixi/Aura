"""
岗位爬取 — Playwright + BOSS直聘
"""

import asyncio
import logging
from typing import Optional

from playwright.async_api import async_playwright, Page

from .config import Config
from .models import Job, make_job_id

logger = logging.getLogger("job_hunter.crawler")

BOSS_CITY_CODES = {
    "全国": "100010000", "北京": "101010100", "上海": "101020100",
    "杭州": "101210100", "深圳": "101280600", "广州": "101280100",
    "成都": "101270100", "南京": "101190100", "苏州": "101190400",
}


async def crawl_boss(config: Config) -> list[Job]:
    """从 BOSS 直聘爬取岗位"""
    jobs = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=config.browser_path,
        )
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )

        for loc in config.target_locations:
            for pos in config.target_positions:
                try:
                    city = BOSS_CITY_CODES.get(loc, "100010000")
                    url = f"https://www.zhipin.com/web/geek/job?query={pos}&city={city}"
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(2)

                    page_jobs = await _parse_list(page, loc)
                    jobs.extend(page_jobs)
                    logger.info(f"[BOSS] {loc}-{pos}: {len(page_jobs)} 个岗位")
                    await asyncio.sleep(3)
                except Exception as e:
                    logger.error(f"[BOSS] {loc}-{pos} 失败: {e}")

        await browser.close()

    # 去重
    seen = set()
    unique = []
    for j in jobs:
        if j.id not in seen:
            seen.add(j.id)
            unique.append(j)
    return unique


async def _parse_list(page: Page, location: str) -> list[Job]:
    """解析岗位列表页"""
    jobs = []
    cards = await page.query_selector_all(".job-card-wrapper, [class*='job-card']")

    for card in cards:
        try:
            title_el = await card.query_selector(".job-name, [class*='job-title']")
            company_el = await card.query_selector(".company-name a, [class*='company-name']")
            salary_el = await card.query_selector(".salary, [class*='salary']")
            link_el = await card.query_selector("a[href*='/job_detail/']")

            title = (await title_el.inner_text()).strip() if title_el else ""
            company = (await company_el.inner_text()).strip() if company_el else ""
            salary = (await salary_el.inner_text()).strip() if salary_el else ""
            href = (await link_el.get_attribute("href")) if link_el else ""

            if not title or not company:
                continue

            job_url = f"https://www.zhipin.com{href}" if href and not href.startswith("http") else href

            jobs.append(Job(
                id=make_job_id("boss", company, title),
                title=title, company=company, location=location,
                salary_range=salary, source="boss", url=job_url,
            ))
        except Exception:
            continue

    return jobs
