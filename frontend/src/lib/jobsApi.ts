import api from './api';

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
  started_at?: string;
  completed_at?: string;
}

export interface JobDetail extends JobSummary {
  attempt_number?: number;
  current_phase?: string;
  current_step?: string;
  detail?: string;
  progress_current?: number;
  progress_total?: number;
  error?: string;
}

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
    // The backend does not expose a job-list projection yet.
    // Return an empty collection rather than calling a missing endpoint.
    void projectId;
    return [];
  },

  create: async (request: JobCreateRequest): Promise<JobDetail> => {
    const response = await api.post('/jobs/create', {
      phase: request.phase,
      payload: {
        project_id: request.project_id,
        ...(request.payload ?? {}),
      },
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
      started_at: undefined,
      completed_at: undefined,
      attempt_number: data.attempt_number,
      current_phase: data.current_phase,
      current_step: data.current_step,
      detail: data.detail,
      progress_current: data.progress_current,
      progress_total: data.progress_total,
      error: data.error,
    };
  },

  get: async (jobId: string): Promise<JobDetail> => {
    const response = await api.get(`/jobs/${jobId}/status`);
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
      phase: data.phase,
      status: data.status,
      created_at: data.created_at,
      attempt_number: data.attempt_number,
      current_phase: data.current_phase,
      current_step: data.current_step,
      detail: data.detail,
      progress_current: data.progress_current,
      progress_total: data.progress_total,
      error: data.error,
    };
  },

  getLogs: async (jobId: string): Promise<JobLogsResponse> => {
    const response = await api.get(`/jobs/${jobId}/logs`);
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
