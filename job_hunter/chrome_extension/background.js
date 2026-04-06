// JobHunter AI 填表助手 — Background Service Worker
// Ollama API 调用必须在 background.js 中，content.js 直接调 localhost 会被 CORS 拦截

const DEFAULT_CONFIG = {
  provider: 'ollama',        // 'ollama' | 'openai'
  model: 'qwen3:4b',
  // Ollama
  ollamaUrl: 'http://localhost:11434',
  numGpu: 99,
  numCtx: 32000,
  temperature: 0.1,
  // OpenAI-compatible (NVIDIA NIM, etc.)
  openaiBaseUrl: 'https://integrate.api.nvidia.com/v1',
  apiKey: '',
};

// ---------- Install: load bundled resume into storage ----------
chrome.runtime.onInstalled.addListener(async () => {
  const { resumeData } = await chrome.storage.local.get('resumeData');
  if (!resumeData) {
    try {
      const resp = await fetch(chrome.runtime.getURL('resume_data.json'));
      const data = await resp.json();
      await chrome.storage.local.set({ resumeData: data });
      console.log('[JH] 默认简历已加载');
    } catch (e) {
      console.error('[JH] 加载默认简历失败:', e);
    }
  }
  const { llmConfig } = await chrome.storage.local.get('llmConfig');
  if (!llmConfig) {
    await chrome.storage.local.set({ llmConfig: DEFAULT_CONFIG });
  }
});

// ---------- Icon click → open side panel ----------
chrome.action.onClicked.addListener((tab) => {
  if (chrome.sidePanel) {
    chrome.sidePanel.open({ tabId: tab.id }).catch((err) => {
      console.error('[JH] 打开侧边栏失败:', err);
    });
  }
});

// ---------- Merge common + active preset into flat resume ----------
function mergeResume(data) {
  if (!data.presets) return data; // legacy format
  const preset = data.presets[data.activePreset] || {};
  return { ...data.common, ...preset };
}

// ---------- Resume → compact key:value (for LLM prompt) ----------
function resumeToKv(resume) {
  const lines = [];

  if (resume.target_position) lines.push(`目标岗位: ${resume.target_position}`);

  const p = resume.personal || {};
  for (const [k, v] of Object.entries(p)) {
    if (v) lines.push(`${k}: ${v}`);
  }

  (resume.education || []).forEach((e, i) => {
    for (const [k, v] of Object.entries(e)) {
      if (v) lines.push(`edu${i}_${k}: ${v}`);
    }
  });

  (resume.experience || []).forEach((x, i) => {
    for (const [k, v] of Object.entries(x)) {
      if (!v) continue;
      const val = Array.isArray(v) ? v.join('; ') : String(v);
      lines.push(`exp${i}_${k}: ${val.slice(0, 300)}`);
    }
  });

  const skills = resume.skills;
  if (typeof skills === 'string') {
    lines.push(`专业技能:\n${skills}`);
  } else if (skills && typeof skills === 'object') {
    for (const [cat, items] of Object.entries(skills)) {
      if (Array.isArray(items)) lines.push(`skills_${cat}: ${items.join(', ')}`);
    }
  }

  (resume.projects || []).forEach((proj, i) => {
    for (const [k, v] of Object.entries(proj)) {
      if (v) lines.push(`proj${i}_${k}: ${String(v).slice(0, 300)}`);
    }
  });

  (resume.languages || []).forEach((lang) => {
    lines.push(`lang_${lang.name || ''}: ${lang.level || ''}`);
  });

  (resume.awards || []).forEach((a) => {
    const parts = [a.name, a.level, a.org, a.date].filter(Boolean);
    if (parts.length) lines.push(`award: ${parts.join(' | ')}`);
  });
  if (resume.honors) lines.push(`honors: ${resume.honors}`);

  (resume.student_activities || []).forEach((sa) => {
    const parts = [sa.org, sa.role, sa.period, sa.desc].filter(Boolean);
    if (parts.length) lines.push(`activity: ${parts.join(' | ')}`);
  });

  if (resume.self_description) lines.push(`自我描述: ${resume.self_description}`);

  const oi = resume.other_info || {};
  for (const [k, v] of Object.entries(oi)) {
    if (v) lines.push(`${k}: ${v}`);
  }

  const pref = resume.preferences || {};
  for (const [k, v] of Object.entries(pref)) {
    if (v) lines.push(`pref_${k}: ${Array.isArray(v) ? v.join(', ') : v}`);
  }

  return lines.join('\n');
}

const SYSTEM_MSG = '你是JSON输出助手。严格返回JSON数组，不要输出任何解释、前言或后语。';

// ---------- Build LLM prompt (DOM pruning approach, ref OfferNow) ----------
function buildPrompt(formHTML, resume, { noThink = true } = {}) {
  let prompt =
    '你是表单填写助手。下面是网页表单的HTML结构和用户简历。请根据HTML上下文语义，判断每个 data-jh 标记的表单字段含义，并从简历中匹配填入值。\n\n' +
    '## 网页表单HTML\n```html\n' + formHTML + '\n```\n\n' +
    '## 简历数据\n' + resumeToKv(resume) + '\n\n' +
    '## 要求\n' +
    '返回JSON数组: [{"idx": data-jh编号, "value": "填入值"}, ...]\n' +
    '- 根据 <label> 或附近文本判断每个 data-jh 字段的含义\n' +
    '- name、placeholder 属性也是重要线索\n' +
    '- data-jh-type="select" 表示自定义下拉框，data-jh-type="datepicker" 表示日期选择器\n' +
    '- "请选择" 也通常表示下拉框或日期选择器，照常填写（程序会自动从下拉列表匹配最接近的选项）\n' +
    '- select 字段的 options 属性列出了可选值，必须从中选\n' +
    '- 日期字段用 YYYY-MM 格式（如 2023-09）\n' +
    '- 手机号只填数字（不含+86前缀）\n' +
    '- 尽量多填，所有能从简历匹配到的字段都要输出\n' +
    '- 只返回JSON，不要解释';
  if (noThink) prompt += '\n\n/no_think';
  return prompt;
}

// ---------- Parse LLM response ----------
function parseMapping(text) {
  if (!text || !text.trim()) {
    console.error('[JH] LLM returned empty response');
    return [];
  }
  text = text.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
  let m = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (m) text = m[1].trim();
  m = text.match(/\[[\s\S]*\]/);
  if (m) text = m[0];
  try {
    const arr = JSON.parse(text);
    console.log('[JH] Parsed mapping:', arr.length, 'items');
    return arr;
  } catch (e) {
    console.error('[JH] JSON parse failed:', e.message, '\nText:', text.slice(0, 500));
    return [];
  }
}

// ---------- Ollama API call ----------
async function callOllama(prompt, config) {
  const url = `${config.ollamaUrl}/api/chat`;
  const body = {
    model: config.model,
    messages: [
      { role: 'system', content: SYSTEM_MSG },
      { role: 'user', content: prompt },
    ],
    stream: false,
    options: {
      temperature: config.temperature || 0.1,
      num_ctx: config.numCtx || 32000,
      num_gpu: config.numGpu ?? 99,
    },
  };

  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const errText = await resp.text().catch(() => '');
    if (resp.status === 403) {
      throw new Error(
        'Ollama 拒绝访问(403)。请设置环境变量后重启:\n' +
        '  Windows: set OLLAMA_ORIGINS=* && ollama serve\n' +
        '  Linux/Mac: OLLAMA_ORIGINS=* ollama serve'
      );
    }
    throw new Error(`Ollama ${resp.status}: ${errText.slice(0, 200)}`);
  }

  const data = await resp.json();
  return data.message?.content || '';
}

// ---------- OpenAI-compatible API call (NVIDIA NIM, etc.) ----------
async function callOpenAI(prompt, config) {
  const url = `${config.openaiBaseUrl}/chat/completions`;
  const body = {
    model: config.model,
    messages: [
      { role: 'system', content: SYSTEM_MSG },
      { role: 'user', content: prompt },
    ],
    temperature: config.temperature || 0.1,
    max_tokens: 65536,
  };

  const headers = { 'Content-Type': 'application/json' };
  if (config.apiKey) {
    headers['Authorization'] = `Bearer ${config.apiKey}`;
  }

  console.log('[JH] callOpenAI →', url, 'model:', config.model, 'prompt length:', prompt.length);

  const resp = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const errText = await resp.text().catch(() => '');
    throw new Error(`API ${resp.status}: ${errText.slice(0, 300)}`);
  }

  const data = await resp.json();
  const choice = data.choices?.[0];
  const finish = choice?.finish_reason;
  const content = choice?.message?.content;
  const reasoning = choice?.message?.reasoning || choice?.message?.reasoning_content;
  console.log('[JH] API response: finish_reason:', finish,
    'content:', content?.length ?? 'null',
    'reasoning:', reasoning?.length ?? 'null');

  // Some reasoning models (nemotron, deepseek) put the answer in content,
  // but if content is null, try to extract JSON from reasoning
  if (content) return content;
  if (reasoning) {
    console.log('[JH] No content, extracting from reasoning...');
    const jsonMatch = reasoning.match(/\[[\s\S]*\]/);
    if (jsonMatch) return jsonMatch[0];
  }
  if (finish === 'length') {
    throw new Error('模型输出被截断 (finish_reason=length)。请换更大的模型或减少表单字段数量。');
  }
  throw new Error(`API 返回空内容。finish_reason: ${finish}, response: ${JSON.stringify(data).slice(0, 300)}`);
}

// ---------- Message router ----------
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {

    case 'llmFill': {
      (async () => {
        try {
          const { llmConfig } = await chrome.storage.local.get('llmConfig');
          const config = { ...DEFAULT_CONFIG, ...llmConfig };
          const { resumeData } = await chrome.storage.local.get('resumeData');
          if (!resumeData) {
            sendResponse({ error: '未找到简历数据，请先在侧边栏导入' });
            return;
          }
          const flatResume = mergeResume(resumeData);
          const isOllama = config.provider !== 'openai';
          const prompt = buildPrompt(request.formHTML, flatResume, {
            noThink: isOllama,
          });
          console.log('[JH] Prompt length:', prompt.length, 'provider:', config.provider);
          console.log('[JH] === FULL PROMPT START ===\n' + prompt + '\n=== FULL PROMPT END ===');
          const raw = isOllama
            ? await callOllama(prompt, config)
            : await callOpenAI(prompt, config);
          console.log('[JH] LLM response:', raw.slice(0, 500));
          const mapping = parseMapping(raw);
          sendResponse({ mapping, raw });
        } catch (e) {
          console.error('[JH] llmFill error:', e);
          sendResponse({ error: e.message });
        }
      })();
      return true;
    }

    case 'getResumeData': {
      chrome.storage.local.get('resumeData', (result) => {
        sendResponse({ resumeData: result.resumeData || null });
      });
      return true;
    }

    case 'saveResumeData': {
      chrome.storage.local.set({ resumeData: request.data }, () => {
        sendResponse({ success: true });
      });
      return true;
    }

    case 'getConfig': {
      chrome.storage.local.get('llmConfig', (result) => {
        sendResponse({ config: { ...DEFAULT_CONFIG, ...result.llmConfig } });
      });
      return true;
    }

    case 'saveConfig': {
      chrome.storage.local.set({ llmConfig: request.config }, () => {
        sendResponse({ success: true });
      });
      return true;
    }

    case 'testConnection': {
      (async () => {
        try {
          const { llmConfig } = await chrome.storage.local.get('llmConfig');
          const config = { ...DEFAULT_CONFIG, ...llmConfig };
          if (config.provider === 'openai') {
            const headers = { 'Content-Type': 'application/json' };
            if (config.apiKey) headers['Authorization'] = `Bearer ${config.apiKey}`;
            const resp = await fetch(`${config.openaiBaseUrl}/models`, { headers });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            const models = (data.data || []).slice(0, 5).map((m) => m.id);
            sendResponse({ success: true, models, provider: 'openai' });
          } else {
            const resp = await fetch(`${config.ollamaUrl}/api/tags`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            sendResponse({
              success: true,
              models: (data.models || []).map((m) => m.name),
              provider: 'ollama',
            });
          }
        } catch (e) {
          sendResponse({ error: e.message });
        }
      })();
      return true;
    }
  }
});

// ---------- Track active tab ----------
chrome.tabs.onActivated.addListener((info) => {
  chrome.storage.local.set({ lastActiveTab: info.tabId });
});
chrome.tabs.onUpdated.addListener((tabId, change) => {
  if (change.status === 'complete') {
    chrome.storage.local.set({ lastActiveTab: tabId });
  }
});
