import type { ManuscriptDocument } from './drafting';

export interface TextRange {
  start_offset: number;
  end_offset: number;
  selected_text: string;
  anchor_before: string;
  anchor_after: string;
}

export type ManuscriptAssistKind =
  | 'developmental_review'
  | 'canon_check'
  | 'character_voice_check'
  | 'pacing_review'
  | 'theme_review'
  | 'line_edit_selection'
  | 'expand_selection'
  | 'compress_selection'
  | 'rewrite_selection_same_voice'
  | 'alternate_selection'
  | 'continue_from_selection'
  | 'fork_from_selection'
  | 'generate_next_chapter'
  | 'generate_alternate_chapter'
  | 'continuity_repair';

export interface ManuscriptAssistRequest {
  assist_id?: string | null;
  project_id: string;
  document_id: string;
  assist_kind: ManuscriptAssistKind;
  instruction: string;
  text_range?: TextRange | null;
  canon_scope?: Record<string, unknown> | null;
  canon_policy?: Record<string, unknown> | null;
  target_branch_id?: string | null;
  create_branch?: boolean;
  create_draft_artifact?: boolean;
  model_id?: string | null;
  temperature?: number | null;
  max_tokens?: number | null;
  idempotency_key?: string | null;
}

export interface AssistGateResult {
  gate_result_id: string;
  assist_id: string;
  project_id: string;
  document_id: string;
  gate_name: string;
  passed: boolean;
  severity: string;
  reasons: string[];
  created_at: string;
}

export interface LLMRevisionSuggestion {
  suggestion_id: string;
  assist_id: string;
  project_id: string;
  target_document_id: string;
  source_text: string;
  proposed_text: string;
  rationale: string;
  suggestion_kind: ManuscriptAssistKind;
  range?: TextRange | null;
  canon_risk: 'none' | 'low' | 'medium' | 'high' | 'blocking';
  confidence_score: number;
  status: 'REQUESTED' | 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'ARCHIVED';
  source_context: string[];
}

export interface ManuscriptAssistResult {
  assist_id: string;
  project_id: string;
  document_id: string;
  assist_kind: ManuscriptAssistKind;
  status: 'queued' | 'running' | 'completed' | 'blocked' | 'failed';
  summary: string;
  suggestions: LLMRevisionSuggestion[];
  created_draft_artifact_id?: string | null;
  created_branch_id?: string | null;
  created_manuscript_document_id?: string | null;
  gate_results: AssistGateResult[];
  job_ids: string[];
  warnings: string[];
}

export interface ApplyAssistSuggestionRequest {
  project_id: string;
  document_id: string;
  suggestion_id: string;
  expected_document_version: number;
  apply_mode: 'replace_range' | 'append_after_range' | 'create_draft' | 'create_branch';
}

export interface ApplyAssistSuggestionResponse {
  suggestion: LLMRevisionSuggestion;
  manuscript: ManuscriptDocument;
}
