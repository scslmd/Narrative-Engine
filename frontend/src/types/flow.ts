export type StageKind = 'brainstorm' | 'foundation' | 'character' | 'world_bible' | 'arc_selection' | 'planning' | 'drafting' | 'review';

export type StageConfigurationState = 'ENABLED' | 'DISABLED' | 'OPTIONAL' | 'ARCHIVED';

export interface StoryFlowStage {
  stage_id: string;
  project_id: string;
  position: number;
  display_name: string;
  stage_kind: StageKind;
  description?: string;
  custom_prompt_guidance?: string;
  depends_on?: string[];
  stage_configuration_state: StageConfigurationState;
  stage_progress_state?: string;
  writer_notes?: string;
}

export interface FlowEditorState {
  stages: StoryFlowStage[];
  isUpdating: boolean;
  error: string | null;
}
