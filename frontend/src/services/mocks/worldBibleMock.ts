export type WorldBibleEntryType = 'location' | 'organization' | 'artifact' | 'event' | 'concept' | 'creature' | 'magic_system' | 'technology' | 'culture' | 'history';

export interface WorldBibleEntry {
  entry_id: string;
  project_id: string;
  entry_type: WorldBibleEntryType;
  title: string;
  summary: string;
  canonical_facts: string[];
  related_character_ids: string[];
  source_artifacts: string[];
  visibility_scope: string;
  continuity_warnings: string[];
  writer_notes: string | null;
}

const MOCK_DELAY = 2000;

// Mock data store for world bible entries
const worldBibleStore = new Map<string, WorldBibleEntry[]>();

// Initialize with sample data
worldBibleStore.set('project-1', [
  {
    entry_id: 'wb-001',
    project_id: 'project-1',
    entry_type: 'location',
    title: 'The Writer\'s Retreat',
    summary: 'A secluded cabin in the Pacific Northwest where Elena discovers her powers.',
    canonical_facts: [
      'Built in 1920s as a writer\'s retreat',
      'Located three hours from Seattle',
      'Has a vintage Royal typewriter in the study',
    ],
    related_character_ids: ['char-001'],
    source_artifacts: [],
    visibility_scope: 'project',
    continuity_warnings: [],
    writer_notes: 'Make sure the atmosphere feels isolating but peaceful.',
  },
  {
    entry_id: 'wb-002',
    project_id: 'project-1',
    entry_type: 'artifact',
    title: 'The Manuscript',
    summary: 'A mysterious manuscript that appears in Elena\'s study, writing itself.',
    canonical_facts: [
      'Bound in dark leather with no title',
      'Pages are blank until Elena falls asleep',
      'Writing appears in her own handwriting',
    ],
    related_character_ids: ['char-001'],
    source_artifacts: [],
    visibility_scope: 'project',
    continuity_warnings: ['Ensure the manuscript\'s origins remain ambiguous'],
    writer_notes: null,
  },
  {
    entry_id: 'wb-003',
    project_id: 'project-1',
    entry_type: 'concept',
    title: 'Narrative Bleed',
    summary: 'The phenomenon where fictional elements manifest in reality.',
    canonical_facts: [
      'Only affects those with strong creative imagination',
      'Manifestations are subtle at first',
      'Can be controlled through conscious writing',
    ],
    related_character_ids: ['char-001', 'char-002'],
    source_artifacts: [],
    visibility_scope: 'project',
    continuity_warnings: ['Keep the rules consistent but mysterious'],
    writer_notes: 'This is the core magical system - treat it with care.',
  },
]);

export async function getWorldBible(projectId: string): Promise<WorldBibleEntry[]> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));
  return worldBibleStore.get(projectId) || [];
}

export async function getWorldBibleEntry(
  entryType: WorldBibleEntryType,
  title: string,
  projectId: string,
): Promise<WorldBibleEntry | null> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));
  const entries = worldBibleStore.get(projectId) || [];
  return entries.find((e) => e.entry_type === entryType && e.title === title) || null;
}

export async function createWorldBibleEntry(
  projectId: string,
  entry: Omit<WorldBibleEntry, 'entry_id' | 'project_id'>,
): Promise<WorldBibleEntry> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const newEntry: WorldBibleEntry = {
    entry_id: crypto.randomUUID(),
    project_id: projectId,
    ...entry,
  };

  const entries = worldBibleStore.get(projectId) || [];
  entries.push(newEntry);
  worldBibleStore.set(projectId, entries);

  return newEntry;
}

export async function updateWorldBibleEntry(
  entryType: WorldBibleEntryType,
  title: string,
  projectId: string,
  updates: Partial<WorldBibleEntry>,
): Promise<WorldBibleEntry> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const entries = worldBibleStore.get(projectId);
  if (!entries) {
    throw new Error(`World Bible entry not found`);
  }

  const index = entries.findIndex((e) => e.entry_type === entryType && e.title === title);
  if (index === -1) {
    throw new Error(`World Bible entry not found`);
  }

  const updated = { ...entries[index], ...updates };
  entries[index] = updated;
  worldBibleStore.set(projectId, entries);

  return updated;
}
