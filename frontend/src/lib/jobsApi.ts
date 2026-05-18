import api from './api';
import { idempotencyKey } from './idempotencyKey';

export interface JobCreateRequest {
  project_id: string;
  phase: 'P-100' | 'P-200' | 'P-300' | 'P-400';
  payload?: Record<string, unknown>;
}

export type JobPhase = 'P-100' | 'P-200' | 'P-300' | 'P-400';

export interface JobSummary {
  job_id: string;
  project_id?: string;
  phase: JobPhase;
  status: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  attempt_number?: number;
  current_phase?: string;
  current_step?: string;
  detail?: string;
  progress_current?: number;
  progress_total?: number;
  heartbeat_at?: string;
  error?: string;
}

export type JobDetail = JobSummary;

export interface JobLogEntry {
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR';
  message: string;
}

export interface JobLogsResponse {
  job_id: string;
  entries: JobLogEntry[];
}

export const jobsApi = {
  list: async (projectId: string): Promise<JobSummary[]> => {
    const response = await api.get('/v1/jobs', { params: { project_id: projectId, limit: 20 } });
    return (response.data as Array<{
      id: string;
      phase: JobPhase;
      status: string;
      attempt_number?: number;
      created_at: string;
      updated_at: string;
      current_phase?: string;
      current_step?: string;
      detail?: string;
      progress_current?: number;
      progress_total?: number;
      heartbeat_at?: string;
      error?: string;
    }>).map((j) => ({
      job_id: j.id,
      phase: j.phase,
      status: j.status,
      created_at: j.created_at,
      updated_at: j.updated_at,
      attempt_number: j.attempt_number,
      current_phase: j.current_phase,
      current_step: j.current_step,
      detail: j.detail,
      progress_current: j.progress_current,
      progress_total: j.progress_total,
      heartbeat_at: j.heartbeat_at,
      error: j.error,
    }));
  },

  create: async (request: JobCreateRequest): Promise<JobDetail> => {
    const idemKey = idempotencyKey(`job:${request.phase}:${request.project_id}`);
    const response = await api.post('/v1/jobs/create', {
      phase: request.phase,
      payload: {
        project_id: request.project_id,
        ...(request.payload ?? {}),
      },
    }, {
      headers: { 'Idempotency-Key': idemKey },
    });

    const data = response.data as {
      id: string;
      phase: JobPhase;
      status: string;
      attempt_number?: number;
      created_at: string;
      updated_at: string;
      current_phase?: string;
      current_step?: string;
      detail?: string;
      progress_current?: number;
      progress_total?: number;
      error?: string;
    };

    return {
      job_id: data.id,
      project_id: request.project_id,
      phase: data.phase,
      status: data.status,
      created_at: data.created_at,
      updated_at: data.updated_at,
      attempt_number: data.attempt_number,
      current_phase: data.current_phase,
      current_step: data.current_step,
      detail: data.detail,
      progress_current: data.progress_current,
      progress_total: data.progress_total,
      heartbeat_at: undefined,
      error: data.error,
    };
  },

  get: async (jobId: string): Promise<JobDetail> => {
    const response = await api.get(`/v1/jobs/${jobId}/status`);
    const data = response.data as {
      id: string;
      phase: JobPhase;
      status: string;
      attempt_number?: number;
      created_at: string;
      updated_at: string;
      current_phase?: string;
      current_step?: string;
      detail?: string;
      progress_current?: number;
      progress_total?: number;
      heartbeat_at?: string;
      error?: string;
    };

    return {
      job_id: data.id,
      phase: data.phase,
      status: data.status,
      created_at: data.created_at,
      updated_at: data.updated_at,
      attempt_number: data.attempt_number,
      current_phase: data.current_phase,
      current_step: data.current_step,
      detail: data.detail,
      progress_current: data.progress_current,
      progress_total: data.progress_total,
      heartbeat_at: data.heartbeat_at,
      error: data.error,
    };
  },

  getLogs: async (jobId: string): Promise<JobLogsResponse> => {
    const response = await api.get(`/v1/jobs/${jobId}/logs`);
    const data = response.data as {
      id: string;
      entries: JobLogEntry[];
    };

    return {
      job_id: data.id,
      entries: data.entries,
    };
  },
};
