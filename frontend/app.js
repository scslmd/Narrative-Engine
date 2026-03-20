const state = {
  catalog: null,
  projects: [],
  selectedProjectId: null,
  selectedProject: null,
  selectedModels: {},
  criticProfile: 'minimal_context',
  checkerResults: [],
};

const storagePrefix = 'narrative-engine-workspace:';

const els = {
  refreshProjects: document.getElementById('refresh-projects'),
  projectsList: document.getElementById('projects-list'),
  projectDetail: document.getElementById('project-detail'),
  createProjectForm: document.getElementById('create-project-form'),
  projectNameInput: document.getElementById('project-name-input'),
  genreInput: document.getElementById('genre-input'),
  toneInput: document.getElementById('tone-input'),
  povSelect: document.getElementById('pov-select'),
  storyStructureSelect: document.getElementById('story-structure-select'),
  primaryLanguageInput: document.getElementById('primary-language-input'),
  secondaryLanguageInput: document.getElementById('secondary-language-input'),
  premiseText: document.getElementById('premise-text'),
  constraintsInput: document.getElementById('constraints-input'),
  createProjectStatus: document.getElementById('create-project-status'),
  activeProjectName: document.getElementById('active-project-name'),
  activeProjectMeta: document.getElementById('active-project-meta'),
  activeProjectHealth: document.getElementById('active-project-health'),
  workspaceStatus: document.getElementById('workspace-status'),
  synopsisSeed: document.getElementById('synopsis-seed'),
  constraintChips: document.getElementById('constraint-chips'),
  storyBibleMap: document.getElementById('story-bible-map'),
  characterNotes: document.getElementById('character-notes'),
  worldNotes: document.getElementById('world-notes'),
  continuityNotes: document.getElementById('continuity-notes'),
  chapterBrief: document.getElementById('chapter-brief'),
  continuityRisks: document.getElementById('continuity-risks'),
  stageStrip: document.getElementById('stage-strip'),
  artifactManifest: document.getElementById('artifact-manifest'),
  artifactSequence: document.getElementById('artifact-sequence'),
  artifactChapter: document.getElementById('artifact-chapter'),
  artifactViewer: document.getElementById('artifact-viewer'),
  buildPacket: document.getElementById('build-packet'),
  chapterPacket: document.getElementById('chapter-packet'),
  continuityLens: document.getElementById('continuity-lens'),
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
  checkerSummary: document.getElementById('checker-summary'),
  checkerLog: document.getElementById('checker-log'),
  checkerReportPath: document.getElementById('checker-report-path'),
};

async function getJson(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch (_error) {
      // Keep the HTTP status text if the response is not JSON.
    }
    throw new Error(detail);
  }
  return response.json();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getWorkspaceKey(projectId) {
  return `${storagePrefix}${projectId}`;
}

function defaultWorkspaceState() {
  return {
    characterNotes: '',
    worldNotes: '',
    continuityNotes: '',
    chapterBrief: '',
    continuityRisks: '',
  };
}

function readWorkspaceNotes(projectId) {
  if (!projectId) {
    return defaultWorkspaceState();
  }
  try {
    const raw = window.localStorage.getItem(getWorkspaceKey(projectId));
    return raw ? { ...defaultWorkspaceState(), ...JSON.parse(raw) } : defaultWorkspaceState();
  } catch (_error) {
    return defaultWorkspaceState();
  }
}

function titleCase(value) {
  return value
    .split(/[_-]/g)
    .filter(Boolean)
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(' ');
}

function splitConstraints(rawValue) {
  return rawValue
    .split(/\r?\n|,/g)
    .map((item) => item.trim())
    .filter(Boolean);
}

function getConstraintList() {
  return state.selectedProject?.manifest?.constraints || [];
}

function getContinuityItems() {
  const notes = readWorkspaceNotes(state.selectedProjectId);
  return [
    ...getConstraintList(),
    ...splitConstraints(notes.continuityNotes),
    ...splitConstraints(notes.continuityRisks),
  ].slice(0, 12);
}

function renderWorkflow() {
  els.workflowGuidance.innerHTML = '';
  (state.catalog?.workflow_guidance || []).forEach((line) => {
    const item = document.createElement('article');
    item.className = 'guidance-item';
    item.textContent = line;
    els.workflowGuidance.appendChild(item);
  });
}

function renderWorkspaceStatus() {
  if (!state.selectedProjectId) {
    els.workspaceStatus.textContent = 'Select a project to open local workspace notes.';
    return;
  }
  const notes = readWorkspaceNotes(state.selectedProjectId);
  const filledCount = [notes.characterNotes, notes.worldNotes, notes.continuityNotes, notes.chapterBrief, notes.continuityRisks]
    .filter((value) => value && value.trim()).length;
  els.workspaceStatus.textContent = filledCount
    ? `${filledCount} workspace sections filled for this project.`
    : 'Local workspace notes are empty.';
}

function renderStoryBibleMap() {
  const manifest = state.selectedProject?.manifest;
  const notes = readWorkspaceNotes(state.selectedProjectId);
  const sections = [
    {
      title: 'Synopsis',
      detail: manifest?.premise_text ? 'Loaded from manifest' : 'Needs a stronger premise seed',
      complete: Boolean(manifest?.premise_text),
    },
    {
      title: 'Characters',
      detail: notes.characterNotes ? 'Character signals captured' : 'Add cast roles and relationship tension',
      complete: Boolean(notes.characterNotes),
    },
    {
      title: 'World',
      detail: notes.worldNotes ? 'World rules captured' : 'Add setting systems and story limits',
      complete: Boolean(notes.worldNotes),
    },
    {
      title: 'Continuity',
      detail: notes.continuityNotes || notes.continuityRisks ? 'Continuity watchlist assembled' : 'No continuity guardrails yet',
      complete: Boolean(notes.continuityNotes || notes.continuityRisks),
    },
  ];

  els.storyBibleMap.innerHTML = '';
  sections.forEach((section) => {
    const item = document.createElement('article');
    item.className = `map-card${section.complete ? ' complete' : ''}`;
    item.innerHTML = `<strong>${section.title}</strong><span>${section.detail}</span>`;
    els.storyBibleMap.appendChild(item);
  });
}

function renderConstraintChips() {
  els.constraintChips.innerHTML = '';
  const constraints = getConstraintList();
  if (!constraints.length) {
    els.constraintChips.innerHTML = '<span class="chip muted-chip">No explicit project constraints saved.</span>';
    return;
  }
  constraints.forEach((constraint) => {
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.textContent = constraint;
    els.constraintChips.appendChild(chip);
  });
}

function renderContinuityLens() {
  const items = getContinuityItems();
  if (!items.length) {
    els.continuityLens.innerHTML = '<div class="detail-box muted">No continuity protections assembled yet.</div>';
    return;
  }
  els.continuityLens.innerHTML = '';
  items.forEach((item) => {
    const row = document.createElement('article');
    row.className = 'continuity-item';
    row.innerHTML = `<strong>Guard</strong><span>${item}</span>`;
    els.continuityLens.appendChild(row);
  });
}

function buildChapterPacketText() {
  const manifest = state.selectedProject?.manifest;
  const notes = readWorkspaceNotes(state.selectedProjectId);
  const constraints = getConstraintList();
  const continuityItems = getContinuityItems();
  return [
    `PROJECT: ${manifest?.project_name || '(none selected)'}`,
    `GENRE: ${manifest?.config?.genre || '(unknown)'}`,
    `TONE: ${manifest?.config?.tone_profile || '(unknown)'}`,
    `STRUCTURE: ${manifest?.config?.story_structure || '(unknown)'}`,
    '',
    'SYNOPSIS SEED',
    manifest?.premise_text || '(none)',
    '',
    'CHARACTER SIGNALS',
    notes.characterNotes || '(none)',
    '',
    'WORLD RULES',
    notes.worldNotes || '(none)',
    '',
    'CHAPTER BRIEF',
    notes.chapterBrief || '(none)',
    '',
    'CONTINUITY RISKS',
    notes.continuityRisks || '(none)',
    '',
    'PROTECTED FACTS',
    continuityItems.length ? `- ${continuityItems.join('\n- ')}` : '(none)',
    '',
    'PROJECT CONSTRAINTS',
    constraints.length ? `- ${constraints.join('\n- ')}` : '(none)',
  ].join('\n');
}

function renderChapterPacket() {
  els.chapterPacket.textContent = buildChapterPacketText();
}

function saveWorkspaceNotes() {
  if (!state.selectedProjectId) {
    return;
  }
  window.localStorage.setItem(
    getWorkspaceKey(state.selectedProjectId),
    JSON.stringify({
      characterNotes: els.characterNotes.value,
      worldNotes: els.worldNotes.value,
      continuityNotes: els.continuityNotes.value,
      chapterBrief: els.chapterBrief.value,
      continuityRisks: els.continuityRisks.value,
    }),
  );
  renderWorkspaceStatus();
  renderStoryBibleMap();
  renderContinuityLens();
  renderChapterPacket();
  renderStageStrip();
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
    title.textContent = titleCase(role);
    card.appendChild(title);

    const recommendation = document.createElement('p');
    recommendation.className = 'muted';
    recommendation.textContent = state.catalog?.recommended_selection?.[role]
      ? `Recommended: ${state.catalog.recommended_selection[role]}`
      : 'No recommended discovered model yet.';
    card.appendChild(recommendation);

    const label = document.createElement('label');
    label.className = 'stacked';
    label.innerHTML = '<span>Model</span>';
    const select = document.createElement('select');
    select.dataset.role = role;

    const blank = document.createElement('option');
    blank.value = '';
    blank.textContent = 'Use recommended/default';
    if (!state.selectedModels[role]) blank.selected = true;
    select.appendChild(blank);

    (state.catalog?.discovered_models || []).forEach((model) => {
      const option = document.createElement('option');
      option.value = model;
      option.textContent = model;
      if ((state.selectedModels[role] || '') === model) option.selected = true;
      select.appendChild(option);
    });
    select.addEventListener('change', (event) => {
      const nextValue = event.target.value;
      if (nextValue) {
        state.selectedModels[role] = nextValue;
      } else {
        delete state.selectedModels[role];
      }
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
    status.className = 'muted role-status';
    status.textContent = resultsByRole[role]
      ? `${resultsByRole[role].passed ? 'Pass' : 'Fail'} in ${resultsByRole[role].duration_seconds}s`
      : 'Ready for evaluation';
    card.appendChild(status);
    els.roleGrid.appendChild(card);
  });
}

function applyRecommended() {
  state.selectedModels = { ...(state.catalog?.recommended_selection || {}) };
  state.criticProfile = state.catalog?.default_critic_profile || 'minimal_context';
  renderRoleCards(Object.fromEntries(state.checkerResults.map((entry) => [entry.role, entry])));
}

function renderProjects() {
  els.projectsList.innerHTML = '';
  if (!state.projects.length) {
    const empty = document.createElement('div');
    empty.className = 'detail-box muted';
    empty.textContent = 'No projects yet. Create one from the setup form.';
    els.projectsList.appendChild(empty);
    return;
  }

  state.projects.forEach((project) => {
    const item = document.createElement('button');
    item.type = 'button';
    item.className = `project-item${state.selectedProjectId === project.project_id ? ' active' : ''}`;
    item.innerHTML = `
      <strong>${project.project_name}</strong>
      <div class="muted">${project.genre} · ${project.story_structure}</div>
      <div class="micro-copy">${project.project_id}</div>
    `;
    item.addEventListener('click', () => selectProject(project.project_id));
    els.projectsList.appendChild(item);
  });
}

function renderHealthCards(projectDetail) {
  const manifest = projectDetail?.manifest;
  const cards = [
    { label: 'Genre', value: manifest?.config?.genre || 'Not set' },
    { label: 'Tone', value: manifest?.config?.tone_profile || 'Not set' },
    { label: 'Structure', value: titleCase(manifest?.config?.story_structure || 'unknown') },
    {
      label: 'Artifacts',
      value: [
        projectDetail?.sequence_exists ? 'Sequence' : null,
        projectDetail?.chapter_exists ? 'Chapter' : null,
        projectDetail?.database_exists ? 'DB' : null,
      ].filter(Boolean).join(' · ') || 'Manifest only',
    },
  ];

  els.activeProjectHealth.innerHTML = cards
    .map((card) => `<article class="health-card"><span>${card.label}</span><strong>${card.value}</strong></article>`)
    .join('');
}

function renderStageStrip() {
  const notes = readWorkspaceNotes(state.selectedProjectId);
  const manifest = state.selectedProject?.manifest;
  const stages = [
    {
      name: 'Setup',
      complete: Boolean(state.selectedProjectId),
      detail: manifest?.project_name || 'Select or create a project',
    },
    {
      name: 'Story Engine',
      complete: Boolean(manifest?.premise_text || notes.characterNotes || notes.worldNotes || notes.continuityNotes),
      detail: manifest?.premise_text ? 'Story spine loaded' : 'Add cast, world, and continuity notes',
    },
    {
      name: 'Draft',
      complete: Boolean(notes.chapterBrief || notes.continuityRisks),
      detail: notes.chapterBrief ? 'Chapter packet staged' : 'Stage chapter intent and continuity risks',
    },
    {
      name: 'Review',
      complete: Boolean(state.checkerResults.length),
      detail: state.checkerResults.length ? 'Checker run captured' : 'Run the role-model checker',
    },
  ];

  els.stageStrip.innerHTML = '';
  stages.forEach((stage) => {
    const card = document.createElement('article');
    card.className = `stage-card${stage.complete ? ' complete' : ''}`;
    card.innerHTML = `<strong>${stage.name}</strong><span>${stage.detail}</span>`;
    els.stageStrip.appendChild(card);
  });
}

function hydrateWorkspaceNotes() {
  const notes = readWorkspaceNotes(state.selectedProjectId);
  els.characterNotes.value = notes.characterNotes;
  els.worldNotes.value = notes.worldNotes;
  els.continuityNotes.value = notes.continuityNotes;
  els.chapterBrief.value = notes.chapterBrief;
  els.continuityRisks.value = notes.continuityRisks;
  renderWorkspaceStatus();
  renderStoryBibleMap();
  renderContinuityLens();
  renderChapterPacket();
  renderStageStrip();
}

function renderSelectedProject() {
  const detail = state.selectedProject;
  const manifest = detail?.manifest;
  if (!detail || !manifest) {
    els.activeProjectName.textContent = 'Select a project';
    els.activeProjectMeta.textContent = 'Project detail, planning cues, and artifact review appear here.';
    els.activeProjectHealth.innerHTML = '';
    els.synopsisSeed.textContent = 'Choose a project to inspect its story spine.';
    els.projectDetail.textContent = 'Select a project to inspect its manifest and operational state.';
    els.artifactViewer.textContent = 'Artifact preview will appear here.';
    els.constraintChips.innerHTML = '<span class="chip muted-chip">No project selected.</span>';
    renderWorkspaceStatus();
    renderStoryBibleMap();
    renderContinuityLens();
    renderChapterPacket();
    renderStageStrip();
    return;
  }

  const summary = `${manifest.config.genre} · ${manifest.config.tone_profile} · ${titleCase(manifest.config.story_structure)} · POV ${manifest.config.pov}`;
  els.activeProjectName.textContent = manifest.project_name;
  els.activeProjectMeta.textContent = summary;
  els.synopsisSeed.textContent = manifest.premise_text || 'No synopsis seed saved yet.';
  els.projectDetail.textContent = JSON.stringify(detail, null, 2);
  renderHealthCards(detail);
  renderConstraintChips();
  renderWorkspaceStatus();
  renderStoryBibleMap();
  renderContinuityLens();
  renderChapterPacket();
  renderStageStrip();
}

async function loadCatalog() {
  state.catalog = await getJson('/models');
  applyRecommended();
  renderWorkflow();
}

async function loadProjects() {
  state.projects = await getJson('/projects');
  renderProjects();
  if (state.selectedProjectId && state.projects.some((project) => project.project_id === state.selectedProjectId)) {
    await selectProject(state.selectedProjectId, { preserveArtifactViewer: true });
  }
}

async function selectProject(projectId, options = {}) {
  state.selectedProjectId = projectId;
  state.checkerResults = [];
  renderProjects();
  const detail = await getJson(`/projects/${projectId}`);
  state.selectedProject = detail;
  renderSelectedProject();
  hydrateWorkspaceNotes();
  if (!options.preserveArtifactViewer) {
    els.artifactViewer.textContent = 'Artifact preview will appear here.';
  }
}

async function createProject(event) {
  event.preventDefault();
  const payload = {
    project_name: els.projectNameInput.value.trim(),
    config: {
      genre: els.genreInput.value.trim(),
      tone_profile: els.toneInput.value.trim(),
      pov: els.povSelect.value,
      primary_language: els.primaryLanguageInput.value.trim(),
      secondary_language: els.secondaryLanguageInput.value.trim(),
      story_structure: els.storyStructureSelect.value,
    },
    premise_text: els.premiseText.value.trim() || null,
    constraints: splitConstraints(els.constraintsInput.value),
  };

  const project = await getJson('/projects/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  els.createProjectStatus.textContent = `Created ${project.project_name}`;
  els.createProjectForm.reset();
  els.primaryLanguageInput.value = 'English';
  els.secondaryLanguageInput.value = 'None';
  els.povSelect.value = 'Third_Limited';
  els.storyStructureSelect.value = 'THREE_ACT';
  await loadProjects();
  await selectProject(project.project_id);
}

async function loadArtifact(kind) {
  if (!state.selectedProjectId) {
    throw new Error('Select a project first.');
  }
  const path = kind === 'chapter' ? 'chapter-1' : kind;
  const artifact = await getJson(`/projects/${state.selectedProjectId}/${path}`);
  els.artifactViewer.textContent = artifact.content;
}

async function pollJobStatus(jobId) {
  let status = await getJson(`/jobs/${jobId}/status`);
  for (let attempt = 0; attempt < 8; attempt += 1) {
    els.jobStatusLabel.textContent = status.status;
    els.jobMonitor.textContent = JSON.stringify(status, null, 2);
    if (status.status === 'COMPLETED' || status.status === 'FAILED') {
      return status;
    }
    await sleep(600);
    status = await getJson(`/jobs/${jobId}/status`);
  }
  return status;
}

async function startJob() {
  if (!state.selectedProjectId) {
    throw new Error('Select or create a project before starting a job.');
  }

  const notes = readWorkspaceNotes(state.selectedProjectId);
  const payload = {
    phase: 'P-100',
    payload: {
      project_id: state.selectedProjectId,
      premise_text: els.premiseText.value.trim() || state.selectedProject?.manifest?.premise_text || null,
      chapter_brief: notes.chapterBrief || null,
      continuity_notes: notes.continuityNotes || null,
      continuity_risks: notes.continuityRisks || null,
    },
  };

  els.jobStatusLabel.textContent = 'RUNNING';
  const job = await getJson('/jobs/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const finalStatus = await pollJobStatus(job.id);
  els.jobStatusLabel.textContent = finalStatus.status;
  els.jobMonitor.textContent = JSON.stringify(finalStatus, null, 2);
  const logs = await getJson(`/jobs/${job.id}/logs`);
  els.jobLogs.textContent = JSON.stringify(logs.entries, null, 2);
}

function buildPacket() {
  if (!state.selectedProjectId) {
    throw new Error('Select a project before building a chapter packet.');
  }
  saveWorkspaceNotes();
  renderChapterPacket();
}

function setRoleTesting(role) {
  const card = els.roleGrid.querySelector(`[data-role="${role}"]`);
  if (card) card.className = 'role-card testing';
}

async function pollCheckerStatus(runId, initialResult) {
  let result = initialResult;
  for (let attempt = 0; attempt < 8; attempt += 1) {
    if (result.status === 'COMPLETED' || result.status === 'FAILED') {
      return result;
    }
    await sleep(600);
    result = await getJson(`/role-model-checker/${runId}/status`);
  }
  return result;
}

async function runRoleCheck() {
  if (!state.catalog) {
    throw new Error('Model catalog not loaded yet.');
  }

  els.checkerStatus.textContent = 'RUNNING';
  els.checkerProgress.textContent = 'Checker is walking the role workflow.';
  els.checkerSummary.innerHTML = '';
  els.checkerLog.textContent = 'Starting role-model check...';
  els.checkerReportPath.textContent = 'Saved report path will appear here when enabled.';

  const roles = state.catalog.workflow_order;
  roles.forEach(setRoleTesting);

  const request = {
    roles,
    model_selection: state.selectedModels,
    critic_profile: state.criticProfile,
    save_report: els.saveReport.checked,
  };

  const started = await getJson('/role-model-checker/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  const result = await pollCheckerStatus(started.run_id, started);

  state.checkerResults = result.results || [];
  const resultsByRole = Object.fromEntries(state.checkerResults.map((entry) => [entry.role, entry]));
  renderRoleCards(resultsByRole);
  renderStageStrip();
  els.checkerStatus.textContent = result.status;
  els.checkerProgress.textContent = result.detail || 'Checker finished.';
  els.checkerSummary.innerHTML = '';
  state.checkerResults.forEach((entry) => {
    const card = document.createElement('article');
    card.className = `summary-card ${entry.passed ? 'pass' : 'fail'}`;
    card.innerHTML = `<strong>${titleCase(entry.role)}</strong><div>${entry.passed ? 'PASS' : 'FAIL'}</div><div>${entry.duration_seconds}s</div>`;
    els.checkerSummary.appendChild(card);
  });
  els.checkerReportPath.textContent = result.report_path
    ? `Report saved to ${result.report_path}`
    : 'No report saved for this run.';
  els.checkerLog.textContent = state.checkerResults.map((entry) => {
    const warnings = entry.warnings.length ? `Warnings: ${entry.warnings.join(' | ')}` : 'Warnings: none';
    const findings = entry.findings.length ? `Findings: ${entry.findings.join(' | ')}` : 'Findings: none';
    return `${entry.role.toUpperCase()}\n${warnings}\n${findings}\nPreview: ${entry.preview || '(none)'}`;
  }).join('\n\n');
}

function attachWorkspaceListeners() {
  [els.characterNotes, els.worldNotes, els.continuityNotes, els.chapterBrief, els.continuityRisks].forEach((element) => {
    element.addEventListener('input', saveWorkspaceNotes);
  });
}

els.refreshProjects.addEventListener('click', () => {
  loadProjects().catch((error) => {
    els.createProjectStatus.textContent = `Project refresh failed: ${error.message}`;
  });
});
els.useRecommended.addEventListener('click', applyRecommended);
els.createProjectForm.addEventListener('submit', (event) => {
  createProject(event).catch((error) => {
    els.createProjectStatus.textContent = `Create failed: ${error.message}`;
  });
});
els.buildPacket.addEventListener('click', () => {
  try {
    buildPacket();
  } catch (error) {
    els.chapterPacket.textContent = error.message;
  }
});
els.startJob.addEventListener('click', () => {
  startJob().catch((error) => {
    els.jobStatusLabel.textContent = 'ERROR';
    els.jobMonitor.textContent = error.message;
  });
});
els.runRoleCheck.addEventListener('click', () => {
  runRoleCheck().catch((error) => {
    els.checkerStatus.textContent = 'ERROR';
    els.checkerProgress.textContent = error.message;
  });
});
els.artifactManifest.addEventListener('click', () => {
  loadArtifact('manifest').catch((error) => {
    els.artifactViewer.textContent = error.message;
  });
});
els.artifactSequence.addEventListener('click', () => {
  loadArtifact('sequence').catch((error) => {
    els.artifactViewer.textContent = error.message;
  });
});
els.artifactChapter.addEventListener('click', () => {
  loadArtifact('chapter').catch((error) => {
    els.artifactViewer.textContent = error.message;
  });
});

attachWorkspaceListeners();

Promise.all([loadCatalog(), loadProjects()])
  .then(() => {
    renderSelectedProject();
  })
  .catch((error) => {
    els.checkerProgress.textContent = `Failed to initialize console: ${error.message}`;
    els.projectDetail.textContent = `Failed to load project view: ${error.message}`;
  });
