export type StageKind = 'brainstorm' | 'foundation' | 'character' | 'world_bible' | 'arc_selection' | 'planning' | 'drafting' | 'review';

export type StageConfigurationState = 'ACTIVE' | 'DISABLED' | 'ARCHIVED';

export interface StoryFlowStage {
  stage_id: string;
  project_id: string;
  position: number;
  display_name: string;
  stage_kind: StageKind;
  description?: string;
  custom_prompt_guidance?: string;
  depends_on?: string[];  // Dependencies on other stages
  stage_configuration_state: StageConfigurationState;
  progress_percentage?: number;
}

export interface FlowEditorState {
  stages: StoryFlowStage[];
  isUpdating: boolean;
  error: string | null;
}
