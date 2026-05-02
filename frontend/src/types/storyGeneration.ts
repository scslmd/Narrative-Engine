export type GenerationMode =
  | 'same_project_new_arc'
  | 'same_project_sequel'
  | 'same_project_prequel'
  | 'same_project_side_story'
  | 'same_project_alternate_route'
  | 'new_project_character_fork'
  | 'new_project_world_fork'
  | 'new_project_hybrid_fork';

export interface WorldBibleRef {
  entry_type: string;
  title: string;
}

export interface CanonScope {
  source_project_id: string;
  scope_mode?: string;
  character_ids: string[];
  world_bible_refs: WorldBibleRef[];
  continuity_thread_ids: string[];
  arc_ids: string[];
  mythos_ids: string[];
  pattern_ids: string[];
  include_relationships: boolean;
  include_unresolved_questions: boolean;
  include_contradictions_as_forbidden: boolean;
}

export interface GenerationDestination {
  destination_kind: 'same_project' | 'new_project';
  target_project_id?: string | null;
  target_project_name?: string | null;
  source_branch_id?: string | null;
  target_branch_id?: string | null;
}

export interface CanonPolicy {
  locked_character_fields: string[];
  locked_world_fields: string[];
  allowed_character_changes: string[];
  allowed_world_changes: string[];
  forbidden_contradictions: string[];
  continuity_strictness: 'warn' | 'block' | 'repair_once' | 'repair_twice';
}

export interface GenerationReviewPolicy {
  require_manual_approval: boolean;
  auto_promote_on_clean_gates: boolean;
  block_on_warnings: boolean;
}

export interface CanonGenerationRequest {
  request_id?: string | null;
  source_project_id: string;
  mode: GenerationMode;
  destination: GenerationDestination;
  canon_scope: CanonScope;
  generation_brief: string;
  premise_override?: string | null;
  tone_override?: string | null;
  pov_override?: string | null;
  target_chapter_count: number;
  target_words_per_chapter?: number | null;
  canon_policy?: CanonPolicy;
  review_policy?: GenerationReviewPolicy;
  model_id?: string | null;
  temperature?: number | null;
  max_tokens?: number | null;
  idempotency_key?: string | null;
}

export interface GenerationArtifactRef {
  artifact_kind: string;
  artifact_id: string;
  project_id: string;
}

export interface GenerationRunResponse {
  generation_id: string;
  source_project_id: string;
  target_project_id: string;
  job_ids: string[];
  status: 'queued' | 'running' | 'completed' | 'blocked' | 'failed';
  warnings: string[];
  created_artifacts: GenerationArtifactRef[];
}

export interface CanonGenerationPacket {
  packet_id: string;
  source_project_id: string;
  target_project_id: string;
  mode: GenerationMode;
  generation_brief: string;
  foundation_snapshot: Record<string, unknown>;
  characters: Array<Record<string, unknown>>;
  relationships: Array<Record<string, unknown>>;
  world_bible: Array<Record<string, unknown>>;
  arcs: Array<Record<string, unknown>>;
  continuity_threads: Array<Record<string, unknown>>;
  continuity_findings: Array<Record<string, unknown>>;
  drafting_context_packets: Array<Record<string, unknown>>;
  mythos_entries: Array<Record<string, unknown>>;
  pattern_entries: Array<Record<string, unknown>>;
  canon_annotations: Array<Record<string, unknown>>;
  customization_profile_id?: string | null;
  canon_policy: CanonPolicy;
  prompt_budget_summary: Record<string, unknown>;
  source_hashes: Record<string, string>;
}

export interface GenerationGateResult {
  gate_result_id: string;
  generation_id: string;
  project_id: string;
  artifact_kind: string;
  artifact_id: string;
  gate_name: string;
  passed: boolean;
  severity: string;
  reasons: string[];
  repair_attempted: boolean;
  repair_job_id?: string | null;
  created_at: string;
}

export interface CanonForkPreviewResponse {
  source_project_id: string;
  mode: GenerationMode;
  destination_kind: 'same_project' | 'new_project';
  selected_character_ids: string[];
  selected_world_bible_refs: WorldBibleRef[];
  selected_continuity_thread_ids: string[];
  selected_arc_ids: string[];
  warnings: string[];
}
