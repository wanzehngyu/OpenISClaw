/**
 * OpenISClaw Web UI — Frontend Application
 * TensorBoard-Style Econometrics Dashboard
 */

// ─── State ────────────────────────────────────────────────────────────────────────
const STATE = {
  currentPage: 'dashboard',
  datasets: [],
  results: [],
  skills: [],
  currentDataset: null,
  chatHistory: [],
  executionLogs: [],
};

// ─── Utility ─────────────────────────────────────────────────────────────────────

function api(path, options = {}) {
  return fetch(`/api${path}`, options).then(r => r.json());
}

function toast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function timeTag() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

function updateStatusBar() {
  document.getElementById('sb-data').textContent = `数据: ${STATE.datasets.length} 个`;
  document.getElementById('sb-results').textContent = `结果: ${STATE.results.length} 个`;
  document.getElementById('sb-time').textContent = new Date().toLocaleTimeString('zh-CN');
}

// ─── Navigation ──────────────────────────────────────────────────────────────────

function navTo(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const pageEl = document.getElementById(`page-${page}`);
  const navEl = document.querySelector(`.nav-item[data-page="${page}"]`);
  if (pageEl) pageEl.classList.add('active');
  if (navEl) navEl.classList.add('active');

  STATE.currentPage = page;

  // Page-specific loaders
  if (page === 'dashboard') loadDashboard();
  if (page === 'data') loadDataPage();
  if (page === 'results') loadResultsPage();
  if (page === 'chat') loadChatPage();
  if (page === 'skills') loadSkillsPage();
  if (page === 'panel-regression') initRegressionPage();
  if (page === 'iv-estimator') initIVPage();
  if (page === 'staggered-did') initDIDPage();
  if (page === 'psm') initPSMPage();
  if (page === 'rdd') initRDDPage();
  if (page === 'survival') initSurvivalPage();
  if (page === 'paper-writer') initPaperWriter();
}

document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    const page = el.dataset.page;
    if (page) navTo(page);
  });
});

// ─── Settings Modal ──────────────────────────────────────────────────────────────

document.getElementById('btn-settings').addEventListener('click', () => {
  document.getElementById('modal-overlay').classList.add('active');
  document.getElementById('settings-modal').classList.add('active');
  // Load saved settings
  const saved = localStorage.getItem('ois_settings');
  if (saved) {
    const s = JSON.parse(saved);
    if (s.apiKey) document.getElementById('setting-api-key').value = s.apiKey;
    if (s.model) document.getElementById('setting-model').value = s.model;
    if (s.baseUrl) document.getElementById('setting-base-url').value = s.baseUrl;
  }
});

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('active');
  document.getElementById('settings-modal').classList.remove('active');
}

function saveSettings() {
  const settings = {
    apiKey: document.getElementById('setting-api-key').value,
    model: document.getElementById('setting-model').value,
    baseUrl: document.getElementById('setting-base-url').value,
  };
  localStorage.setItem('ois_settings', JSON.stringify(settings));
  if (settings.apiKey) {
    // Apply via cookie/header workaround: store in localStorage + reload
    toast('设置已保存，部分配置需刷新页面后生效', 'success');
  }
  closeModal();
}

// ─── Dashboard ──────────────────────────────────────────────────────────────────

async function loadDashboard() {
  await Promise.all([loadDatasets(), loadResults(), loadSkills()]);
  renderDashboardDatasets();
  renderDashboardResults();
  renderDashboardSkills();
  loadHealthStatus();
}

async function loadHealthStatus() {
  try {
    const health = await api('/health');
    const apiDot = document.getElementById('api-dot');
    const apiText = document.getElementById('api-status-text');
    if (health.status === 'ok') {
      apiDot.className = 'status-dot ok';
      apiText.textContent = 'API 正常';
    } else {
      apiDot.className = 'status-dot warn';
      apiText.textContent = health.status;
    }
    document.getElementById('health-api').textContent = health.status;
    document.getElementById('health-api').className = 'health-value ' + (health.status === 'ok' ? 'ok' : 'warn');
    document.getElementById('health-model').textContent = health.model || '—';
    document.getElementById('health-skills').textContent = health.skills_base ? health.skills_base.split('/').slice(-2).join('/') : '—';
    const deps = health.missing_deps;
    const depEl = document.getElementById('health-deps');
    depEl.textContent = deps.length === 0 ? '✅ 完整' : `⚠️ ${deps.length} 缺失`;
    depEl.className = 'health-value ' + (deps.length === 0 ? 'ok' : 'warn');
  } catch (e) {
    document.getElementById('health-api').textContent = '❌ 连接失败';
  }
}

function renderDashboardDatasets() {
  const el = document.getElementById('dash-dataset-list');
  if (!STATE.datasets.length) {
    el.innerHTML = '<div class="empty-state small"><span>暂无数据集</span><button class="btn-sm" onclick="navTo(\'data\')">上传</button></div>';
    return;
  }
  el.innerHTML = STATE.datasets.slice(0, 5).map(ds => `
    <div class="dataset-item" onclick="loadDatasetPreview('${ds.name}')">
      <span class="dataset-icon">📊</span>
      <div class="dataset-info">
        <div class="dataset-name">${ds.name}</div>
        <div class="dataset-meta">${ds.type.toUpperCase()} · ${formatBytes(ds.size)}</div>
      </div>
    </div>
  `).join('');
}

function renderDashboardResults() {
  const el = document.getElementById('dash-result-list');
  if (!STATE.results.length) {
    el.innerHTML = '<div class="empty-state small"><span>还没有分析结果</span></div>';
    return;
  }
  el.innerHTML = STATE.results.slice(0, 5).map(r => `
    <div class="result-item" onclick="openResult('${r.id}')">
      <span class="result-icon">${iconForType(r.type)}</span>
      <div class="result-info">
        <div class="dataset-name">${r.name}</div>
        <div class="dataset-meta">${r.type} · ${formatBytes(r.size)}</div>
      </div>
    </div>
  `).join('');
}

function renderDashboardSkills() {
  const el = document.getElementById('dash-skills-tags');
  if (!STATE.skills.length) return;
  el.innerHTML = STATE.skills.map(s => `
    <span class="skill-tag" onclick="navTo('skills')">${s.name}</span>
  `).join('');
}

// ─── Data Page ──────────────────────────────────────────────────────────────────

async function loadDataPage() {
  await loadDatasets();
  renderDatasetGrid();
  setupUploadZone();
}

async function loadDatasets() {
  try {
    STATE.datasets = await api('/datasets');
  } catch (e) {
    STATE.datasets = [];
  }
  updateStatusBar();
  populateDatasetSelects();
}

function renderDatasetGrid() {
  const grid = document.getElementById('dataset-grid');
  if (!STATE.datasets.length) {
    grid.innerHTML = '<div class="empty-state">还没有数据集，拖拽文件到上方区域上传</div>';
    return;
  }
  grid.innerHTML = STATE.datasets.map(ds => `
    <div class="dataset-card" onclick="loadDatasetPreview('${ds.name}')">
      <div class="dataset-card-header">
        <span class="dataset-card-icon">${iconForType(ds.type)}</span>
        <span class="type-badge ${ds.type}">${ds.type.toUpperCase()}</span>
      </div>
      <div class="dataset-card-name">${ds.name}</div>
      <div class="dataset-card-meta">${formatBytes(ds.size)} · ${ds.modified.slice(0, 10)}</div>
    </div>
  `).join('');
}

function setupUploadZone() {
  const zone = document.getElementById('upload-zone');
  const input = document.getElementById('file-input');

  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files);
    files.forEach(f => uploadFile(f));
  });
  zone.addEventListener('click', () => input.click());
  input.addEventListener('change', () => {
    Array.from(input.files).forEach(f => uploadFile(f));
    input.value = '';
  });
}

async function uploadFile(file) {
  const progressEl = document.getElementById('upload-progress');
  const fillEl = document.getElementById('progress-fill');
  const textEl = document.getElementById('progress-text');
  progressEl.style.display = 'block';
  textEl.textContent = `上传 ${file.name}...`;
  fillEl.style.width = '30%';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const resp = await fetch('/api/datasets/upload', { method: 'POST', body: formData });
    const data = await resp.json();
    fillEl.style.width = '100%';
    if (data.success) {
      toast(`✅ ${file.name} 上传成功`, 'success');
      await loadDatasets();
      renderDatasetGrid();
    } else {
      toast(`❌ ${data.detail || '上传失败'}`, 'error');
    }
  } catch (e) {
    toast(`❌ 上传出错: ${e.message}`, 'error');
  }
  setTimeout(() => { progressEl.style.display = 'none'; fillEl.style.width = '0%'; }, 1500);
}

async function loadDatasetPreview(name) {
  STATE.currentDataset = name;
  const section = document.getElementById('preview-section');
  section.style.display = 'block';
  document.getElementById('preview-title').textContent = `预览: ${name}`;

  const infoEl = document.getElementById('preview-info');
  infoEl.innerHTML = '<div class="skeleton" style="height:40px;margin-bottom:14px"></div><div class="skeleton" style="height:200px"></div>';

  try {
    const data = await api(`/datasets/${encodeURIComponent(name)}/preview`);
    infoEl.innerHTML = `
      <div class="preview-stat"><div class="preview-stat-num">${data.rows}</div><div class="preview-stat-label">行（预览）</div></div>
      <div class="preview-stat"><div class="preview-stat-num">${data.total_rows}</div><div class="preview-stat-label">总行数</div></div>
      <div class="preview-stat"><div class="preview-stat-num">${data.columns.length}</div><div class="preview-stat-label">列</div></div>
    `;

    const table = document.getElementById('preview-table');
    const headers = data.columns.map(c => `<th title="${c.dtype}">${c.name}</th>`).join('');
    const rows = data.preview.map(row => `<tr>${row.map(v => `<td title="${v}">${v}</td>`).join('')}</tr>`).join('');
    table.innerHTML = `<thead><tr>${headers}</tr></thead><tbody>${rows}</tbody>`;

    // Column quality bars
    const qualityEl = document.getElementById('column-quality');
    qualityEl.innerHTML = data.columns.map(c => {
      const fill = c.type === 'numeric' ? 'green' : 'yellow';
      return `
        <div class="col-quality-item">
          <span class="col-quality-name" title="${c.dtype}">${c.name}</span>
          <div class="quality-bar"><div class="quality-fill ${fill}" style="width:${100 - c.missing_pct}%"></div></div>
          <span class="col-quality-pct">${c.missing_pct}% 缺失</span>
        </div>`;
    }).join('');

    // Update data selectors for skill pages
    populateDatasetSelects(data.columns);

  } catch (e) {
    infoEl.innerHTML = `<div class="empty-state">加载失败: ${e.message}</div>`;
  }
}

function showDataStats() {
  if (!STATE.currentDataset) return;
  // Simple summary already shown in preview-info
  toast('统计摘要已显示在上方', 'info');
}

function closePreview() {
  document.getElementById('preview-section').style.display = 'none';
  STATE.currentDataset = null;
}

// ─── Chat Page ──────────────────────────────────────────────────────────────────

async function loadChatPage() {
  await loadDatasets();
  populateChatDataSelect();
}

function populateChatDataSelect() {
  const sel = document.getElementById('chat-data-select');
  sel.innerHTML = '<option value="">未选择（可选）</option>' +
    STATE.datasets.map(ds => `<option value="${ds.name}">${ds.name}</option>`).join('');
}

function fillPrompt(text) {
  document.getElementById('chat-input').value = text;
}

async function sendChat() {
  const input = document.getElementById('chat-input');
  const task = input.value.trim();
  if (!task) return;

  const dataSelect = document.getElementById('chat-data-select');
  const dataPath = dataSelect.value ? `./user_data/${dataSelect.value}` : null;
  const autoExec = document.getElementById('chat-auto-execute').checked;
  const sendBtn = document.getElementById('chat-send-btn');

  // Remove welcome
  const welcome = document.querySelector('.chat-welcome');
  if (welcome) welcome.remove();

  // Add user message
  addChatMessage('user', task);

  // Add assistant placeholder
  const assistantEl = addChatMessage('assistant', '正在分析...');

  sendBtn.disabled = true;
  input.value = '';

  try {
    const resp = await api('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task, data_path: dataPath, auto_execute: autoExec }),
    });

    if (resp.error) {
      assistantEl.querySelector('.chat-message-bubble').innerHTML = `<span style="color:var(--danger)">❌ ${resp.error}</span>`;
    } else {
      assistantEl.querySelector('.chat-message-bubble').innerHTML = formatMarkdown(resp.reply);

      if (resp.script_command && autoExec) {
        const execDiv = document.createElement('div');
        execDiv.className = 'exec-output';
        execDiv.textContent = '⏳ 正在执行...';
        assistantEl.querySelector('.chat-message-content').appendChild(execDiv);

        if (resp.execution_result) {
          const r = resp.execution_result;
          execDiv.className = `exec-output ${r.success ? 'success' : 'error'}`;
          execDiv.textContent = r.stdout || r.stderr || (r.success ? '✅ 执行成功' : '❌ 执行失败');
          STATE.executionLogs.push({ time: new Date().toISOString(), ...r });
        }
      }
    }
  } catch (e) {
    assistantEl.querySelector('.chat-message-bubble').innerHTML = `<span style="color:var(--danger)">❌ 网络错误: ${e.message}</span>`;
  }

  sendBtn.disabled = false;
}

function addChatMessage(role, content) {
  const messagesEl = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-message ${role}`;
  const avatar = role === 'user' ? '👤' : '🤖';
  div.innerHTML = `
    <div class="chat-message-avatar">${avatar}</div>
    <div class="chat-message-content">
      <div class="chat-message-bubble">${content}</div>
      <div class="chat-message-time">${timeTag()}</div>
    </div>`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/```python\n([\s\S]*?)```/g, '<pre class="code-block"><code>$1</code></pre>')
    .replace(/```\n?([\s\S]*?)```/g, '<pre class="code-block"><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

// ─── Skills Pages Common ─────────────────────────────────────────────────────────

function populateDatasetSelects(columns = null) {
  ['pr', 'iv', 'did', 'psm', 'rdd', 'surv'].forEach(prefix => {
    const sel = document.getElementById(`${prefix}-data`);
    if (!sel) return;
    const current = sel.value;
    sel.innerHTML = '<option value="">— 选择数据 —</option>' +
      STATE.datasets.map(ds => `<option value="${ds.name}">${ds.name}</option>`).join('');
    if (current) sel.value = current;
  });
}

async function loadColumnsForDataset(datasetName, targetPrefix) {
  if (!datasetName) return;
  try {
    const data = await api(`/datasets/${encodeURIComponent(datasetName)}/preview`);
    const numericCols = data.columns.filter(c => c.type === 'numeric').map(c => c.name);
    const allCols = data.columns.map(c => c.name);

    // Y selector
    const ySel = document.getElementById(`${targetPrefix}-y`);
    if (ySel) {
      ySel.innerHTML = '<option value="">— 选择 —</option>' +
        numericCols.map(c => `<option value="${c}">${c}</option>`).join('');
    }

    // Entity/ID selectors
    const entitySel = document.getElementById(`${targetPrefix}-entity`) || document.getElementById(`${targetPrefix}-id`);
    if (entitySel) {
      entitySel.innerHTML = '<option value="">— 选择 —</option>' +
        allCols.map(c => `<option value="${c}">${c}</option>`).join('');
    }

    // Time selector
    const timeSel = document.getElementById(`${targetPrefix}-time`) || document.getElementById(`${targetPrefix}-t`);
    if (timeSel) {
      timeSel.innerHTML = '<option value="">— 选择 —</option>' +
        allCols.map(c => `<option value="${c}">${c}</option>`).join('');
    }

    // X / covariate checklist
    const xList = document.getElementById(`${targetPrefix}-x-list`) || document.getElementById(`${targetPrefix}-cov-list`) ||
                  document.getElementById(`${targetPrefix}-exog-list`) || document.getElementById(`${targetPrefix}-iv-list`);
    if (xList) {
      xList.innerHTML = numericCols.map(c => `
        <label class="checkbox-label">
          <input type="checkbox" value="${c}"> ${c}
        </label>`).join('');
    }

  } catch (e) {
    toast(`加载列信息失败: ${e.message}`, 'error');
  }
}

// ─── Panel Regression ────────────────────────────────────────────────────────────

function initRegressionPage() {
  loadDatasets().then(() => {
    document.getElementById('pr-data').innerHTML = '<option value="">— 选择数据 —</option>' +
      STATE.datasets.map(ds => `<option value="${ds.name}">${ds.name}</option>`).join('');
  });
  document.getElementById('pr-data').addEventListener('change', e => {
    if (e.target.value) loadColumnsForDataset(e.target.value, 'pr');
  });
}

function runPanelRegression() {
  console.log('[runPanelRegression] START — data=', document.getElementById('pr-data').value, 'y=', document.getElementById('pr-y').value);
  const checkedX = Array.from(document.querySelectorAll('#pr-x-list input:checked')).map(el => el.value);
  console.log('[runPanelRegression] checked X:', checkedX);
  document.getElementById('pr-result').innerHTML = '<div class="empty-state" style="color:#f97316">⏳ 正在准备执行...</div>';
  const data = document.getElementById('pr-data').value;
  const y = document.getElementById('pr-y').value;
  const entity = document.getElementById('pr-entity').value;
  const time = document.getElementById('pr-time').value;
  const cluster = document.querySelector('input[name="pr-cluster"]:checked')?.value || 'entity';

  // Collect checked X variables — each gets its own --x flag
  const xChecked = Array.from(document.querySelectorAll('#pr-x-list input:checked')).map(el => el.value);

  if (!data || !y || !entity || !time) {
    toast('请填写必填字段：数据集、因变量、个体ID、时间', 'error');
    return;
  }
  if (!xChecked.length) {
    toast('请至少选择一个解释变量 (X)', 'error');
    return;
  }

  const args = [
    '--data', `./user_data/${data}`,
    '--y', y,
  ];
  // Add --x flag for each selected variable (script expects one --x per variable)
  xChecked.forEach(x => { args.push('--x', x); });
  args.push(
    '--entity', entity,
    '--time', time,
    '--cluster', cluster,
    '--output_pickle', './user_output/panel_results.pkl',
  );

  executeSkill('panel-regression', args, 'pr-result', '📐 面板回归');
}

// ─── IV Estimator ───────────────────────────────────────────────────────────────

function initIVPage() {
  loadDatasets().then(() => {
    document.getElementById('iv-data').innerHTML = '<option value="">— 选择数据 —</option>' +
      STATE.datasets.map(ds => `<option value="${ds.name}">${ds.name}</option>`).join('');
  });
  document.getElementById('iv-data').addEventListener('change', e => {
    if (e.target.value) loadColumnsForDataset(e.target.value, 'iv');
  });
}

function loadIVColumns() {
  const data = document.getElementById('iv-data').value;
  if (!data) return;
  loadColumnsForDataset(data, 'iv');
  // Also setup endog and IV lists from same data
  api(`/datasets/${encodeURIComponent(data)}/preview`).then(data => {
    const allCols = data.columns.map(c => c.name);
    const numericCols = data.columns.filter(c => c.type === 'numeric').map(c => c.name);

    const endogSel = document.getElementById('iv-endog');
    if (endogSel) {
      endogSel.innerHTML = '<option value="">— 选择内生变量 —</option>' +
        numericCols.map(c => `<option value="${c}">${c}</option>`).join('');
    }

    const ivList = document.getElementById('iv-iv-list');
    if (ivList) {
      ivList.innerHTML = numericCols.map(c => `
        <label class="checkbox-label"><input type="checkbox" value="${c}"> ${c}</label>
      `).join('');
    }
  });
}

function runIV() {
  const data = document.getElementById('iv-data').value;
  const y = document.getElementById('iv-y').value;
  const endog = document.getElementById('iv-endog').value;
  const ivCheckboxes = document.querySelectorAll('#iv-iv-list input:checked');
  const instruments = Array.from(ivCheckboxes).map(el => el.value);
  const exogCheckboxes = document.querySelectorAll('#iv-exog-list input:checked');
  const exog = Array.from(exogCheckboxes).map(el => el.value);

  if (!data || !y || !endog || !instruments.length) {
    toast('请填写：数据集、因变量、内生变量、工具变量', 'error');
    return;
  }

  const args = [
    '--data', `./user_data/${data}`,
    '--y', y,
    '--endog', endog,
    '--iv', instruments.join(' '),
    '--output_pickle', './user_output/iv_results.pkl',
  ];
  if (exog.length) args.push('--exog', exog.join(' '));

  executeSkill('iv-estimator', args, 'iv-result', '🎯 IV 估计');
}

// ─── DID ─────────────────────────────────────────────────────────────────────────

function initDIDPage() {
  loadDatasets().then(() => {
    document.getElementById('did-data').innerHTML = '<option value="">— 选择数据 —</option>' +
      STATE.datasets.map(ds => `<option value="${ds.name}">${ds.name}</option>`).join('');
  });
  document.getElementById('did-data').addEventListener('change', e => {
    if (e.target.value) loadColumnsForDataset(e.target.value, 'did');
  });
}

function loadDIDColumns() {
  const data = document.getElementById('did-data').value;
  if (!data) return;
  api(`/datasets/${encodeURIComponent(data)}/preview`).then(d => {
    const cols = d.columns.map(c => c.name);
    ['did-y', 'did-g', 'did-id', 'did-t'].forEach((id, i) => {
      const sel = document.getElementById(id);
      if (sel) {
        sel.innerHTML = '<option value="">— 选择 —</option>' + cols.map(c => `<option value="${c}">${c}</option>`).join('');
      }
    });
  });
}

function runDID() {
  const data = document.getElementById('did-data').value;
  const y = document.getElementById('did-y').value;
  const g = document.getElementById('did-g').value;
  const id = document.getElementById('did-id').value;
  const t = document.getElementById('did-t').value;
  const cg = document.querySelector('input[name="did-cg"]:checked')?.value || 'notyettreated';
  const est = document.querySelector('input[name="did-est"]:checked')?.value || 'dr';
  const cov = document.getElementById('did-cov').value;

  if (!data || !y || !g || !id || !t) {
    toast('请填写：数据集、因变量、处理时间变量、个体ID、时间变量', 'error');
    return;
  }

  const args = [
    '--data', `./user_data/${data}`,
    '--y', y,
    '--t', t,
    '--id', id,
    '--g', g,
    '--est_method', est,
    '--control_group', cg,
    '--output_pickle', './user_output/did_results.pkl',
    '--plot_path', './user_output/event_study_plot.png',
  ];
  if (cov) args.push('--cov', cov);

  executeSkill('staggered-did', args, 'did-result', '⏱️ 多时点 DID');
}

// ─── PSM ─────────────────────────────────────────────────────────────────────────

function initPSMPage() {
  loadDatasets().then(() => {
    document.getElementById('psm-data').innerHTML = '<option value="">— 选择数据 —</option>' +
      STATE.datasets.map(ds => `<option value="${ds.name}">${ds.name}</option>`).join('');
  });
  document.getElementById('psm-data').addEventListener('change', e => {
    if (e.target.value) loadColumnsForDataset(e.target.value, 'psm');
  });
}

function loadPSMColumns() {
  const data = document.getElementById('psm-data').value;
  if (!data) return;
  api(`/datasets/${encodeURIComponent(data)}/preview`).then(d => {
    const numericCols = d.columns.filter(c => c.type === 'numeric').map(c => c.name);
    const allCols = d.columns.map(c => c.name);

    ['psm-y', 'psm-t'].forEach((id, i) => {
      const sel = document.getElementById(id);
      if (sel) sel.innerHTML = '<option value="">— 选择 —</option>' + allCols.map(c => `<option value="${c}">${c}</option>`).join('');
    });

    const covList = document.getElementById('psm-cov-list');
    if (covList) {
      covList.innerHTML = numericCols.map(c => `
        <label class="checkbox-label"><input type="checkbox" value="${c}"> ${c}</label>
      `).join('');
    }
  });
}

function runPSM() {
  const data = document.getElementById('psm-data').value;
  const y = document.getElementById('psm-y').value;
  const t = document.getElementById('psm-t').value;
  const method = document.getElementById('psm-method').value;
  const covs = Array.from(document.querySelectorAll('#psm-cov-list input:checked')).map(el => el.value);

  if (!data || !y || !t) { toast('请填写：数据集、结果变量、处理变量', 'error'); return; }

  const args = [
    '--data', `./user_data/${data}`,
    '--y', y,
    '--t', t,
    '--method', method,
    '--output_pickle', './user_output/psm_results.pkl',
  ];
  if (covs.length) args.push('--cov', covs.join(' '));

  executeSkill('propensity-score-matching', args, 'psm-result', '🔀 PSM');
}

// ─── RDD ─────────────────────────────────────────────────────────────────────────

function initRDDPage() {
  loadDatasets().then(() => {
    document.getElementById('rdd-data').innerHTML = '<option value="">— 选择数据 —</option>' +
      STATE.datasets.map(ds => `<option value="${ds.name}">${ds.name}</option>`).join('');
  });
  document.getElementById('rdd-data').addEventListener('change', e => {
    if (e.target.value) loadColumnsForDataset(e.target.value, 'rdd');
  });
}

function loadRDDColumns() {
  const data = document.getElementById('rdd-data').value;
  if (!data) return;
  api(`/datasets/${encodeURIComponent(data)}/preview`).then(d => {
    const cols = d.columns.map(c => c.name);
    ['rdd-y', 'rdd-x'].forEach(id => {
      const sel = document.getElementById(id);
      if (sel) sel.innerHTML = '<option value="">— 选择 —</option>' + cols.map(c => `<option value="${c}">${c}</option>`).join('');
    });
  });
}

function runRDD() {
  const data = document.getElementById('rdd-data').value;
  const y = document.getElementById('rdd-y').value;
  const x = document.getElementById('rdd-x').value;
  const cutoff = document.getElementById('rdd-cutoff').value;
  const bw = document.getElementById('rdd-bandwidth').value;
  const type = document.querySelector('input[name="rdd-type"]:checked')?.value || 'sharp';

  if (!data || !y || !x) { toast('请填写：数据集、结果变量、分配变量', 'error'); return; }

  const args = [
    '--data', `./user_data/${data}`,
    '--y', y,
    '--x', x,
    '--type', type,
    '--cutoff', cutoff,
    '--output_pickle', './user_output/rdd_results.pkl',
  ];
  if (bw) args.push('--bandwidth', bw);

  executeSkill('difference-in-discontinuities', args, 'rdd-result', '📍 RDD');
}

// ─── Survival ────────────────────────────────────────────────────────────────────

function initSurvivalPage() {
  loadDatasets().then(() => {
    document.getElementById('surv-data').innerHTML = '<option value="">— 选择数据 —</option>' +
      STATE.datasets.map(ds => `<option value="${ds.name}">${ds.name}</option>`).join('');
  });
  document.getElementById('surv-data').addEventListener('change', e => {
    if (e.target.value) loadColumnsForDataset(e.target.value, 'surv');
  });
}

function loadSurvColumns() {
  const data = document.getElementById('surv-data').value;
  if (!data) return;
  api(`/datasets/${encodeURIComponent(data)}/preview`).then(d => {
    const numericCols = d.columns.filter(c => c.type === 'numeric').map(c => c.name);
    const allCols = d.columns.map(c => c.name);

    ['surv-time', 'surv-event'].forEach(id => {
      const sel = document.getElementById(id);
      if (sel) sel.innerHTML = '<option value="">— 选择 —</option>' + allCols.map(c => `<option value="${c}">${c}</option>`).join('');
    });

    const covList = document.getElementById('surv-cov-list');
    if (covList) {
      covList.innerHTML = numericCols.map(c => `
        <label class="checkbox-label"><input type="checkbox" value="${c}"> ${c}</label>
      `).join('');
    }
  });
}

function runSurvival() {
  const data = document.getElementById('surv-data').value;
  const time = document.getElementById('surv-time').value;
  const event = document.getElementById('surv-event').value;
  const covs = Array.from(document.querySelectorAll('#surv-cov-list input:checked')).map(el => el.value);

  if (!data || !time || !event) { toast('请填写：数据集、时间变量、事件变量', 'error'); return; }

  const args = [
    '--data', `./user_data/${data}`,
    '--time', time,
    '--event', event,
    '--output_pickle', './user_output/survival_results.pkl',
  ];
  if (covs.length) args.push('--cov', covs.join(' '));

  executeSkill('survival-analysis', args, 'surv-result', '📉 生存分析');
}

// ─── Skill Execution ─────────────────────────────────────────────────────────────

async function executeSkill(skill, args, resultElId, label) {
  const el = document.getElementById(resultElId);
  if (!el) { alert(`错误: 找不到元素 #${resultElId}`); return; }

  // Loading state
  el.innerHTML = `<div style="text-align:center;padding:40px;background:#1e293b;border-radius:8px">
    <div style="font-size:2rem;margin-bottom:10px">⏳</div>
    <div style="color:#94a3b8">正在运行 ${label}...</div>
    <div style="font-family:monospace;font-size:0.75rem;color:#64748b;margin-top:8px;background:#0f172a;padding:8px;border-radius:4px;text-align:left;max-height:80px;overflow:auto;word-break:break-all">
    python3 skills/${skill}/scripts/...py ${args.join(' ')}
    </div></div>`;

  try {
    const resp = await api('/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skill, args }),
    });

    if (resp.success) {
      el.innerHTML = `<div class="exec-output success" style="max-height:500px;overflow:auto">${escapeHtml(resp.stdout || '✅ 执行成功')}</div>
        <div style="margin-top:12px">
          <button class="btn-sm" onclick="loadResultsPage()">📋 查看结果</button>
          <button class="btn-sm" onclick="loadDatasets()">📁 刷新数据</button>
        </div>`;
      toast(`${label} 执行成功`, 'success');
      STATE.executionLogs.push({ time: new Date().toISOString(), skill, args, ...resp });
      await loadResults();
    } else {
      el.innerHTML = `<div class="exec-output error" style="max-height:400px;overflow:auto">${escapeHtml((resp.stderr || resp.stdout || '').slice(-2000))}</div>
        <div style="margin-top:8px;font-size:0.8rem;color:#64748b;padding:8px;background:#0f172a;border-radius:4px;word-break:break-all">
          Command: ${escapeHtml((resp.command || '').slice(0, 200))}
        </div>`;
      toast(`${label} 执行失败`, 'error');
    }
  } catch (e) {
    el.innerHTML = `<div class="empty-state" style="text-align:left">❌ 网络错误: ${e.message}<br><br><button class='btn-sm' onclick='loadResultsPage()'>📋 查看已有结果</button></div>`;
    toast(`❌ 执行出错: ${e.message}`, 'error');
  }
}

// ─── Results Page ────────────────────────────────────────────────────────────────

async function loadResultsPage() {
  await loadResults();
  renderResultsByType();
}

async function loadResults() {
  try {
    STATE.results = await api('/results');
  } catch (e) {
    STATE.results = [];
  }
  updateStatusBar();
}

function renderResultsByType() {
  const tables = STATE.results.filter(r => r.type === 'table');
  const plots = STATE.results.filter(r => r.type === 'plot');
  const logs = STATE.executionLogs;

  document.getElementById('result-tables').innerHTML = tables.length
    ? tables.map(r => resultCard(r)).join('')
    : '<div class="empty-state">暂无表格结果</div>';

  document.getElementById('result-plots').innerHTML = plots.length
    ? plots.map(r => resultCard(r, true)).join('')
    : '<div class="empty-state">暂无图表结果</div>';

  const logsEl = document.getElementById('terminal-logs');
  logsEl.innerHTML = logs.length
    ? logs.map(l => `[${l.time.slice(11,19)}] ${l.skill}: ${l.success ? '✅' : '❌'}\n${l.stdout || l.stderr || ''}`).join('\n\n')
    : '暂无执行日志';

  document.getElementById('diagnostics-content').innerHTML = STATE.results.length
    ? STATE.results.slice(0, 5).map(r => `
        <div class="result-card" onclick="openResult('${r.id}')">
          <div class="result-card-info">
            <div class="result-card-name">${r.name}</div>
            <div class="result-card-meta">${r.type} · ${formatBytes(r.size)}</div>
          </div>
        </div>`).join('')
    : '<div class="empty-state">暂无诊断报告</div>';
}

function resultCard(r, isImage = false) {
  const icon = iconForType(r.type);
  return `
    <div class="result-card" onclick="openResult('${r.id}')">
      <div class="result-card-preview">${isImage ? `<img src="/api/results/${r.id}/file" style="max-width:100%;max-height:100%;object-fit:contain">` : icon}</div>
      <div class="result-card-info">
        <div class="result-card-name">${r.name}</div>
        <div class="result-card-meta">${r.type} · ${formatBytes(r.size)} · ${r.modified.slice(0,16)}</div>
      </div>
    </div>`;
}

async function openResult(filename) {
  try {
    const data = await api(`/results/${filename}`);
    if (data.content) {
      showModal(`📄 ${filename}`, `<pre style="white-space:pre-wrap;max-height:70vh;overflow:auto;font-size:0.85rem">${escapeHtml(data.content)}</pre>`);
    } else if (data.url) {
      showModal(`📊 ${filename}`, `<img src="${data.url}" style="max-width:100%;max-height:70vh;object-fit:contain">`);
    }
  } catch (e) {
    toast('无法加载结果文件', 'error');
  }
}

function showModal(title, content) {
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('settings-modal');
  modal.querySelector('.modal-header h3').textContent = title;
  modal.querySelector('.modal-body').innerHTML = `<div style="max-height:70vh;overflow:auto">${content}</div>`;
  modal.className = 'modal active';
  overlay.classList.add('active');
}

function showResultTab(tab) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`.tab-btn[data-tab="${tab}"]`)?.classList.add('active');
  document.getElementById(`tab-${tab}`)?.classList.add('active');
}

// ─── Skills Page ────────────────────────────────────────────────────────────────

async function loadSkillsPage() {
  if (!STATE.skills.length) {
    try {
      STATE.skills = await api('/skills');
    } catch (e) {
      STATE.skills = [];
    }
  }
  renderSkillsGrid();
}

function renderSkillsGrid() {
  const grid = document.getElementById('skills-grid');
  if (!STATE.skills.length) {
    grid.innerHTML = '<div class="empty-state">无法加载技能列表，请检查 API 服务状态</div>';
    return;
  }
  const ICONS = ['📊', '🎯', '⏱️', '🔀', '📍', '📉', '📝', '📐', '🔬', '📚', '🧩', '📋'];
  grid.innerHTML = STATE.skills.map((s, i) => `
    <div class="skill-card" onclick="openSkillPanel('${s.id}')">
      <div class="skill-card-icon">${ICONS[i % ICONS.length]}</div>
      <div class="skill-card-name">${s.name}</div>
      <div class="skill-card-desc">${s.description}</div>
      <div class="skill-card-keywords">
        ${(s.required_args || []).slice(0, 3).map(a => `<span class="keyword">${a}</span>`).join('')}
      </div>
    </div>`).join('');
}

function openSkillPanel(skillId) {
  navTo(skillId.replace(/is-/, '').replace(/-estimator/, '-estimator').replace(/is-theory-matcher/, 'chat'));
  // Map skill IDs to page names
  const pageMap = {
    'panel-regression': 'panel-regression',
    'iv-estimator': 'iv-estimator',
    'staggered-did': 'staggered-did',
    'propensity-score-matching': 'psm',
    'difference-in-discontinuities': 'rdd',
    'survival-analysis': 'survival',
    'paper-writer': 'paper-writer',
    'stargazer-exporter': 'results',
    'is-econometrics': 'chat',
    'is-theory-matcher': 'chat',
  };
  const page = pageMap[skillId] || 'chat';
  navTo(page);
}

// ─── Paper Writer ────────────────────────────────────────────────────────────────

let pwCurrentStep = 1;

function initPaperWriter() {
  loadResults().then(() => {
    const cb = document.getElementById('pw-result-checkboxes');
    cb.innerHTML = STATE.results.length
      ? STATE.results.map(r => `
          <label class="checkbox-label">
            <input type="checkbox" value="${r.id}"> ${r.name}
          </label>`).join('')
      : '<div style="color:var(--text-muted);font-size:0.85rem">暂无已生成的结果文件</div>';
  });

  document.querySelectorAll('.theory-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.theory-chip').forEach(c => c.classList.remove('selected'));
      chip.classList.add('selected');
      document.getElementById('pw-theory').value = chip.dataset.theory;
    });
  });
}

function wizardNext(step) {
  document.querySelectorAll('.wizard-step').forEach(s => {
    const n = parseInt(s.dataset.step);
    if (n < step) s.classList.add('done');
    if (n === step) { s.classList.add('done'); s.classList.remove('active'); }
    if (n === step + 1) s.classList.add('active');
  });
  document.querySelectorAll('.wizard-panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`.wizard-panel[data-panel="${step + 1}"]`)?.classList.add('active');
  pwCurrentStep = step + 1;
}

function wizardPrev(step) {
  document.querySelectorAll('.wizard-step').forEach(s => {
    const n = parseInt(s.dataset.step);
    if (n === step) { s.classList.remove('done'); s.classList.add('active'); }
    if (n > step) s.classList.remove('active', 'done');
  });
  document.querySelectorAll('.wizard-panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`.wizard-panel[data-panel="${step - 1}"]`)?.classList.add('active');
  pwCurrentStep = step - 1;
}

async function generatePaper() {
  const rq = document.getElementById('pw-rq').value;
  const theory = document.getElementById('pw-theory').value;
  const hypotheses = document.getElementById('pw-hypotheses').value;
  const variables = document.getElementById('pw-variables').value;
  const dataDesc = document.getElementById('pw-data-desc').value;
  const template = document.querySelector('input[name="pw-template"]:checked')?.value || 'ieee_dual_column';
  const preview = document.getElementById('paper-preview');
  const content = document.getElementById('paper-preview-content');

  preview.style.display = 'block';
  content.innerHTML = '<div style="text-align:center;padding:40px"><div style="font-size:2rem">⏳</div><div>正在生成论文，请稍候...</div></div>';

  try {
    const resp = await api('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task: `生成实证论文，研究问题：${rq}，数据描述：${dataDesc}，理论框架：${theory}，研究假设：${hypotheses}，变量列表：${variables}，使用${template}模板`,
        auto_execute: false,
      }),
    });

    content.innerHTML = formatMarkdown(resp.reply || '⚠️ 未收到回复');
    toast('论文生成完成', 'success');
  } catch (e) {
    content.innerHTML = `<div style="color:var(--danger)">❌ 生成失败: ${e.message}</div>`;
  }
}

function copyPaper() {
  const content = document.getElementById('paper-preview-content').innerText;
  navigator.clipboard.writeText(content).then(() => toast('已复制到剪贴板', 'success'));
}

function downloadPaper() {
  const content = document.getElementById('paper-preview-content').innerText;
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'paper.md';
  a.click();
  URL.revokeObjectURL(url);
}

// ─── Utilities ──────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function iconForType(type) {
  const icons = { table: '📋', plot: '📈', data: '📦', other: '📄' };
  return icons[type] || icons.other;
}

// ─── Init ───────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Restore settings from localStorage
  const saved = localStorage.getItem('ois_settings');
  if (saved) {
    const s = JSON.parse(saved);
    if (s.apiKey) {
      // Apply environment vars via a custom header approach isn't possible client-side
      // User must set them server-side; just warn
    }
  }

  navTo('dashboard');
  setInterval(updateStatusBar, 5000);
  updateStatusBar();
});
