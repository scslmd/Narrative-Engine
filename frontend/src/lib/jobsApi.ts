import api from './api';

export interface JobCreateRequest {
  project_id: string;
  phase: 'P-100' | 'P-200' | 'P-300' | 'P-400';
  payload?: Record<string, unknown>;
}

export type JobPhase = 'P-100' | 'P-200' | 'P-300' | 'P-400';

export type JobStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface JobSummary {
  job_id: string;
  project_id: string;
  phase: JobPhase;
  status: JobStatus;
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
    const response = await api.get(`/v1/jobs?project_id=${projectId}`);
    return response.data;
  },

  create: async (request: JobCreateRequest): Promise<JobDetail> => {
    const response = await api.post('/v1/jobs/create', request);
    return response.data;
  },

  get: async (jobId: string): Promise<JobDetail> => {
    const response = await api.get(`/v1/jobs/${jobId}/status`);
    return response.data;
  },

  getLogs: async (jobId: string): Promise<JobLogsResponse> => {
    const response = await api.get(`/v1/jobs/${jobId}/logs`);
    return response.data;
  },
};
