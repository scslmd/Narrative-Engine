import type { JobCreateRequest, JobStatusResponse, JobRetryRequest } from '../types/job';
import api from '../lib/api';

export const jobsService = {
  async createJob(request: JobCreateRequest): Promise<JobStatusResponse> {
    try {
      const response = await api.post('/jobs/create', request);
      
      if (response.status !== 201) {
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

    if (response.status !== 201) {
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
};
