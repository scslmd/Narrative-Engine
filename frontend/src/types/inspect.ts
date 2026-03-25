export type StepState = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface StepRecord {
  step_record_id: string;
  logical_run_id: string;
  run_id: string;
  run_kind: string;
  attempt_number: number;
  step_name: string;
  step_index: number;
  state: StepState;
  project_id: string;
  model_id?: string;
  backend_name?: string;
  started_at?: string;
  finished_at?: string;
  duration_seconds?: number;
  error_code?: string;
}

export interface InspectContext {
  jobId: string;
  attemptNumber?: number;
}

export type ArtifactState = 'CANONICAL' | 'SUPERSEDED' | 'REJECTED' | 'DRAFT';

export type ArtifactKind = 
  | 'PROJECT_BRIEF'
  | 'CHAPTER_PLAN'
  | 'SEQUENCE'
  | 'SCENE_STORYBOARD'
  | 'STORY_BIBLE'
  | 'MANUSCRIPT_DOCUMENT';

export interface ArtifactLineageView {
  artifact_id: string;
  artifact_kind: ArtifactKind;
  state: ArtifactState;
  run_id: string;
  step_name: string;
  created_at: string;
  provenance?: {
    provider?: string;
    model?: string;
    backend_name?: string;
  };
}
