// JobHunter AI 填表助手 — Sidebar
// Flow: expand → DOM prune → LLM (HTML + resume) → fill by idx

let isRunning = false;
const shownIdxs = new Set();

// ========== Helpers ==========

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function sendToContent(action, data = {}) {
  const tab = await getActiveTab();
  if (!tab?.id) throw new Error('未找到活动标签页');
  try {
    return await chrome.tabs.sendMessage(tab.id, { action, ...data });
  } catch (e) {
    if (e.message?.includes('Receiving end does not exist')) {
      throw new Error('请刷新页面后重试');
    }
    throw e;
  }
}

function setStatus(text, type = 'default') {
  document.getElementById('statusText').textContent = text;
  const dot = document.getElementById('statusDot');
  dot.className = 'status-dot';
  if (type !== 'default') dot.classList.add(type);
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

// ========== UI Updates ==========

function showFieldsSection(fieldCount) {
  const section = document.getElementById('fieldsSection');
  const countEl = document.getElementById('fieldCount');
  const summaryEl = document.getElementById('fieldSummary');

  countEl.textContent = fieldCount;
  summaryEl.innerHTML = `<span class="tag">DOM 剪枝模式</span>`;
  section.style.display = '';
}

function clearResults() {
  document.getElementById('resultsSection').style.display = 'none';
  document.getElementById('resultsList').innerHTML = '';
  document.getElementById('resultCount').textContent = '0/0';
  shownIdxs.clear();
}

function addResult(result) {
  if (result.idx != null && shownIdxs.has(result.idx)) return;
  if (result.idx != null) shownIdxs.add(result.idx);

  const section = document.getElementById('resultsSection');
  const list = document.getElementById('resultsList');
  const countEl = document.getElementById('resultCount');
  section.style.display = '';

  const item = document.createElement('div');
  item.className = `result-item ${result.success ? 'success' : 'fail'}`;

  let html =
    `<span class="result-icon">${result.success ? '✓' : '✗'}</span>` +
    `<span class="result-label">${escapeHtml(result.label || '#' + result.idx)}</span>` +
    `<span class="result-value">${escapeHtml((result.value || '').slice(0, 50))}</span>`;
  if (result.reason) {
    html += `<span class="result-reason">${escapeHtml(result.reason)}</span>`;
  }
  item.innerHTML = html;
  list.appendChild(item);

  const total = list.children.length;
  const ok = list.querySelectorAll('.success').length;
  countEl.textContent = `${ok}/${total}`;

  // Auto-scroll to bottom
  list.scrollTop = list.scrollHeight;
}

// ========== Collapsible Sections ==========

function setupCollapsible(headerId, panelId, iconId) {
  const header = document.getElementById(headerId);
  const panel = document.getElementById(panelId);
  const icon = document.getElementById(iconId);
  header.addEventListener('click', () => {
    const isOpen = panel.classList.toggle('open');
    icon.classList.toggle('open', isOpen);
  });
}

// ========== Core: AI Fill ==========

async function startAiFill() {
  if (isRunning) return;
  isRunning = true;

  const btn = document.getElementById('btnAiFill');
  btn.disabled = true;
  clearResults();

  try {
    await saveCurrentSettings();

    // Step 1: Expand multi-entry sections
    btn.textContent = '展开表单...';
    setStatus('展开多段经历...', 'working');
    try {
      const rdResp = await chrome.runtime.sendMessage({ action: 'getResumeData' });
      const rd = rdResp.resumeData;
      const preset = rd?.presets?.[rd.activePreset] || {};
      const counts = {
        education: (rd?.common?.education || rd?.education || []).length,
        experience: (preset.experience || rd?.experience || []).length,
        projects: (preset.projects || rd?.projects || []).length,
      };
      await sendToContent('expandSections', { counts });
    } catch { /* ok */ }
    await new Promise((r) => setTimeout(r, 300));

    // Step 2: DOM prune — get form HTML
    btn.textContent = '提取页面...';
    setStatus('DOM 剪枝中...', 'working');
    const htmlResp = await sendToContent('getFormHTML');
    if (htmlResp.error) throw new Error(htmlResp.error);
    if (!htmlResp.html || htmlResp.fieldCount === 0)
      throw new Error('页面未找到可填写的表单字段');

    showFieldsSection(htmlResp.fieldCount);
    console.log('[JH] Form HTML:', htmlResp.html.length, 'chars,', htmlResp.fieldCount, 'fields');

    // Step 3: LLM — send HTML + resume, get mapping
    btn.textContent = 'AI 分析中...';
    setStatus(`AI 分析 ${htmlResp.fieldCount} 个字段...`, 'working');
    console.log('[JH] Sending to LLM, HTML length:', htmlResp.html.length);
    const llmResp = await chrome.runtime.sendMessage({
      action: 'llmFill',
      formHTML: htmlResp.html,
    });
    console.log('[JH] LLM response:', llmResp);
    if (!llmResp) throw new Error('LLM 无响应（service worker 可能超时）');
    if (llmResp.error) throw new Error(llmResp.error);
    if (!llmResp.mapping || llmResp.mapping.length === 0) {
      const hint = llmResp.raw ? llmResp.raw.slice(0, 300) : '(无返回内容)';
      console.error('[JH] LLM 原始返回:', llmResp.raw);
      throw new Error(`AI 未生成有效映射\n模型返回: ${hint}`);
    }

    // Step 4: Fill by idx
    btn.textContent = `填写中 (${llmResp.mapping.length})...`;
    setStatus('正在填写表单...', 'working');

    const fillResp = await sendToContent('fillFields', { mapping: llmResp.mapping });
    if (fillResp.error) throw new Error(fillResp.error);

    await new Promise((r) => setTimeout(r, 150));
    if (fillResp.results) {
      for (const r of fillResp.results) addResult(r);
    }

    const total = llmResp.mapping.length;
    const ok = fillResp.results ? fillResp.results.filter((r) => r.success).length : 0;
    setStatus(`完成 ${ok}/${total}`, 'success');
  } catch (e) {
    setStatus(e.message, 'error');
  } finally {
    isRunning = false;
    btn.disabled = false;
    btn.innerHTML =
      '<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">' +
      '<path d="M10 1L3 5.5v9L10 19l7-4.5v-9L10 1zm0 2.2l4.8 3.1L10 9.3 5.2 6.3 10 3.2zM4.5 7.5L9.5 10.5v5.7l-5-3.2V7.5zm6 8.9v-5.7l5-3v5.5l-5 3.2z"/>' +
      '</svg>AI 智能填写';
  }
}

// ========== Extract Only (preview pruned HTML) ==========

async function extractOnly() {
  try {
    setStatus('DOM 剪枝中...', 'working');
    const resp = await sendToContent('getFormHTML');
    if (resp.error) throw new Error(resp.error);
    if (!resp.html || resp.fieldCount === 0) {
      setStatus('未找到表单字段', 'error');
      return;
    }
    showFieldsSection(resp.fieldCount);
    console.log('[JH] Pruned HTML preview:\n', resp.html.slice(0, 2000));
    setStatus(`检测到 ${resp.fieldCount} 个字段 (${resp.html.length} chars)`, 'success');
  } catch (e) {
    setStatus(e.message, 'error');
  }
}

// ========== Resume Data ==========

async function loadResumeStatus() {
  try {
    const resp = await chrome.runtime.sendMessage({ action: 'getResumeData' });
    const statusEl = document.getElementById('resumeStatus');
    const editorEl = document.getElementById('resumeEditor');
    const presetEl = document.getElementById('presetSelect');
    if (resp.resumeData) {
      const rd = resp.resumeData;
      const name = rd.common?.personal?.name || rd.personal?.name || '未知';
      const preset = rd.activePreset || '';
      statusEl.textContent = preset ? `${name} — ${preset}` : `已加载: ${name}`;
      statusEl.className = 'resume-status loaded';
      editorEl.value = JSON.stringify(rd, null, 2);

      if (preset && presetEl) {
        presetEl.value = preset;
        if (!Array.from(presetEl.options).some((o) => o.value === preset)) {
          const opt = document.createElement('option');
          opt.value = preset;
          opt.textContent = preset;
          presetEl.appendChild(opt);
          presetEl.value = preset;
        }
      }
    } else {
      statusEl.textContent = '未加载简历数据';
      statusEl.className = 'resume-status empty';
    }
  } catch {
    document.getElementById('resumeStatus').textContent = '加载失败';
  }
}

async function switchPreset(presetName) {
  const resp = await chrome.runtime.sendMessage({ action: 'getResumeData' });
  if (!resp.resumeData) return;
  resp.resumeData.activePreset = presetName;
  await chrome.runtime.sendMessage({ action: 'saveResumeData', data: resp.resumeData });
  loadResumeStatus();
  setStatus(`已切换: ${presetName}`, 'success');
}

// ========== Settings ==========

async function saveCurrentSettings() {
  const config = {
    provider: document.getElementById('settingProvider').value,
    model: document.getElementById('settingModel').value.trim(),
    ollamaUrl: document.getElementById('settingUrl').value.trim(),
    numGpu: parseInt(document.getElementById('settingGpu').value) || 99,
    openaiBaseUrl: document.getElementById('settingBaseUrl').value.trim(),
    apiKey: document.getElementById('settingApiKey').value.trim(),
  };
  await chrome.runtime.sendMessage({ action: 'saveConfig', config });
  return config;
}

function toggleProviderUI(provider) {
  const isOllama = provider !== 'openai';
  document.getElementById('ollamaSettings').style.display = isOllama ? '' : 'none';
  document.getElementById('openaiSettings').style.display = isOllama ? 'none' : '';
  if (!isOllama && !document.getElementById('settingModel').dataset.userSet) {
    document.getElementById('settingModel').value = 'nvidia/nemotron-3-nano-30b-a3b';
  }
}

async function loadSettings() {
  try {
    const resp = await chrome.runtime.sendMessage({ action: 'getConfig' });
    if (resp.config) {
      document.getElementById('settingProvider').value = resp.config.provider || 'ollama';
      document.getElementById('settingModel').value = resp.config.model || 'qwen3:4b';
      document.getElementById('settingUrl').value = resp.config.ollamaUrl || '';
      document.getElementById('settingGpu').value = resp.config.numGpu ?? 99;
      document.getElementById('settingBaseUrl').value =
        resp.config.openaiBaseUrl || 'https://integrate.api.nvidia.com/v1';
      document.getElementById('settingApiKey').value = resp.config.apiKey || '';
      toggleProviderUI(resp.config.provider || 'ollama');
    }
  } catch { /* ignore */ }
}

// ========== Fill progress listener (real-time updates from content.js) ==========

chrome.runtime.onMessage.addListener((request) => {
  if (request.action === 'fillProgress') {
    addResult(request);
  }
});

// ========== Init ==========

document.addEventListener('DOMContentLoaded', () => {
  // Main actions
  document.getElementById('btnAiFill').addEventListener('click', startAiFill);
  document.getElementById('btnExtract').addEventListener('click', extractOnly);
  document.getElementById('btnClear').addEventListener('click', clearResults);

  // Preset selector
  document.getElementById('presetSelect').addEventListener('change', (e) => {
    switchPreset(e.target.value);
  });

  // Collapsible sections
  setupCollapsible('settingsHeader', 'settingsPanel', 'settingsToggleIcon');

  // Resume management
  loadResumeStatus();

  document.getElementById('btnImportResume').addEventListener('click', () => {
    document.getElementById('fileResume').click();
  });

  document
    .getElementById('fileResume')
    .addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = async (ev) => {
        try {
          const data = JSON.parse(ev.target.result);
          document.getElementById('resumeEditor').value = JSON.stringify(
            data,
            null,
            2
          );
          await chrome.runtime.sendMessage({ action: 'saveResumeData', data });
          loadResumeStatus();
          setStatus('简历已导入', 'success');
        } catch {
          setStatus('文件格式错误', 'error');
        }
      };
      reader.readAsText(file);
    });

  // Settings
  loadSettings();

  document.getElementById('settingProvider').addEventListener('change', (e) => {
    toggleProviderUI(e.target.value);
    saveCurrentSettings();
  });

  document
    .getElementById('btnSaveSettings')
    .addEventListener('click', async () => {
      await saveCurrentSettings();
      setStatus('设置已保存', 'success');
    });

  document
    .getElementById('btnTestConnection')
    .addEventListener('click', async () => {
      setStatus('测试连接...', 'working');
      const resp = await chrome.runtime.sendMessage({ action: 'testConnection' });
      if (resp.error) {
        setStatus(`连接失败: ${resp.error}`, 'error');
      } else {
        const models = resp.models?.slice(0, 5).join(', ') || '无';
        setStatus(`连接成功 — ${models}`, 'success');
      }
    });
});
