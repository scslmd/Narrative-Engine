import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { jobsService } from './jobs';
import type { JobStatusResponse } from '../types/job';

const mockJobStatus: JobStatusResponse = {
  id: 'job-123',
  phase: 'P-100',
  status: 'COMPLETED',
  attempt_number: 1,
};

describe('jobsService', () => {
  describe('createJob', () => {
    it('creates a job with phase and payload (202)', async () => {
      server.use(
        http.post('/jobs/create', async ({ request }) => {
          const body = (await request.json()) as { phase?: string };
          return HttpResponse.json(
            { ...mockJobStatus, phase: body.phase },
            { status: 202 },
          );
        }),
      );

      const result = await jobsService.createJob({ phase: 'P-100', payload: { project_id: 'proj-1' } });

      expect(result.id).toBe('job-123');
      expect(result.phase).toBe('P-100');
    });

    it('creates a job and returns 200 response', async () => {
      server.use(
        http.post('/jobs/create', () => {
          return HttpResponse.json(mockJobStatus, { status: 200 });
        }),
      );

      const result = await jobsService.createJob({ phase: 'P-300', payload: {} });

      expect(result.id).toBe('job-123');
    });

    it('throws on 201 (service only accepts 200 or 202)', async () => {
      server.use(
        http.post('/jobs/create', () => {
          return HttpResponse.json(mockJobStatus, { status: 201 });
        }),
      );

      await expect(
        jobsService.createJob({ phase: 'P-100', payload: {} }),
      ).rejects.toThrow('Failed to create job: 201');
    });

    it('throws on 400 invalid request', async () => {
      server.use(
        http.post('/jobs/create', () => {
          return HttpResponse.json({ detail: 'Invalid phase' }, { status: 400 });
        }),
      );

      await expect(
        jobsService.createJob({ phase: 'P-100', payload: {} }),
      ).rejects.toThrow('Invalid phase');
    });

    it('throws on 409 idempotency conflict', async () => {
      server.use(
        http.post('/jobs/create', () => {
          return HttpResponse.json({ detail: 'Conflict' }, { status: 409 });
        }),
      );

      await expect(
        jobsService.createJob({ phase: 'P-100', payload: {} }),
      ).rejects.toThrow('Conflict');
    });

    it('throws on 500 server error', async () => {
      server.use(
        http.post('/jobs/create', () => {
          return HttpResponse.json({ detail: 'Internal error' }, { status: 500 });
        }),
      );

      await expect(
        jobsService.createJob({ phase: 'P-100', payload: {} }),
      ).rejects.toThrow('Server error occurred. Please try again later.');
    });
  });

  describe('getStatus', () => {
    it('returns job status by ID', async () => {
      server.use(
        http.get('/jobs/job-123/status', () => {
          return HttpResponse.json(mockJobStatus);
        }),
      );

      const result = await jobsService.getStatus('job-123');

      expect(result.id).toBe('job-123');
      expect(result.status).toBe('COMPLETED');
    });

    it('returns RUNNING status', async () => {
      server.use(
        http.get('/jobs/job-running/status', () => {
          return HttpResponse.json({ ...mockJobStatus, id: 'job-running', status: 'RUNNING' });
        }),
      );

      const result = await jobsService.getStatus('job-running');

      expect(result.status).toBe('RUNNING');
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.get('/jobs/job-missing/status', () => {
          return HttpResponse.json({ detail: 'Job not found' }, { status: 404 });
        }),
      );

      await expect(jobsService.getStatus('job-missing')).rejects.toThrow();
    });
  });

  describe('getLogs', () => {
    it('returns log entries for a job', async () => {
      const mockLogs = {
        id: 'job-123',
        entries: [
          { timestamp: '2026-01-01T00:00:00Z', level: 'INFO' as const, message: 'Job started' },
          { timestamp: '2026-01-01T00:00:01Z', level: 'INFO' as const, message: 'Phase P-100 complete' },
        ],
      };

      server.use(
        http.get('/jobs/job-123/logs', () => {
          return HttpResponse.json(mockLogs);
        }),
      );

      const result = await jobsService.getLogs('job-123');

      expect(result.id).toBe('job-123');
      expect(result.entries).toHaveLength(2);
      expect(result.entries[0].level).toBe('INFO');
    });

    it('returns empty log entries', async () => {
      server.use(
        http.get('/jobs/job-empty/logs', () => {
          return HttpResponse.json({ id: 'job-empty', entries: [] });
        }),
      );

      const result = await jobsService.getLogs('job-empty');

      expect(result.entries).toEqual([]);
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.get('/jobs/job-missing/logs', () => {
          return HttpResponse.json({ detail: 'Job not found' }, { status: 404 });
        }),
      );

      await expect(jobsService.getLogs('job-missing')).rejects.toThrow();
    });
  });

  describe('getAttempts', () => {
    it('returns attempt history for a job', async () => {
      const mockAttempts = {
        job_id: 'job-123',
        items: [
          {
            attempt_number: 1,
            status: 'COMPLETED',
            executor_name: 'local_executor',
            executor_instance_id: 'inst-1',
            queue_delay_ms: 100,
            lease_owner: 'worker-1',
            lease_expires_at: null,
            claimed_at: '2026-01-01T00:00:00Z',
            started_at: '2026-01-01T00:00:01Z',
            finished_at: '2026-01-01T00:01:00Z',
            last_heartbeat_at: '2026-01-01T00:00:59Z',
            finish_reason: 'success',
            failure_stage: null,
            retryable: false,
            retry_reason: null,
            error_code: null,
            error_category: null,
          },
        ],
        meta: { total_attempts: '1' },
      };

      server.use(
        http.get('/jobs/job-123/attempts', () => {
          return HttpResponse.json(mockAttempts);
        }),
      );

      const result = await jobsService.getAttempts('job-123');

      expect(result.job_id).toBe('job-123');
      expect(result.items).toHaveLength(1);
      expect(result.items[0].attempt_number).toBe(1);
      expect(result.items[0].status).toBe('COMPLETED');
    });

    it('returns multiple attempts with retries', async () => {
      const mockAttempts = {
        job_id: 'job-retries',
        items: [
          {
            attempt_number: 1,
            status: 'FAILED',
            executor_name: 'local_executor',
            executor_instance_id: 'inst-1',
            queue_delay_ms: 100,
            lease_owner: null,
            lease_expires_at: null,
            claimed_at: '2026-01-01T00:00:00Z',
            started_at: '2026-01-01T00:00:01Z',
            finished_at: '2026-01-01T00:00:30Z',
            last_heartbeat_at: null,
            finish_reason: 'error',
            failure_stage: 'inference',
            retryable: true,
            retry_reason: 'timeout',
            error_code: 'TIMEOUT',
            error_category: 'transient',
          },
          {
            attempt_number: 2,
            status: 'COMPLETED',
            executor_name: 'local_executor',
            executor_instance_id: 'inst-1',
            queue_delay_ms: 500,
            lease_owner: null,
            lease_expires_at: null,
            claimed_at: '2026-01-01T00:01:00Z',
            started_at: '2026-01-01T00:01:01Z',
            finished_at: '2026-01-01T00:02:00Z',
            last_heartbeat_at: null,
            finish_reason: 'success',
            failure_stage: null,
            retryable: false,
            retry_reason: null,
            error_code: null,
            error_category: null,
          },
        ],
        meta: { total_attempts: '2' },
      };

      server.use(
        http.get('/jobs/job-retries/attempts', () => {
          return HttpResponse.json(mockAttempts);
        }),
      );

      const result = await jobsService.getAttempts('job-retries');

      expect(result.items).toHaveLength(2);
      expect(result.items[0].status).toBe('FAILED');
      expect(result.items[1].status).toBe('COMPLETED');
      expect(result.meta.total_attempts).toBe('2');
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.get('/jobs/job-missing/attempts', () => {
          return HttpResponse.json({ detail: 'Job not found' }, { status: 404 });
        }),
      );

      await expect(jobsService.getAttempts('job-missing')).rejects.toThrow();
    });
  });
});
