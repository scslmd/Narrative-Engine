export interface ToneProfile {
  primary_tone: string;
  secondary_tones: string[];
}

export type StoryStructureType =
  | 'THREE_ACT'
  | 'SAVE_THE_CAT'
  | 'HERO_JOURNEY'
  | 'FREYTAGS_PYRAMID'
  | 'KISHOTENKETSU'
  | 'FICHTEAN_CURVE'
  | 'SEVEN_POINT_STRUCTURE'
  | 'SEVEN_KEY_STEPS'
  | 'SNOWFLAKE_METHOD'
  | 'BRAINDUMP'
  | 'OTHER';

export interface StoryStructure {
  structure_type: StoryStructureType;
  act_breakdown?: string[];
}

export interface ProjectSummaryResponse {
  project_id: string;
  project_name: string;
  genre: string;
  tone_profile: ToneProfile;
  story_structure: StoryStructure;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetailResponse extends ProjectSummaryResponse {
  manifest_path: string;
  project_dir: string;
  database_exists: boolean;
  sequence_exists: boolean;
  chapter_exists: boolean;
}

export interface ProjectCreateRequest {
  project_name: string;
  project_kind?: string;
  genre?: string;
  tone_profile?: string;
  story_structure?: string;
  story_structure_obj?: StoryStructure;
}
