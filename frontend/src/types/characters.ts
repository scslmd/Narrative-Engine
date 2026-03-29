/**
 * Character Types
 * 
 * Types for character profiles and relationships.
 * Backend schema: app.schemas.story_development.CharacterProfile
 */

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

export interface CharacterProfileCreateRequest {
  project_id: string;
  character_id: string;
  display_name: string;
  role_in_story: string;
  archetype: string;
  external_goal: string;
  internal_need: string;
  misbelief_or_wound: string;
  core_fear: string;
  primary_strength: string;
  fatal_flaw_or_limitation: string;
  contradictions?: string[];
  backstory_summary: string;
  voice_notes: string;
  secrets?: string[];
  values?: string[];
  taboos?: string[];
  change_axis: string;
  arc_stage_notes?: string[];
  continuity_facts?: string[];
  writer_notes?: string | null;
}

export interface CharacterProfileUpdateRequest {
  display_name?: string;
  role_in_story?: string;
  archetype?: string;
  external_goal?: string;
  internal_need?: string;
  misbelief_or_wound?: string;
  core_fear?: string;
  primary_strength?: string;
  fatal_flaw_or_limitation?: string;
  contradictions?: string[];
  backstory_summary?: string;
  voice_notes?: string;
  secrets?: string[];
  values?: string[];
  taboos?: string[];
  change_axis?: string;
  arc_stage_notes?: string[];
  continuity_facts?: string[];
  writer_notes?: string | null;
}

export interface RelationshipEdgeCreateRequest {
  edge_id?: string;
  project_id: string;
  source_character_id: string;
  target_character_id: string;
  relation_kind: string;
  summary: string;
  tension?: string | null;
  notes?: string | null;
}

// Response wrappers
export interface CharacterProfileListResponse {
  project_id: string;
  items: CharacterProfile[];
  meta: Record<string, string>;
}

export interface RelationshipEdgeListResponse {
  project_id: string;
  items: RelationshipEdge[];
  meta: Record<string, string>;
}
