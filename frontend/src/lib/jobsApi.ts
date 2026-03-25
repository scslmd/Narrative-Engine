import api from './api';

export interface JobCreateRequest {
  project_id: string;
  phase: 'P-100' | 'P-200' | 'P-300' | 'P-400';
}

export interface JobSummary {
  job_id: string;
  project_id: string;
  phase: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface JobDetail extends JobSummary {
  logs_url?: string;
  error_message?: string;
  artifacts?: string[];
}

export const jobsApi = {
  list: async (projectId: string): Promise<JobSummary[]> => {
    const response = await api.get(`/jobs?project_id=${projectId}`);
    return response.data;
  },

  create: async (request: JobCreateRequest): Promise<JobDetail> => {
    const response = await api.post('/jobs', request);
    return response.data;
  },

  get: async (jobId: string): Promise<JobDetail> => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },

  getLogs: async (jobId: string): Promise<string> => {
    const response = await api.get(`/jobs/${jobId}/logs`);
    return response.data;
  },
};
