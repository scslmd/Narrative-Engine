import type { JobCreateRequest, JobStatusResponse, JobRetryRequest } from '../types/job';
import api from '../lib/api';

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

export const jobsService = {
  async createJob(request: JobCreateRequest): Promise<JobStatusResponse> {
    try {
      const response = await api.post('/jobs/create', request);
      
      if (response.status !== 202 && response.status !== 200) {
        throw new Error(`Failed to create job: ${response.status}`);
      }

      return response.data;
    } catch (error: unknown) {
      const axiosError = error as { response?: { status: number; data?: { detail?: string } } };
      
      if (axiosError?.response?.status === 400) {
        throw new Error(axiosError.response.data?.detail || 'Invalid request');
      }
      if (axiosError?.response?.status === 409) {
        throw new Error('Idempotency conflict - job may already exist');
      }
      if (axiosError?.response?.status === 500) {
        throw new Error('Server error occurred');
      }
      throw error;
    }
  },

  async getStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await api.get(`/jobs/${jobId}/status`);
    
    if (response.status !== 200) {
      throw new Error(`Failed to get job status: ${response.status}`);
    }

    return response.data;
  },

  async retryJob(jobId: string, request: JobRetryRequest): Promise<JobStatusResponse> {
    const response = await api.post(`/jobs/${jobId}/retry`, request);

    if (response.status !== 202) {
      throw new Error(`Failed to retry job: ${response.status}`);
    }

    return response.data;
  },

  async getLogs(jobId: string): Promise<{ id: string; entries: Array<{ timestamp: string; level: 'INFO' | 'WARNING' | 'ERROR'; message: string }> }> {
    const response = await api.get(`/jobs/${jobId}/logs`);
    
    if (response.status !== 200) {
      throw new Error(`Failed to get job logs: ${response.status}`);
    }

    return response.data;
  },

  async getAttempts(jobId: string): Promise<JobAttemptHistoryResponse> {
    const response = await api.get(`/jobs/${jobId}/attempts`);
    
    if (response.status !== 200) {
      throw new Error(`Failed to get job attempts: ${response.status}`);
    }

    return response.data;
  },
};
