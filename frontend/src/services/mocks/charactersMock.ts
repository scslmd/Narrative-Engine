export interface RelationshipEdge {
  edge_id: string;
  source_character_id: string;
  target_character_id: string;
  relation_kind: string;
  summary: string;
  tension: string | null;
  notes: string | null;
}

export interface CharacterProfile {
  character_id: string;
  project_id: string;
  display_name: string;
  role_in_story: string;
  archetype: string;
  external_goal: string;
  internal_need: string;
  misbelief_or_wound: string;
  core_fear: string;
  primary_strength: string;
  fatal_flaw_or_limitation: string;
  contradictions: string[];
  backstory_summary: string;
  voice_notes: string;
  relationship_edges: RelationshipEdge[];
  secrets: string[];
  values: string[];
  taboos: string[];
  change_axis: string;
  arc_stage_notes: string[];
  continuity_facts: string[];
  writer_notes: string | null;
}

const MOCK_DELAY = 2000;

// Mock data store for characters
const characterStore = new Map<string, CharacterProfile[]>();

// Initialize with sample data
characterStore.set('project-1', [
  {
    character_id: 'char-001',
    project_id: 'project-1',
    display_name: 'Elena Martinez',
    role_in_story: 'Protagonist',
    archetype: 'The Creator',
    external_goal: 'To write a bestselling novel that changes lives.',
    internal_need: 'To believe in her own worth beyond external validation.',
    misbelief_or_wound: 'That her voice doesn\'t matter unless others approve of it.',
    core_fear: 'Being forgotten or irrelevant.',
    primary_strength: 'Empathetic imagination that connects deeply with readers.',
    fatal_flaw_or_limitation: 'Paralyzing self-doubt that sabotages her momentum.',
    contradictions: [
      'Craves fame but fears being seen',
      'Wants authenticity but mimics successful authors',
    ],
    backstory_summary: 'A former teacher who quit to pursue writing full-time after a student\'s life was changed by her classroom stories.',
    voice_notes: 'Warm, introspective, with moments of sharp wit. She observes details others miss.',
    relationship_edges: [],
    secrets: ['She\'s been writing under a pen name for years'],
    values: ['Truth', 'Connection', 'Growth'],
    taboos: ['Betrayal of trust', 'Wasted potential'],
    change_axis: 'From seeking external validation to finding internal certainty.',
    arc_stage_notes: ['Denial of talent', 'Awakening', 'Struggle', 'Acceptance'],
    continuity_facts: ['Left-handed', 'Loves vintage typewriters', 'Has a scar on her left hand'],
    writer_notes: null,
  },
  {
    character_id: 'char-002',
    project_id: 'project-1',
    display_name: 'Marcus Chen',
    role_in_story: 'Mentor',
    archetype: 'The Sage',
    external_goal: 'To guide Elena toward her full potential as a writer.',
    internal_need: 'To pass on his wisdom before it\'s too late.',
    misbelief_or_wound: 'That his own career ended in failure.',
    core_fear: 'Being forgotten after death.',
    primary_strength: 'Deep understanding of story structure and human nature.',
    fatal_flaw_or_limitation: 'Cynicism that masks his lingering passion.',
    contradictions: [
      'Teaches hope while believing in despair',
      'Wants a successor but pushes students away',
    ],
    backstory_summary: 'A once-celebrated author who faded from prominence after a controversial novel.',
    voice_notes: 'Gruff but kind, speaks in metaphors and stories within stories.',
    relationship_edges: [
      {
        edge_id: 'edge-001',
        source_character_id: 'char-002',
        target_character_id: 'char-001',
        relation_kind: 'mentor',
        summary: 'Marcus sees his younger self in Elena and takes her under his wing.',
        tension: 'He fears she\'ll make the same mistakes he did.',
        notes: null,
      },
    ],
    secrets: ['He still writes every day, but never shows anyone'],
    values: ['Mentorship', 'Craft', 'Honesty'],
    taboos: ['Plagiarism', 'Selling out'],
    change_axis: 'From cynicism to renewed hope through Elena\'s success.',
    arc_stage_notes: ['Resistance', 'Reluctant engagement', 'Investment', 'Letting go'],
    continuity_facts: ['Smokes cigars', 'Collects first editions', 'Has a limp from an old injury'],
    writer_notes: 'Make sure his wisdom feels earned, not preachy.',
  },
]);

export async function getCharacters(projectId: string): Promise<CharacterProfile[]> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));
  return characterStore.get(projectId) || [];
}

export async function getCharacter(
  characterId: string,
  projectId: string,
): Promise<CharacterProfile | null> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));
  const characters = characterStore.get(projectId) || [];
  return characters.find((c) => c.character_id === characterId) || null;
}

export async function createCharacter(
  projectId: string,
  profile: Omit<CharacterProfile, 'character_id' | 'project_id'>,
): Promise<CharacterProfile> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const character: CharacterProfile = {
    character_id: crypto.randomUUID(),
    project_id: projectId,
    ...profile,
  };

  const characters = characterStore.get(projectId) || [];
  characters.push(character);
  characterStore.set(projectId, characters);

  return character;
}

export async function updateCharacter(
  characterId: string,
  projectId: string,
  updates: Partial<CharacterProfile>,
): Promise<CharacterProfile> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const characters = characterStore.get(projectId);
  if (!characters) {
    throw new Error(`Character ${characterId} not found`);
  }

  const index = characters.findIndex((c) => c.character_id === characterId);
  if (index === -1) {
    throw new Error(`Character ${characterId} not found`);
  }

  const updated = { ...characters[index], ...updates };
  characters[index] = updated;
  characterStore.set(projectId, characters);

  return updated;
}

export async function getCharacterRelationships(
  characterId: string,
  projectId: string,
): Promise<RelationshipEdge[]> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));

  const character = await getCharacter(characterId, projectId);
  if (!character) {
    return [];
  }

  return character.relationship_edges;
}

export async function createRelationship(
  projectId: string,
  edge: Omit<RelationshipEdge, 'edge_id'>,
): Promise<RelationshipEdge> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const relationship: RelationshipEdge = {
    edge_id: crypto.randomUUID(),
    ...edge,
  };

  // Add relationship to source character's relationship_edges
  const sourceCharacter = await getCharacter(edge.source_character_id, projectId);
  if (sourceCharacter) {
    sourceCharacter.relationship_edges.push(relationship);
    await updateCharacter(edge.source_character_id, projectId, {
      relationship_edges: sourceCharacter.relationship_edges,
    });
  }

  return relationship;
}
