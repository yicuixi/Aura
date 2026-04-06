// JobHunter AI 填表助手 — Content Script
// DOM 剪枝 → LLM 直接看 HTML 结构做字段识别（参考 OfferNow 方案）

(() => {
  if (window.__jhContentLoaded) return;
  window.__jhContentLoaded = true;

  // ========== DOM Pruning: extract form-area HTML for LLM ==========

  function getFormHTML() {
    let idx = 0;
    document.querySelectorAll('input, select, textarea').forEach((el) => {
      const type = (el.type || 'text').toLowerCase();
      if (['hidden', 'submit', 'button', 'image', 'reset', 'file'].includes(type)) return;
      if (el.readOnly && el.disabled) return;
      const rect = el.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0 && type !== 'radio' && type !== 'checkbox') return;
      el.setAttribute('data-jh', String(idx++));
      if (el.tagName !== 'SELECT') {
        const dateInfo = findDatePickerContainer(el);
        const selInfo = !dateInfo && findSelectContainer(el);
        if (dateInfo) {
          el.setAttribute('data-jh-type', 'datepicker');
        } else if (selInfo) {
          el.setAttribute('data-jh-type', 'select');
        } else if (el.readOnly || (el.placeholder || '').includes('请选择')) {
          const ctx = ((el.closest('[class*="form"]') || el.parentElement)?.textContent || '').slice(0, 100);
          if (/年|月|日期|date|出生|毕业|入学|开始|结束/i.test(ctx)) {
            el.setAttribute('data-jh-type', 'datepicker');
          } else if (el.readOnly) {
            el.setAttribute('data-jh-type', 'select');
          }
        }
      }
    });

    // --- Clone body + collect original computed styles for visibility ---
    const origAll = Array.from(document.body.querySelectorAll('*'));
    const clone = document.body.cloneNode(true);
    const cloneAll = Array.from(clone.querySelectorAll('*'));

    // --- Remove junk tags + invisible elements (single reverse pass) ---
    const JUNK = new Set(['script','style','svg','img','video','audio','iframe',
      'noscript','link','meta','canvas','icon','path','br']);
    for (let i = cloneAll.length - 1; i >= 0; i--) {
      const cel = cloneAll[i];
      if (!cel.parentNode) continue;
      if (JUNK.has(cel.tagName.toLowerCase())) { cel.remove(); continue; }
      if (cel.hasAttribute('data-jh')) continue;
      try {
        const s = getComputedStyle(origAll[i]);
        if (s.display === 'none' || s.visibility === 'hidden' || s.opacity === '0') cel.remove();
      } catch {}
    }
    for (const el of clone.querySelectorAll('nav, footer')) {
      if (!el.querySelector('[data-jh]')) el.remove();
    }

    // --- Iterative bottom-up empty element removal ---
    const KEEP_TAGS = new Set(['input','textarea','select','hr']);
    for (let round = 0; round < 5; round++) {
      let changed = false;
      for (const el of Array.from(clone.querySelectorAll('*'))) {
        if (!el.parentNode) continue;
        if (KEEP_TAGS.has(el.tagName.toLowerCase())) continue;
        if (el.hasAttribute('data-jh')) continue;
        if ((el.textContent || '').trim()) continue;
        if (el.querySelector('[data-jh]')) continue;
        el.remove();
        changed = true;
      }
      if (!changed) break;
    }

    // --- Field-relevance pruning: remove subtrees unrelated to form fields ---
    for (const el of clone.querySelectorAll('button, [type="button"], [type="submit"], [role="button"]')) {
      if (!el.querySelector('[data-jh]')) el.remove();
    }
    const relevant = new Set();
    for (const field of clone.querySelectorAll('[data-jh]')) {
      relevant.add(field);
      let p = field.parentElement;
      while (p && p !== clone) { if (relevant.has(p)) break; relevant.add(p); p = p.parentElement; }
    }
    const LABEL_RE = /^(?:label|h[1-6]|legend|th|caption|dt|summary|p)$/i;
    for (const parent of Array.from(clone.querySelectorAll('*'))) {
      if (!parent.parentNode || !relevant.has(parent)) continue;
      for (const child of Array.from(parent.children)) {
        if (relevant.has(child)) continue;
        const text = (child.textContent || '').trim();
        if (LABEL_RE.test(child.tagName) && text.length <= 80) continue;
        if (text.length > 0 && text.length <= 60) continue;
        child.remove();
      }
    }

    // --- Clean attributes (whitelist for form fields, strip all for others) ---
    const FORM_KEEP = new Set([
      'data-jh','data-jh-type','type','name','placeholder',
      'required','readonly','value','options',
    ]);
    for (const el of clone.querySelectorAll('*')) {
      const tag = el.tagName.toLowerCase();
      if (['input','select','textarea'].includes(tag)) {
        if (tag === 'select') {
          const opts = Array.from(el.options || [])
            .filter(o => o.value).map(o => o.text.trim()).slice(0, 20);
          if (opts.length) el.setAttribute('options', opts.join('|'));
          el.innerHTML = '';
        }
        if (el.readOnly) el.setAttribute('readonly', '');
        if (el.value) el.setAttribute('value', el.value.slice(0, 50));
        for (const attr of Array.from(el.attributes)) {
          if (!FORM_KEEP.has(attr.name)) el.removeAttribute(attr.name);
        }
      } else {
        while (el.attributes.length) el.removeAttribute(el.attributes[0].name);
      }
    }

    // --- Clean text nodes (collapse whitespace) ---
    const tw = document.createTreeWalker(clone, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    while (tw.nextNode()) textNodes.push(tw.currentNode);
    for (const tn of textNodes) {
      const t = (tn.nodeValue || '').replace(/\s+/g, ' ').trim();
      if (t) tn.nodeValue = t; else tn.remove();
    }

    // --- Collapse single-child wrapper divs to reduce nesting ---
    for (let round = 0; round < 3; round++) {
      let changed = false;
      for (const el of Array.from(clone.querySelectorAll('div, span'))) {
        if (!el.parentNode) continue;
        const kids = Array.from(el.childNodes).filter(n =>
          n.nodeType === Node.ELEMENT_NODE ||
          (n.nodeType === Node.TEXT_NODE && (n.nodeValue || '').trim()));
        if (kids.length === 1 && kids[0].nodeType === Node.ELEMENT_NODE) {
          el.replaceWith(kids[0]);
          changed = true;
        }
      }
      if (!changed) break;
    }

    // --- Find best root container ---
    let root = clone;
    let bestCount = 0;
    const allTagged = clone.querySelectorAll('[data-jh]');
    for (const c of clone.querySelectorAll('form, main, [role="main"], section')) {
      const n = c.querySelectorAll('[data-jh]').length;
      if (n > bestCount) { bestCount = n; root = c; }
    }
    if (bestCount < allTagged.length * 0.5) root = clone;

    // --- Serialize ---
    let html = root.innerHTML.trim().replace(/\n{3,}/g, '\n');
    if (html.length > 15000) {
      html = html.slice(0, 15000) + '\n<!-- truncated -->';
    }

    console.log(`[JH] DOM cleaned: ${html.length} chars, ${idx} fields`);
    console.log('[JH] Preview:\n' + html.slice(0, 1500));
    return { html, fieldCount: idx };
  }

  // ========== setInputValue — React / Vue / vanilla compatible ==========

  function setInputValue(element, value) {
    if (!element) return;
    element.focus();
    element.value = value;

    const proto = Object.getPrototypeOf(element);
    const desc = Object.getOwnPropertyDescriptor(proto, 'value');
    if (desc && desc.set) desc.set.call(element, value);
    if (element._valueTracker) element._valueTracker.setValue('');

    ['keydown', 'keypress', 'input', 'change', 'keyup', 'blur'].forEach((evt) => {
      element.dispatchEvent(new Event(evt, { bubbles: true, cancelable: true }));
    });
    addFillEffect(element);
  }

  function forceSetValue(el, value) {
    const wasRO = el.readOnly;
    if (wasRO) el.readOnly = false;
    el.dispatchEvent(new FocusEvent('focus', { bubbles: true }));
    el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, view: window }));
    el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, view: window }));
    el.dispatchEvent(new MouseEvent('click', { bubbles: true, view: window }));

    const ctorSet = Object.getOwnPropertyDescriptor(el.constructor.prototype, 'value')?.set;
    const protoSet = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value')?.set;
    if (protoSet && ctorSet !== protoSet) protoSet.call(el, value);
    else if (ctorSet) ctorSet.call(el, value);
    else el.value = value;

    el.setAttribute('value', value);
    if (el._valueTracker) el._valueTracker.setValue('');
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur', { bubbles: true }));
    if (wasRO) el.readOnly = true;
    addFillEffect(el);
  }

  function addFillEffect(element) {
    element.classList.add('jh-filled');
    setTimeout(() => element.classList.remove('jh-filled'), 2500);
  }

  // ========== Fuzzy option matcher ==========

  function bestMatch(candidates, value) {
    if (!value || candidates.length === 0) return null;
    const v = value.trim().toLowerCase();
    let best = null, bestScore = 0;

    for (const c of candidates) {
      const t = (c.text || '').trim().toLowerCase();
      if (!t) continue;
      let score = 0;
      if (t === v) score = 100;
      else if (t.includes(v)) score = 80;
      else if (v.includes(t)) score = 70;
      else {
        const vNum = parseFloat(v.replace(/[^\d.]/g, ''));
        const tNum = parseFloat(t.replace(/[^\d.]/g, ''));
        if (!isNaN(vNum) && !isNaN(tNum)) {
          const diff = Math.abs(vNum - tNum);
          if (diff === 0) score = 95;
          else if (diff <= 5) score = 50;
          else if (diff <= 10) score = 30;
        }
      }
      if (score > bestScore) { bestScore = score; best = c; }
    }
    return bestScore >= 30 ? best : null;
  }

  // ========== Custom select handlers ==========

  function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

  function findSelectContainer(el) {
    if (findDatePickerContainer(el)) return null;
    let p = el;
    for (let i = 0; i < 6 && p; i++, p = p.parentElement) {
      const cls = p.className || '';
      if (/phoenix.?select/i.test(cls) && !/select.?list/i.test(cls)) return { container: p };
      if (/\bel-select\b/i.test(cls)) return { container: p };
      if (/\bant-select\b/i.test(cls)) return { container: p };
      if (/\bivu-select\b/i.test(cls)) return { container: p };
      if (p.getAttribute('role') === 'combobox' || p.getAttribute('role') === 'listbox') return { container: p };
    }
    return null;
  }

  function findDatePickerContainer(el) {
    let p = el;
    for (let i = 0; i < 6 && p; i++, p = p.parentElement) {
      const cls = p.className || '';
      if (/phoenix.?date.?picker|el-date.?picker|ant-?picker|datepicker|date-picker/i.test(cls)) return p;
    }
    return null;
  }

  async function fillSelect(el, value) {
    const info = findSelectContainer(el);
    if (!info) return false;

    const container = info.container;
    container.click();
    await sleep(300);

    const searchInput = container.querySelector('[class*="select__input"], input') || el;
    if (searchInput?.tagName === 'INPUT') setInputValue(searchInput, value);
    await sleep(500);

    const optionSelectors = [
      '.phoenix-selectList__listItem:not(.phoenix-selectList__listItem--disabled)',
      "[class*='select__option']:not([class*='disabled'])",
      "[class*='select-item']:not([class*='disabled'])",
      "[class*='dropdown__item']:not([class*='disabled'])",
      "[class*='selectList__listItem']:not([class*='disabled'])",
      "li[class*='option']:not([class*='disabled'])",
    ].join(',');

    const allOpts = document.querySelectorAll(optionSelectors);
    const candidates = Array.from(allOpts)
      .filter((o) => o.offsetParent)
      .map((o) => ({ el: o, text: (o.textContent || '').trim() }));

    const hit = bestMatch(candidates, value);
    if (hit) { hit.el.click(); return true; }

    return false;
  }

  // ========== Date picker handler ==========

  async function fillDatePicker(el, value) {
    const parts = value.split(/[-/.]/).map(Number);
    const targetY = parts[0], targetM = parts[1] || 1, targetD = parts[2] || 1;
    if (!targetY || targetY < 1900) return false;

    function simulateClick(target) {
      target.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window }));
      target.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window }));
      target.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
    }

    const formatted = parts[2]
      ? `${targetY}-${String(targetM).padStart(2,'0')}-${String(targetD).padStart(2,'0')}`
      : `${targetY}-${String(targetM).padStart(2,'0')}`;

    function findCalPopup() {
      return document.querySelector('.phoenix-calendar-panel') ||
        document.querySelector('[class*="datePicker__popover"]:not([style*="display: none"])') ||
        document.querySelector('[class*="date-picker-popup"]') ||
        document.querySelector('[class*="picker-panel"]') ||
        document.querySelector('[class*="calendar-panel"]');
    }

    // Open popup: click the SELECT CONTAINER, not the input (Phoenix needs container click)
    let popup = findCalPopup();
    if (!popup) {
      const selectInfo = findSelectContainer(el);
      const clickTarget = selectInfo?.container || el;
      clickTarget.dispatchEvent(new FocusEvent('focus', { bubbles: true }));
      clickTarget.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, view: window }));
      clickTarget.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, view: window }));
      clickTarget.dispatchEvent(new MouseEvent('click', { bubbles: true, view: window }));
      await sleep(500);
      popup = findCalPopup();
    }

    if (!popup) {
      forceSetValue(el, formatted);
      return true;
    }

    // Strategy 1: type into the calendar's own input and press Enter
    const calInput = popup.querySelector('input[class*="calendar-input"], input[class*="picker-input"], input[class*="date-input"]');
    if (calInput) {
      calInput.focus();
      calInput.value = '';
      setInputValue(calInput, formatted);
      await sleep(150);
      for (const key of ['Enter']) {
        calInput.dispatchEvent(new KeyboardEvent('keydown', { key, code: key, keyCode: 13, which: 13, bubbles: true }));
        calInput.dispatchEvent(new KeyboardEvent('keyup',   { key, code: key, keyCode: 13, which: 13, bubbles: true }));
      }
      await sleep(400);
      if (el.value) return true;
    }

    // Strategy 2: click month/day cells
    const allTds = Array.from(popup.querySelectorAll('td'));
    const isMonthPicker = allTds.filter(c => /^\d{1,2}月$/.test((c.textContent || '').trim())).length >= 6;

    const yearArrows = Array.from(popup.querySelectorAll('button, [class*="btn"]'))
      .filter(a => !a.closest('table') && (a.querySelector('svg') || /prev|next|year/i.test(a.className || '')));

    function readYear() {
      const yearEl = popup.querySelector('[class*="year-select"], [class*="ym-select"]');
      const text = yearEl ? yearEl.textContent : '';
      const m = text.match(/(\d{4})/);
      return m ? +m[1] : null;
    }

    if (isMonthPicker) {
      let pY = yearArrows[0], nY = yearArrows[yearArrows.length - 1];
      for (const btn of yearArrows) {
        const cls = (btn.className || '').toLowerCase();
        if (/prev.*year|year.*prev/i.test(cls)) pY = btn;
        else if (/next.*year|year.*next/i.test(cls)) nY = btn;
      }
      for (let i = 0; i < 20; i++) {
        const y = readYear(); if (!y || y === targetY) break;
        const btn = y > targetY ? pY : nY;
        if (btn) simulateClick(btn); await sleep(150);
      }
      await sleep(100);
      for (const cell of allTds) {
        if (/disabled/i.test(cell.className || '')) continue;
        const text = (cell.textContent || '').trim();
        if (/^\d{1,2}月$/.test(text) && parseInt(text) === targetM) {
          const target = cell.querySelector('a') || cell.querySelector('div') || cell;
          simulateClick(target);
          await sleep(500);
          break;
        }
      }
    } else {
      function readHeader() {
        const hdr = popup.querySelector('[class*="ym-select"]');
        const text = hdr ? hdr.textContent.trim() : (popup.textContent || '').slice(0, 30);
        const m = text.match(/(\d{4})\s*年?\s*(\d{1,2})\s*月/);
        return m ? { y: +m[1], m: +m[2] } : null;
      }
      let prevY = null, prevM = null, nextM = null, nextY = null;
      for (const btn of yearArrows) {
        const hint = ((btn.className || '') + ' ' + (btn.getAttribute('aria-label') || btn.getAttribute('title') || '')).toLowerCase();
        const t = (btn.textContent || '').trim();
        if (/prev.*year|year.*prev|double.*left/i.test(hint) || t === '«') prevY = btn;
        else if (/next.*year|year.*next|double.*right/i.test(hint) || t === '»') nextY = btn;
        else if (/prev.*month|month.*prev|(?:^|\s)prev(?:\s|$)/i.test(hint) || t === '‹' || t === '<') prevM = btn;
        else if (/next.*month|month.*next|(?:^|\s)next(?:\s|$)/i.test(hint) || t === '›' || t === '>') nextM = btn;
      }
      if (!prevM && !nextM && yearArrows.length >= 2) {
        if (yearArrows.length >= 4) {
          prevY = prevY || yearArrows[0]; prevM = prevM || yearArrows[1];
          nextM = nextM || yearArrows[yearArrows.length - 2]; nextY = nextY || yearArrows[yearArrows.length - 1];
        } else {
          prevM = prevM || yearArrows[0]; nextM = nextM || yearArrows[yearArrows.length - 1];
        }
      }
      for (let i = 0; i < 20; i++) {
        const cur = readHeader(); if (!cur || cur.y === targetY) break;
        const btn = cur.y > targetY ? prevY : nextY;
        if (btn) simulateClick(btn); await sleep(150);
      }
      for (let i = 0; i < 14; i++) {
        const cur = readHeader(); if (!cur || (cur.m === targetM && cur.y === targetY)) break;
        const diff = (targetY - cur.y) * 12 + (targetM - cur.m);
        const btn = diff > 0 ? nextM : prevM;
        if (btn) simulateClick(btn); await sleep(150);
      }
      await sleep(150);
      const dayCells = popup.querySelectorAll('td[class*="cell"], td[class*="day"], [class*="datePicker__day"]');
      for (const cell of dayCells) {
        if (/other|prev|next|last.month|disabled|grey/i.test(cell.className || '')) continue;
        if (parseInt((cell.textContent || '').trim()) === targetD) {
          const target = cell.querySelector('[class*="date"], [class*="day-inner"]') || cell;
          simulateClick(target);
          await sleep(500);
          break;
        }
      }
    }

    // Universal close: Escape + blur + click body
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', keyCode: 27, bubbles: true }));
    await sleep(100);
    document.activeElement?.blur();
    document.body.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    await sleep(300);

    // Fallback: OfferNow-style force set with setAttribute
    if (!el.value) forceSetValue(el, formatted);
    return true;
  }

  // ========== Fill single field (auto-detect type) ==========

  async function fillOneField(item) {
    const value = String(item.value || '').trim();
    const idx = item.idx;
    if (idx == null || !value) return { idx, success: false, reason: '值为空' };

    const el = document.querySelector(`[data-jh="${idx}"]`);
    if (!el) return { idx, success: false, reason: '元素未找到' };

    const label = el.placeholder || el.name || `#${idx}`;
    const jhType = el.getAttribute('data-jh-type');

    try {
      if (el.tagName === 'SELECT') {
        const opt = [...el.options].find((o) => o.value === value || o.text.trim() === value);
        if (opt) { el.value = opt.value; } else { el.value = value; }
        el.dispatchEvent(new Event('change', { bubbles: true }));
      } else if (el.type === 'radio' || el.type === 'checkbox') {
        const name = el.getAttribute('name');
        const target = name ? document.querySelector(`input[name="${name}"][value="${value}"]`) : null;
        if (target) target.click();
        else return { idx, label, value, success: false, reason: '选项未找到' };
      } else if (jhType === 'datepicker' || findDatePickerContainer(el) || (/\d{4}[-/]/.test(value) && (el.readOnly || (el.placeholder || '').includes('请选择')))) {
        await fillDatePicker(el, value);
      } else if (jhType === 'select' || findSelectContainer(el)) {
        if (/^\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?$/.test(value)) {
          await fillDatePicker(el, value);
        } else {
          const ok = await fillSelect(el, value);
          if (!ok) {
            document.activeElement?.blur();
            document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
            return { idx, label, value, success: false, reason: '下拉选项未匹配' };
          }
        }
      } else {
        setInputValue(el, value);
      }
      return { idx, label, value, success: true };
    } catch (e) {
      return { idx, label, value, success: false, reason: e.message };
    }
  }

  // ========== Fill all fields ==========

  async function fillAllFields(mapping) {
    const results = [];
    const serialItems = [];   // readonly (selects, date pickers)
    const parallelItems = [];

    for (const item of mapping) {
      const el = document.querySelector(`[data-jh="${item.idx}"]`);
      const jhType = el?.getAttribute('data-jh-type');
      const needsSerial = el && (
        el.tagName === 'SELECT' || el.type === 'radio' ||
        jhType === 'select' || jhType === 'datepicker' ||
        el.readOnly || findSelectContainer(el) || findDatePickerContainer(el)
      );
      if (needsSerial) {
        serialItems.push(item);
      } else {
        parallelItems.push(item);
      }
    }

    const parallelResults = await Promise.all(parallelItems.map((item) => fillOneField(item)));
    for (const r of parallelResults) {
      results.push(r);
      try { chrome.runtime.sendMessage({ action: 'fillProgress', ...r }); } catch {}
    }

    for (const item of serialItems) {
      const r = await fillOneField(item);
      results.push(r);
      try { chrome.runtime.sendMessage({ action: 'fillProgress', ...r }); } catch {}
    }

    return results;
  }

  // ========== Expand "add more" sections ==========

  async function expandAllSections(counts) {
    if (window.__jhExpanded) return 0;
    const addKeywords = /添加|新增|add|增加/i;
    const candidates = document.querySelectorAll('a, button, span, div');
    const addButtons = [];

    for (const el of candidates) {
      const text = (el.textContent || '').trim();
      if (text.length > 20 || text.length < 2) continue;
      if (!addKeywords.test(text)) continue;
      if (!el.offsetParent) continue;
      addButtons.push({ el, text });
    }

    const categoryMap = [
      { pattern: /教育|学历|education/i, key: 'education' },
      { pattern: /工作|实习|经历|experience|work/i, key: 'experience' },
      { pattern: /项目|project/i, key: 'projects' },
    ];

    let added = 0;
    for (const btn of addButtons) {
      let times = 0;
      for (const cat of categoryMap) {
        if (cat.pattern.test(btn.text)) { times = Math.max(0, ((counts && counts[cat.key]) || 0) - 1); break; }
      }
      if (times <= 0) continue;
      console.log(`[JH] "${btn.text}" × ${times}`);
      for (let i = 0; i < times; i++) { btn.el.click(); await sleep(500); added++; }
    }

    window.__jhExpanded = true;
    return added;
  }

  // ========== Message listener ==========

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.action) {
      case 'expandSections': {
        (async () => {
          try { sendResponse({ added: await expandAllSections(request.counts) }); }
          catch (e) { sendResponse({ added: 0, error: e.message }); }
        })();
        return true;
      }

      case 'getFormHTML': {
        try {
          const { html, fieldCount } = getFormHTML();
          sendResponse({ html, fieldCount });
        } catch (e) {
          sendResponse({ html: '', fieldCount: 0, error: e.message });
        }
        break;
      }

      case 'fillFields': {
        (async () => {
          try { sendResponse({ results: await fillAllFields(request.mapping) }); }
          catch (e) { sendResponse({ error: e.message }); }
        })();
        return true;
      }

      case 'ping': { sendResponse({ ok: true }); break; }
    }
  });
})();
