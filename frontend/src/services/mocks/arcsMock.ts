export interface ArcCandidate {
  arc_id: string;
  project_id: string;
  name: string;
  summary: string;
  stage_map_notes: string[];
  fit_notes: string[];
  tags: string[];
}

export interface ArcSelection {
  selection_id: string;
  project_id: string;
  selected_arc_id: string;
  character_id: string | null;
  rationale: string;
  alternatives_considered: string[];
}

export interface ArcStageMap {
  map_id: string;
  project_id: string;
  arc_id: string;
  stages: ArcStage[];
}

export interface ArcStage {
  stage_name: string;
  beat_notes: string[];
  emotional_state: string;
  key_decisions: string[];
}

const MOCK_DELAY = 2000;

// Mock data stores
const arcCandidatesStore = new Map<string, ArcCandidate[]>();
const arcSelectionsStore = new Map<string, ArcSelection[]>();
const arcStageMapsStore = new Map<string, ArcStageMap[]>();

// Initialize with sample data
arcCandidatesStore.set('project-1', [
  {
    arc_id: 'arc-001',
    project_id: 'project-1',
    name: 'The Awakening Arc',
    summary: 'Elena discovers her powers and learns to control them.',
    stage_map_notes: [
      'Inciting incident: The manuscript appears',
      'First threshold: She writes her first conscious manifestation',
      'Midpoint: Marcus reveals his own history',
    ],
    fit_notes: ['Fits the protagonist\'s journey well'],
    tags: ['protagonist', 'primary', 'transformation'],
  },
  {
    arc_id: 'arc-002',
    project_id: 'project-1',
    name: 'The Mentor\'s Redemption',
    summary: 'Marcus finds purpose again through mentoring Elena.',
    stage_map_notes: [
      'Introduction: Cynical but knowledgeable',
      'Turning point: Sees potential in Elena',
      'Climax: Sacrifices his own recognition for her success',
    ],
    fit_notes: ['Provides emotional counterweight to Elena\'s arc'],
    tags: ['mentor', 'secondary', 'redemption'],
  },
]);

arcSelectionsStore.set('project-1', [
  {
    selection_id: 'sel-001',
    project_id: 'project-1',
    selected_arc_id: 'arc-001',
    character_id: 'char-001',
    rationale: 'Primary character arc for Elena, driving the main narrative.',
    alternatives_considered: ['arc-003'],
  },
]);

arcStageMapsStore.set('project-1', [
  {
    map_id: 'map-001',
    project_id: 'project-1',
    arc_id: 'arc-001',
    stages: [
      {
        stage_name: 'Ordinary World',
        beat_notes: ['Elena struggles with writer\'s block', 'Feels inadequate compared to published authors'],
        emotional_state: 'Frustrated, doubtful',
        key_decisions: ['To retreat to the cabin for solitude'],
      },
      {
        stage_name: 'Call to Adventure',
        beat_notes: ['The manuscript appears', 'She discovers it writes itself'],
        emotional_state: 'Confused, curious',
        key_decisions: ['To investigate the manuscript'],
      },
      {
        stage_name: 'Refusal of the Call',
        beat_notes: ['Tries to ignore the manuscript', 'Burns it, but it reappears'],
        emotional_state: 'Fearful, resistant',
        key_decisions: ['To confront the phenomenon'],
      },
    ],
  },
]);

export async function getArcCandidates(projectId: string): Promise<ArcCandidate[]> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));
  return arcCandidatesStore.get(projectId) || [];
}

export async function getArcSelections(projectId: string): Promise<ArcSelection[]> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));
  return arcSelectionsStore.get(projectId) || [];
}

export async function getArcStageMaps(projectId: string): Promise<ArcStageMap[]> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));
  return arcStageMapsStore.get(projectId) || [];
}

// Write operations
export async function createArcCandidate(
  projectId: string,
  candidate: Omit<ArcCandidate, 'arc_id' | 'project_id'>,
): Promise<ArcCandidate> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const arcCandidate: ArcCandidate = {
    arc_id: crypto.randomUUID(),
    project_id: projectId,
    ...candidate,
  };

  const candidates = arcCandidatesStore.get(projectId) || [];
  candidates.push(arcCandidate);
  arcCandidatesStore.set(projectId, candidates);

  return arcCandidate;
}

export async function selectArc(
  projectId: string,
  selection: Omit<ArcSelection, 'selection_id' | 'project_id'>,
): Promise<ArcSelection> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const arcSelection: ArcSelection = {
    selection_id: crypto.randomUUID(),
    project_id: projectId,
    ...selection,
  };

  const selections = arcSelectionsStore.get(projectId) || [];
  selections.push(arcSelection);
  arcSelectionsStore.set(projectId, selections);

  return arcSelection;
}

export async function createArcStageMap(
  projectId: string,
  stageMap: Omit<ArcStageMap, 'map_id' | 'project_id'>,
): Promise<ArcStageMap> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const arcStageMap: ArcStageMap = {
    map_id: crypto.randomUUID(),
    project_id: projectId,
    ...stageMap,
  };

  const maps = arcStageMapsStore.get(projectId) || [];
  maps.push(arcStageMap);
  arcStageMapsStore.set(projectId, maps);

  return arcStageMap;
}

export async function updateArcStageMap(
  mapId: string,
  projectId: string,
  updates: Partial<ArcStageMap>,
): Promise<ArcStageMap> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const maps = arcStageMapsStore.get(projectId);
  if (!maps) {
    throw new Error(`Arc stage map ${mapId} not found`);
  }

  const index = maps.findIndex((m) => m.map_id === mapId);
  if (index === -1) {
    throw new Error(`Arc stage map ${mapId} not found`);
  }

  const updated = { ...maps[index], ...updates };
  maps[index] = updated;
  arcStageMapsStore.set(projectId, maps);

  return updated;
}
