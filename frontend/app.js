const state = {
  catalog: null,
  selectedProjectId: null,
  selectedModels: {},
  criticProfile: 'minimal_context',
};

const els = {
  refreshProjects: document.getElementById('refresh-projects'),
  projectsList: document.getElementById('projects-list'),
  projectDetail: document.getElementById('project-detail'),
  premiseText: document.getElementById('premise-text'),
  startJob: document.getElementById('start-job'),
  jobStatusLabel: document.getElementById('job-status-label'),
  jobMonitor: document.getElementById('job-monitor'),
  jobLogs: document.getElementById('job-logs'),
  workflowGuidance: document.getElementById('workflow-guidance'),
  useRecommended: document.getElementById('use-recommended'),
  saveReport: document.getElementById('save-report'),
  roleGrid: document.getElementById('role-grid'),
  runRoleCheck: document.getElementById('run-role-check'),
  checkerStatus: document.getElementById('checker-status'),
  checkerProgress: document.getElementById('checker-progress'),
  checkerReportPath: document.getElementById('checker-report-path'),
  checkerSummary: document.getElementById('checker-summary'),
  checkerLog: document.getElementById('checker-log'),
};

async function getJson(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function renderWorkflow() {
  els.workflowGuidance.innerHTML = '';
  (state.catalog?.workflow_guidance || []).forEach((line) => {
    const li = document.createElement('li');
    li.textContent = line;
    els.workflowGuidance.appendChild(li);
  });
}

function roleCardClass(result) {
  if (!result) return 'role-card';
  return `role-card ${result.passed ? 'passed' : 'failed'}`;
}

function renderRoleCards(resultsByRole = {}) {
  els.roleGrid.innerHTML = '';
  const roles = state.catalog?.workflow_order || [];
  roles.forEach((role) => {
    const card = document.createElement('section');
    card.className = roleCardClass(resultsByRole[role]);
    card.dataset.role = role;

    const title = document.createElement('h3');
    title.textContent = role[0].toUpperCase() + role.slice(1);
    card.appendChild(title);

    const label = document.createElement('label');
    label.className = 'stacked';
    label.innerHTML = `<span>Model</span>`;
    const select = document.createElement('select');
    select.dataset.role = role;
    (state.catalog?.discovered_models || []).forEach((model) => {
      const option = document.createElement('option');
      option.value = model;
      option.textContent = model;
      if ((state.selectedModels[role] || '') === model) option.selected = true;
      select.appendChild(option);
    });
    select.addEventListener('change', (event) => {
      state.selectedModels[role] = event.target.value;
    });
    label.appendChild(select);
    card.appendChild(label);

    if (role === 'critic') {
      const criticLabel = document.createElement('label');
      criticLabel.className = 'stacked';
      criticLabel.innerHTML = '<span>Critic Speed Profile</span>';
      const criticSelect = document.createElement('select');
      Object.entries(state.catalog?.critic_profiles || {}).forEach(([value, labelText]) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = labelText;
        if (state.criticProfile === value) option.selected = true;
        criticSelect.appendChild(option);
      });
      criticSelect.addEventListener('change', (event) => {
        state.criticProfile = event.target.value;
      });
      criticLabel.appendChild(criticSelect);
      card.appendChild(criticLabel);
    }

    const status = document.createElement('div');
    status.className = 'muted';
    if (resultsByRole[role]) {
      status.textContent = resultsByRole[role].passed ? `Pass in ${resultsByRole[role].duration_seconds}s` : `Fail in ${resultsByRole[role].duration_seconds}s`;
    } else {
      status.textContent = 'Queued';
    }
    card.appendChild(status);
    els.roleGrid.appendChild(card);
  });
}

function applyRecommended() {
  state.selectedModels = { ...(state.catalog?.recommended_selection || {}) };
  state.criticProfile = state.catalog?.default_critic_profile || 'minimal_context';
  renderRoleCards();
}

async function loadCatalog() {
  state.catalog = await getJson('/models');
  applyRecommended();
  renderWorkflow();
}

async function loadProjects() {
  const projects = await getJson('/projects');
  els.projectsList.innerHTML = '';
  projects.forEach((project) => {
    const item = document.createElement('button');
    item.type = 'button';
    item.className = `project-item${state.selectedProjectId === project.project_id ? ' active' : ''}`;
    item.innerHTML = `<strong>${project.project_name}</strong><div class="muted">${project.project_id}</div>`;
    item.addEventListener('click', async () => {
      state.selectedProjectId = project.project_id;
      renderProjects(projects);
      const detail = await getJson(`/projects/${project.project_id}`);
      els.projectDetail.textContent = JSON.stringify(detail, null, 2);
    });
    els.projectsList.appendChild(item);
  });
}

function renderProjects(projects) {
  els.projectsList.innerHTML = '';
  projects.forEach((project) => {
    const item = document.createElement('button');
    item.type = 'button';
    item.className = `project-item${state.selectedProjectId === project.project_id ? ' active' : ''}`;
    item.innerHTML = `<strong>${project.project_name}</strong><div class="muted">${project.project_id}</div>`;
    item.addEventListener('click', async () => {
      state.selectedProjectId = project.project_id;
      renderProjects(projects);
      const detail = await getJson(`/projects/${project.project_id}`);
      els.projectDetail.textContent = JSON.stringify(detail, null, 2);
    });
    els.projectsList.appendChild(item);
  });
}

async function startRecoveredJob() {
  const payload = {
    phase: 'P-100',
    payload: {
      project_id: state.selectedProjectId,
      premise_text: els.premiseText.value.trim(),
    },
  };
  const job = await getJson('/jobs/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const finalJob = await pollJobStatus(job.id);
  els.jobStatusLabel.textContent = finalJob.status;
  els.jobMonitor.textContent = JSON.stringify(finalJob, null, 2);
  const logs = await getJson(`/jobs/${finalJob.id}/logs`);
  els.jobLogs.textContent = JSON.stringify(logs.entries, null, 2);
}

function setRoleTesting(role) {
  const card = els.roleGrid.querySelector(`[data-role="${role}"]`);
  if (card) card.className = 'role-card testing';
}

async function runRoleCheck() {
  els.checkerStatus.textContent = 'RUNNING';
  els.checkerProgress.textContent = 'Recovered checker running through the workflow. Critic is usually the slowest role.';
  els.checkerReportPath.textContent = 'Saved report path will appear here when enabled.';
  els.checkerSummary.innerHTML = '';
  els.checkerLog.textContent = 'Starting recovered role-model check...';
  const roles = state.catalog.workflow_order;
  roles.forEach(setRoleTesting);

  const request = {
    roles,
    model_selection: state.selectedModels,
    critic_profile: state.criticProfile,
    save_report: els.saveReport.checked,
  };

  const started = await getJson('/role-model-checker/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  const result = await pollCheckerStatus(started.run_id);

  const resultsByRole = Object.fromEntries(result.results.map((entry) => [entry.role, entry]));
  renderRoleCards(resultsByRole);
  els.checkerStatus.textContent = result.status;
  els.checkerProgress.textContent = result.detail || 'Recovered checker finished.';
  els.checkerReportPath.textContent = result.report_path ? `Saved report: ${result.report_path}` : 'Run completed without saving a report.';
  els.checkerSummary.innerHTML = '';
  result.results.forEach((entry) => {
    const card = document.createElement('article');
    card.className = `summary-card ${entry.passed ? 'pass' : 'fail'}`;
    card.innerHTML = `<strong>${entry.role}</strong><div>${entry.passed ? 'PASS' : 'FAIL'}</div><div>${entry.duration_seconds}s</div>`;
    els.checkerSummary.appendChild(card);
  });
  els.checkerLog.textContent = result.results.map((entry) => {
    const warnings = entry.warnings.length ? `Warnings: ${entry.warnings.join(' | ')}` : 'Warnings: none';
    const findings = entry.findings.length ? `Findings: ${entry.findings.join(' | ')}` : 'Findings: none';
    return `${entry.role.toUpperCase()}\n${warnings}\n${findings}\nPreview: ${entry.preview || '(none)'}`;
  }).join('\n\n');
}

async function pollJobStatus(jobId) {
  let status = await getJson(`/jobs/${jobId}/status`);
  while (status.status === 'PENDING' || status.status === 'PROCESSING') {
    await new Promise((resolve) => setTimeout(resolve, 250));
    status = await getJson(`/jobs/${jobId}/status`);
  }
  return status;
}

async function pollCheckerStatus(runId) {
  let status = await getJson(`/role-model-checker/${runId}/status`);
  while (status.status === 'PENDING' || status.status === 'RUNNING') {
    els.checkerProgress.textContent = status.detail || 'Recovered checker still running...';
    await new Promise((resolve) => setTimeout(resolve, 250));
    status = await getJson(`/role-model-checker/${runId}/status`);
  }
  return status;
}

els.refreshProjects.addEventListener('click', loadProjects);
els.useRecommended.addEventListener('click', applyRecommended);
els.startJob.addEventListener('click', startRecoveredJob);
els.runRoleCheck.addEventListener('click', runRoleCheck);

Promise.all([loadCatalog(), loadProjects()]).catch((error) => {
  els.checkerProgress.textContent = `Failed to initialize recovered console: ${error.message}`;
  els.projectDetail.textContent = `Failed to load recovered project view: ${error.message}`;
});
