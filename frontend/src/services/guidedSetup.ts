import api from '../lib/api';

export interface ChatMessage {
  role: string;
  content: string;
  turn: number;
}

export interface GuidedConfig {
  project_name: string;
  genre: string;
  tone_profile: string;
  pov: string;
  story_structure: string;
  primary_language: string;
  secondary_language: string | null;
  constraints: string[];
}

export interface GuidedFoundation {
  premise_text: string;
  logline: string;
  thematic_spine: string;
  emotional_promise: string;
  target_audience: string;
  complexity_level: string;
  success_definition: string;
  narrative_constraints: string[];
}

export interface GuidedCharacter {
  name: string;
  role: string;
  archetype: string;
  age_range: string;
  external_goal: string;
  internal_need: string;
  core_fear: string;
  primary_strength: string;
  fatal_flaw: string;
  backstory_summary: string;
  voice_notes: string;
  contradictions: string[];
  secrets: string[];
  values: string[];
  taboos: string[];
  change_axis: string;
}

export interface GuidedWorldEntry {
  entry_type: string;
  title: string;
  summary: string;
  canonical_facts: string[];
}

export interface GuidedArc {
  character_name: string;
  arc_type: string;
  summary: string;
  stages: string[];
  tags: string[];
}

export interface ExtractedFields {
  config: GuidedConfig;
  foundation: GuidedFoundation;
  characters: GuidedCharacter[];
  world_bible: GuidedWorldEntry[];
  arcs: GuidedArc[];
}

export interface CategoryProgress {
  category: string;
  completeness: number;
  confidence: number;
  fields_collected: string[];
  fields_missing: string[];
}

export interface GuidedSetupAnalyzeRequest {
  conversation_history: ChatMessage[];
  current_answer: string;
  accumulated_fields: ExtractedFields;
}

export interface GuidedSetupAnalyzeResponse {
  extracted_fields: ExtractedFields;
  next_question: string;
  confidence: number;
  progress: number;
  ready_to_create: boolean;
  category_progress: CategoryProgress[];
}

export interface GuidedSetupCreateRequest {
  accumulated_fields: ExtractedFields;
}

export interface GuidedSetupCreateResponse {
  project_id: string;
  project_name: string;
  characters_created: number;
  world_entries_created: number;
  arcs_created: number;
  foundation_created: boolean;
  message: string;
}

export function emptyExtractedFields(): ExtractedFields {
  return {
    config: {
      project_name: '',
      genre: '',
      tone_profile: 'Neutral',
      pov: 'Third_Limited',
      story_structure: 'THREE_ACT',
      primary_language: 'English',
      secondary_language: null,
      constraints: [],
    },
    foundation: {
      premise_text: '',
      logline: '',
      thematic_spine: '',
      emotional_promise: '',
      target_audience: '',
      complexity_level: '',
      success_definition: '',
      narrative_constraints: [],
    },
    characters: [],
    world_bible: [],
    arcs: [],
  };
}

export async function analyzeTurn(
  request: GuidedSetupAnalyzeRequest,
): Promise<GuidedSetupAnalyzeResponse> {
  const response = await api.post('/projects/guided-setup/analyze', request);

  if (response.status !== 200) {
    throw new Error(`Failed to analyze turn: ${response.status}`);
  }

  return response.data;
}

export async function createFromFields(
  request: GuidedSetupCreateRequest,
): Promise<GuidedSetupCreateResponse> {
  const response = await api.post('/projects/guided-setup/create', request);

  if (response.status !== 201) {
    throw new Error(`Failed to create project: ${response.status}`);
  }

  return response.data;
}

export interface LlmHealthStatus {
  ok: boolean;
  backend: string;
  model?: string;
  error?: string;
}

export async function checkLlmHealth(): Promise<LlmHealthStatus> {
  try {
    const response = await api.get('/health/llm');
    if (response.status === 200) {
      return { ok: true, backend: response.data.backend, model: response.data.model };
    }
    return { ok: false, backend: response.data?.backend || 'unknown', error: 'Unexpected status' };
  } catch {
    return { ok: false, backend: 'unknown', error: 'LLM service unreachable' };
  }
}
