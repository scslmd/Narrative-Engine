/**
 * Foundation Types
 * 
 * Types for foundation profile, revisions, and review cues.
 * Backend schema: app.schemas.story_development.FoundationProfile
 */

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

export interface FoundationReviewCue {
  impacted_area: string;
  reason: string;
  triggering_revision_id: string;
  triggering_fields: string[];
}

export interface FoundationCreateRequest {
  project_id: string;
  premise: string;
  logline: string;
  thematic_spine: string;
  emotional_promise: string;
  tone_and_voice_direction: string;
  target_audience: string;
  narrative_constraints?: string[];
  complexity_level: string;
  success_definition: string;
}

export interface FoundationUpdateRequest {
  premise?: string;
  logline?: string;
  thematic_spine?: string;
  emotional_promise?: string;
  tone_and_voice_direction?: string;
  target_audience?: string;
  narrative_constraints?: string[];
  complexity_level?: string;
  success_definition?: string;
}

// Response wrappers
export interface FoundationReadResponse {
  project_id: string;
  foundation_id: string;
  active_profile: FoundationProfile | null;
  current_revision_id: string | null;
  revision_history: FoundationRevision[];
  downstream_review_cues: FoundationReviewCue[];
}

export interface FoundationWriteResponse extends FoundationReadResponse {
  created_revision: FoundationRevision;
}

export interface FoundationRevisionListResponse {
  project_id: string;
  items: FoundationRevision[];
  meta: Record<string, string>;
}

export interface FoundationReviewCueListResponse {
  project_id: string;
  items: FoundationReviewCue[];
  meta: Record<string, string>;
}
