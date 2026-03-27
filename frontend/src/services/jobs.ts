import type { JobCreateRequest, JobStatusResponse, JobRetryRequest } from '../types/job';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const jobsService = {
  async createJob(request: JobCreateRequest): Promise<JobStatusResponse> {
    const response = await fetch(`${API_BASE}/v1/jobs/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      if (response.status === 400) {
        const error = await response.json();
        throw new Error(error.detail || 'Invalid request');
      }
      if (response.status === 409) {
        throw new Error('Idempotency conflict - job may already exist');
      }
      if (response.status === 500) {
        throw new Error('Server error occurred');
      }
      throw new Error(`Failed to create job: ${response.statusText}`);
    }

    return response.json();
  },

  async getStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await fetch(`${API_BASE}/v1/jobs/${jobId}/status`);
    
    if (!response.ok) {
      throw new Error(`Failed to get job status: ${response.statusText}`);
    }

    return response.json();
  },

  async retryJob(jobId: string, request: JobRetryRequest): Promise<JobStatusResponse> {
    const response = await fetch(`${API_BASE}/v1/jobs/${jobId}/retry`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to retry job: ${response.statusText}`);
    }

    return response.json();
  },

  async getLogs(jobId: string): Promise<{ id: string; entries: Array<{ timestamp: string; level: 'INFO' | 'WARNING' | 'ERROR'; message: string }> }> {
    const response = await fetch(`${API_BASE}/v1/jobs/${jobId}/logs`);
    
    if (!response.ok) {
      throw new Error(`Failed to get job logs: ${response.statusText}`);
    }

    return response.json();
  },
};
