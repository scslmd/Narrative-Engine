export interface FoundationProfile {
  foundation_id: string;
  project_id: string;
  premise: string;
  logline: string;
  thematic_spine: string;
  emotional_promise: string;
  tone_and_voice_direction: string;
  target_audience: string;
  narrative_constraints: string[];
  complexity_level: string;
  success_definition: string;
  version: number;
}

export interface FoundationRevision {
  revision_id: string;
  foundation_id: string;
  snapshot: FoundationProfile;
  change_summary: string | null;
}

const MOCK_DELAY = 2000;

// Mock data store for foundations
const foundationStore = new Map<string, FoundationProfile>();

// Initialize with sample data
foundationStore.set('project-1', {
  foundation_id: 'foundation-001',
  project_id: 'project-1',
  premise: 'A young writer discovers that the stories they write begin to manifest in reality.',
  logline: 'When a struggling author\'s fictional creations start bleeding into the real world, they must master their craft before their darkest characters destroy everything they love.',
  thematic_spine: 'The power of storytelling and the responsibility that comes with creative agency.',
  emotional_promise: 'A journey of self-discovery, creativity, and the courage to face the consequences of our creations.',
  tone_and_voice_direction: 'Lyrical yet grounded, blending magical realism with contemporary literary fiction.',
  target_audience: 'Adult readers who enjoy literary fiction with speculative elements.',
  narrative_constraints: [
    'Maintain first-person perspective throughout',
    'Keep magical elements subtle and ambiguous',
    'Ground supernatural events in emotional reality',
  ],
  complexity_level: 'moderate',
  success_definition: 'A story that balances wonder with emotional authenticity, leaving readers questioning the boundary between imagination and reality.',
  version: 1,
});

export async function getFoundation(projectId: string): Promise<FoundationProfile | null> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));
  return foundationStore.get(projectId) || null;
}

export async function createFoundation(
  projectId: string,
  profile: Omit<FoundationProfile, 'foundation_id' | 'project_id' | 'version'>,
): Promise<FoundationProfile> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const foundation: FoundationProfile = {
    foundation_id: crypto.randomUUID(),
    project_id: projectId,
    ...profile,
    version: 1,
  };

  foundationStore.set(projectId, foundation);
  return foundation;
}

export async function updateFoundation(
  projectId: string,
  updates: Partial<FoundationProfile>,
): Promise<FoundationProfile> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const existing = foundationStore.get(projectId);
  if (!existing) {
    throw new Error('Foundation not found');
  }

  const updated: FoundationProfile = {
    ...existing,
    ...updates,
    version: existing.version + 1,
  };

  foundationStore.set(projectId, updated);
  return updated;
}

export async function getFoundationRevisions(
  projectId: string,
): Promise<FoundationRevision[]> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));

  const foundation = foundationStore.get(projectId);
  if (!foundation) {
    return [];
  }

  return [
    {
      revision_id: crypto.randomUUID(),
      foundation_id: foundation.foundation_id,
      snapshot: foundation,
      change_summary: 'Initial foundation created',
    },
  ];
}
