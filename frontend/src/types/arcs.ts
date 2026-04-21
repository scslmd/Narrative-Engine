/**
 * Arcs Types
 * 
 * Types for arc candidates, selections, comparisons, and stage mappings.
 */

export interface ArcCandidate {
  arc_id: string;
  project_id: string;
  name: string;
  summary: string;
  stage_map_notes: string[];
  fit_notes: string[];
  tags: string[];
}

export interface ArcComparisonCandidateRecord {
  candidate: ArcCandidate;
  rank: number;
  score: [number, number, number, number];
  notes: string[];
}

export interface ArcComparisonRecord {
  comparison_id: string;
  project_id: string;
  candidate_ids: string[];
  candidate_set: ArcCandidate[];
  ranked_candidates: ArcComparisonCandidateRecord[];
  review_notes: string[];
}

export interface ArcStageMap {
  arc_stage_map_id: string;
  project_id: string;
  arc_id: string;
  stage_kinds: string[];
  notes: string | null;
}

export interface ArcSelection {
  selection_id: string;
  project_id: string;
  selected_arc: ArcCandidate;
  rejected_arc_ids: string[];
  comparison_notes: string[];
  comparison_record_ids: string[];
  stage_map: ArcStageMap | null;
}

// Response wrappers
interface ArcsListResponse<T> {
  project_id: string;
  items: T[];
  meta: Record<string, string>;
}

export type ArcCandidateListResponse = ArcsListResponse<ArcCandidate>;
export type ArcSelectionListResponse = ArcsListResponse<ArcSelection>;
export type ArcStageMapListResponse = ArcsListResponse<ArcStageMap>;
export type ArcComparisonListResponse = ArcsListResponse<ArcComparisonRecord>;

// ============================================================================
// Request types for mutations
// ============================================================================

export interface ArcCandidateCreateRequest {
  arc_id: string;
  project_id: string;
  name: string;
  summary: string;
  stage_map_notes?: string[];
  fit_notes?: string[];
  tags?: string[];
}

export interface ArcComparisonCreateRequest {
  project_id: string;
  candidate_ids: string[];
  review_notes?: string[];
}

export interface ArcSelectionCreateRequest {
  project_id: string;
  selected_arc: string | {
    arc_id: string;
    name: string;
    summary: string;
    stage_map_notes: string[];
    fit_notes: string[];
    tags: string[];
  };
  rejected_arc_ids?: string[];
  comparison_notes?: string[];
  comparison_record_ids?: string[];
}

export interface ArcSelectionUpdateRequest {
  selected_arc?: {
    arc_id: string;
    name: string;
    summary: string;
    stage_map_notes: string[];
    fit_notes: string[];
    tags: string[];
  };
  rejected_arc_ids?: string[];
  comparison_notes?: string[];
  comparison_record_ids?: string[];
}

export interface ArcStageMapCreateRequest {
  project_id: string;
  arc_id: string;
  stage_kinds: string[];
  notes?: string | null;
}
