export type JobPhase = 'P-100' | 'P-200' | 'P-300' | 'P-400';

export interface JobCreateRequest {
  phase: JobPhase;
  payload: Record<string, unknown>;
}

export interface JobStatusResponse {
  id: string;
  phase: JobPhase;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  attempt_number?: number;
  current_phase?: string;
  current_step?: string;
  progress_current?: number;
  progress_total?: number;
  error?: string;
}

export interface JobRetryRequest {
  retry_reason: string;
}
