export interface ToneProfile {
  primary_tone: string;
  secondary_tones: string[];
}

export interface StoryStructure {
  structure_type: 'three_act' | 'hero_journey' | 'fichtean_curve' | 'seven_point';
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
  genre: string;
  tone_profile: ToneProfile;
  story_structure: StoryStructure;
}
