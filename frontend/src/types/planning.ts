/**
 * Planning Types
 * 
 * Types for sequence plans, chapter plans, scene plans, dependencies, and chapter packets.
 */

export interface BeatPlan {
  beat_id: string;
  project_id: string;
  objective: string;
  conflict: string;
  stakes: string;
  dependency_ids: string[];
  arc_stage: string;
  active_character_ids: string[];
  continuity_requirements: string[];
  unresolved_questions: string[];
  status: string;
}

export interface BeatPlanCreateRequest {
  project_id: string;
  beat_id: string;
  objective: string;
  conflict: string;
  stakes: string;
  arc_stage?: string;
  active_character_ids?: string[];
  continuity_requirements?: string[];
  unresolved_questions?: string[];
  status?: string;
  position?: number;
}

export interface BeatPlanUpdateRequest {
  objective?: string;
  conflict?: string;
  stakes?: string;
  arc_stage?: string;
  active_character_ids?: string[];
  continuity_requirements?: string[];
  unresolved_questions?: string[];
  status?: string;
  position?: number;
}

export interface SequencePlan {
  sequence_id: string;
  project_id: string;
  title: string;
  summary: string;
  beat_ids: string[];
  chapter_ids: string[];
  status: string;
}

export interface ChapterPlan {
  chapter_id: string;
  project_id: string;
  title: string;
  summary: string;
  sequence_id: string | null;
  objective: string;
  conflict: string;
  stakes: string;
  active_character_ids: string[];
  continuity_requirements: string[];
  unresolved_questions: string[];
  status: string;
}

export interface ScenePlan {
  scene_id: string;
  project_id: string;
  title: string;
  summary: string;
  chapter_id: string | null;
  objective: string;
  conflict: string;
  stakes: string;
  active_character_ids: string[];
  continuity_requirements: string[];
  unresolved_questions: string[];
  status: string;
}

export interface ChapterPacket {
  packet_id: string;
  project_id: string;
  chapter_id: string;
  included_reference_ids: string[];
  constraints: string[];
  scene_goals: string[];
  status: string;
}

export interface PlanningDependency {
  dependency_id: string;
  project_id: string;
  upstream_id: string;
  downstream_id: string;
  dependency_kind: string;
  reason: string | null;
}

// Response wrappers
interface PlanningListResponse<T> {
  project_id: string;
  items: T[];
  meta: Record<string, string>;
}

export type SequencePlanListResponse = PlanningListResponse<SequencePlan>;
export type ChapterPlanListResponse = PlanningListResponse<ChapterPlan>;
export type ScenePlanListResponse = PlanningListResponse<ScenePlan>;
export type BeatPlanListResponse = PlanningListResponse<BeatPlan>;
export type ChapterPacketListResponse = PlanningListResponse<ChapterPacket>;
export type PlanningDependencyListResponse = PlanningListResponse<PlanningDependency>;

// Storyboard Card types

export interface StoryboardCard {
  card_id: string;
  project_id: string;
  title: string;
  content: string;
  card_type: string;
  column_id: string | null;
  position: number;
  tags: string[];
  character_ids: string[];
  dependencies: string[];
  metadata: Record<string, unknown>;
}

// Create/Update request types

export interface SequencePlanCreateRequest {
  project_id: string;
  sequence_id: string;
  title: string;
  summary?: string;
  beat_ids?: string[];
  chapter_ids?: string[];
  status?: string;
  position?: number;
}

export interface SequencePlanUpdateRequest {
  title?: string;
  summary?: string;
  beat_ids?: string[];
  chapter_ids?: string[];
  status?: string;
  position?: number;
}

export interface ChapterPacketCreateRequest {
  project_id: string;
  packet_id: string;
  chapter_id: string;
  included_reference_ids?: string[];
  constraints?: string[];
  scene_goals?: string[];
  status?: string;
}

export interface ChapterPacketUpdateRequest {
  included_reference_ids?: string[];
  constraints?: string[];
  scene_goals?: string[];
  status?: string;
}

export interface ChapterPlanCreateRequest {
  project_id: string;
  chapter_id: string;
  title: string;
  summary?: string;
  objective: string;
  conflict: string;
  stakes: string;
  sequence_id?: string;
  active_character_ids?: string[];
  continuity_requirements?: string[];
  unresolved_questions?: string[];
  status?: string;
  position?: number;
}

export interface ChapterPlanUpdateRequest {
  title?: string;
  summary?: string;
  objective?: string;
  conflict?: string;
  stakes?: string;
  active_character_ids?: string[];
  continuity_requirements?: string[];
  unresolved_questions?: string[];
  status?: string;
  position?: number;
}

export interface ScenePlanCreateRequest {
  project_id: string;
  scene_id: string;
  title: string;
  summary?: string;
  objective: string;
  conflict: string;
  stakes: string;
  chapter_id?: string;
  active_character_ids?: string[];
  continuity_requirements?: string[];
  unresolved_questions?: string[];
  status?: string;
  position?: number;
}

export interface ScenePlanUpdateRequest {
  title?: string;
  summary?: string;
  objective?: string;
  conflict?: string;
  stakes?: string;
  active_character_ids?: string[];
  continuity_requirements?: string[];
  unresolved_questions?: string[];
  status?: string;
  position?: number;
}

export interface StoryboardCardCreateRequest {
  project_id: string;
  card_id: string;
  title: string;
  content: string;
  card_type?: string;
  column_id?: string | null;
  position?: number;
  tags?: string[];
  character_ids?: string[];
  dependencies?: string[];
  metadata?: Record<string, unknown>;
}

export interface StoryboardCardUpdateRequest {
  title?: string;
  content?: string;
  card_type?: string;
  column_id?: string | null;
  position?: number;
  tags?: string[];
  character_ids?: string[];
  dependencies?: string[];
  metadata?: Record<string, unknown>;
}

export interface StoryboardCardReindexRequest {
  card_ids: string[];
}
