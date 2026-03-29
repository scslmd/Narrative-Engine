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
  runKind: 'pipeline_job' | 'role_model_check';
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

export interface AttemptHistoryItem {
  attempt_number: number;
  status: string;
  executor_name: string | null;
  executor_instance_id: string | null;
  queue_delay_ms: number | null;
  lease_owner: string | null;
  lease_expires_at: string | null;
  claimed_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  last_heartbeat_at: string | null;
  finish_reason: string | null;
  failure_stage: string | null;
  retryable: boolean | null;
  retry_reason: string | null;
  error_code: string | null;
  error_category: string | null;
}

export interface JobAttemptHistoryResponse {
  job_id: string;
  items: AttemptHistoryItem[];
  meta: Record<string, string>;
}

export interface RoleModelCheckAttemptHistoryResponse {
  run_id: string;
  items: AttemptHistoryItem[];
  meta: Record<string, string>;
}
