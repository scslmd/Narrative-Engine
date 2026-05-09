import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { createJob, getStatus, getLogs, getAttempts, getJobSteps, getJobLineage, retryJob } from './jobs';
import type { JobStatusResponse } from '../types/job';
import type { StepRecord, ArtifactLineageView } from '../types/inspect';

const mockJobStatus: JobStatusResponse = {
  id: 'job-123',
  phase: 'P-100',
  status: 'COMPLETED',
  attempt_number: 1,
};

describe('jobs', () => {
  describe('createJob', () => {
    it('creates a job with phase and payload (202)', async () => {
      server.use(
        http.post('/v1/jobs/create', async ({ request }) => {
          const body = (await request.json()) as { phase?: string };
          return HttpResponse.json(
            { ...mockJobStatus, phase: body.phase },
            { status: 202 },
          );
        }),
      );

      const result = await createJob({ phase: 'P-100', payload: { project_id: 'proj-1' } });

      expect(result.id).toBe('job-123');
      expect(result.phase).toBe('P-100');
    });

    it('creates a job and returns 200 response', async () => {
      server.use(
        http.post('/v1/jobs/create', () => {
          return HttpResponse.json(mockJobStatus, { status: 200 });
        }),
      );

      const result = await createJob({ phase: 'P-300', payload: {} });

      expect(result.id).toBe('job-123');
    });

    it('throws on 201 (service only accepts 200 or 202)', async () => {
      server.use(
        http.post('/v1/jobs/create', () => {
          return HttpResponse.json(mockJobStatus, { status: 201 });
        }),
      );

      await expect(
       createJob({ phase: 'P-100', payload: {} }),
       ).rejects.toThrow('Failed to create job: 201');
    });

    it('throws on 400 invalid request', async () => {
      server.use(
        http.post('/v1/jobs/create', () => {
          return HttpResponse.json({ detail: 'Invalid phase' }, { status: 400 });
        }),
      );

      await expect(
        createJob({ phase: 'P-100', payload: {} }),
      ).rejects.toThrow('Invalid phase');
    });

    it('throws on 409 idempotency conflict', async () => {
      server.use(
        http.post('/v1/jobs/create', () => {
          return HttpResponse.json({ detail: 'Conflict' }, { status: 409 });
        }),
      );

      await expect(
        createJob({ phase: 'P-100', payload: {} }),
      ).rejects.toThrow('Conflict');
    });

    it('throws on 500 server error', async () => {
      server.use(
        http.post('/v1/jobs/create', () => {
          return HttpResponse.json({ detail: 'Internal error' }, { status: 500 });
        }),
      );

      await expect(
        createJob({ phase: 'P-100', payload: {} }),
      ).rejects.toThrow('Server error occurred. Please try again later.');
    });
  });

  describe('getStatus', () => {
    it('returns job status by ID', async () => {
      server.use(
        http.get('/v1/jobs/job-123/status', () => {
          return HttpResponse.json(mockJobStatus);
        }),
      );

      const result = await getStatus('job-123');

      expect(result.id).toBe('job-123');
      expect(result.status).toBe('COMPLETED');
    });

    it('returns PROCESSING status', async () => {
      server.use(
        http.get('/v1/jobs/job-running/status', () => {
          return HttpResponse.json({ ...mockJobStatus, id: 'job-running', status: 'PROCESSING' });
        }),
      );

      const result = await getStatus('job-running');

      expect(result.status).toBe('PROCESSING');
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.get('/v1/jobs/job-missing/status', () => {
          return HttpResponse.json({ detail: 'Job not found' }, { status: 404 });
        }),
      );

      await expect(getStatus('job-missing')).rejects.toThrow();
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
        http.get('/v1/jobs/job-123/logs', () => {
          return HttpResponse.json(mockLogs);
        }),
      );

      const result = await getLogs('job-123');

      expect(result.id).toBe('job-123');
      expect(result.entries).toHaveLength(2);
      expect(result.entries[0].level).toBe('INFO');
    });

    it('returns empty log entries', async () => {
      server.use(
        http.get('/v1/jobs/job-empty/logs', () => {
          return HttpResponse.json({ id: 'job-empty', entries: [] });
        }),
      );

      const result = await getLogs('job-empty');

      expect(result.entries).toEqual([]);
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.get('/v1/jobs/job-missing/logs', () => {
          return HttpResponse.json({ detail: 'Job not found' }, { status: 404 });
        }),
      );

      await expect(getLogs('job-missing')).rejects.toThrow();
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
        http.get('/v1/jobs/job-123/attempts', () => {
          return HttpResponse.json(mockAttempts);
        }),
      );

      const result = await getAttempts('job-123');

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
        http.get('/v1/jobs/job-retries/attempts', () => {
          return HttpResponse.json(mockAttempts);
        }),
      );

      const result = await getAttempts('job-retries');

      expect(result.items).toHaveLength(2);
      expect(result.items[0].status).toBe('FAILED');
      expect(result.items[1].status).toBe('COMPLETED');
      expect(result.meta.total_attempts).toBe('2');
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.get('/v1/jobs/job-missing/attempts', () => {
          return HttpResponse.json({ detail: 'Job not found' }, { status: 404 });
        }),
      );

      await expect(getAttempts('job-missing')).rejects.toThrow();
    });
  });

  describe('getJobSteps', () => {
    it('returns step records for a job', async () => {
      const mockSteps: StepRecord[] = [
        {
          step_record_id: 's1',
          logical_run_id: 'job-123',
          run_id: 'job-123',
          run_kind: 'pipeline_job',
          attempt_number: 1,
          step_name: 'architect',
          step_index: 0,
          state: 'COMPLETED',
          project_id: 'proj-1',
        },
        {
          step_record_id: 's2',
          logical_run_id: 'job-123',
          run_id: 'job-123',
          run_kind: 'pipeline_job',
          attempt_number: 1,
          step_name: 'sequence',
          step_index: 1,
          state: 'COMPLETED',
          project_id: 'proj-1',
        },
      ];

      server.use(
        http.get('/v1/jobs/job-123/steps', () => {
          return HttpResponse.json({ items: mockSteps });
        }),
      );

      const result = await getJobSteps('job-123');

      expect(result.items).toHaveLength(2);
      expect(result.items[0].step_name).toBe('architect');
      expect(result.items[1].step_name).toBe('sequence');
      expect(result.items[0].state).toBe('COMPLETED');
    });

    it('returns empty steps array', async () => {
      server.use(
        http.get('/v1/jobs/job-empty/steps', () => {
          return HttpResponse.json({ items: [] });
        }),
      );

      const result = await getJobSteps('job-empty');

      expect(result.items).toEqual([]);
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.get('/v1/jobs/job-missing/steps', () => {
          return HttpResponse.json({ detail: 'Job not found' }, { status: 404 });
        }),
      );

      await expect(getJobSteps('job-missing')).rejects.toThrow();
    });
  });

  describe('getJobLineage', () => {
    it('returns lineage artifacts for a job', async () => {
      const mockArtifacts: ArtifactLineageView[] = [
        {
          artifact_id: 'a1',
          artifact_kind: 'PROJECT_BRIEF',
          state: 'CANONICAL',
          run_id: 'job-123',
          step_name: 'architect',
          created_at: '2026-01-01T00:00:00Z',
        },
        {
          artifact_id: 'a2',
          artifact_kind: 'CHAPTER_PLAN',
          state: 'CANONICAL',
          run_id: 'job-123',
          step_name: 'sequence',
          created_at: '2026-01-01T00:01:00Z',
        },
      ];

      server.use(
        http.get('/v1/jobs/job-123/lineage', () => {
          return HttpResponse.json({ items: mockArtifacts });
        }),
      );

      const result = await getJobLineage('job-123');

      expect(result.items).toHaveLength(2);
      expect(result.items[0].artifact_id).toBe('a1');
      expect(result.items[0].artifact_kind).toBe('PROJECT_BRIEF');
      expect(result.items[1].state).toBe('CANONICAL');
    });

    it('returns empty lineage array', async () => {
      server.use(
        http.get('/v1/jobs/job-empty/lineage', () => {
          return HttpResponse.json({ items: [] });
        }),
      );

      const result = await getJobLineage('job-empty');

      expect(result.items).toEqual([]);
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.get('/v1/jobs/job-missing/lineage', () => {
          return HttpResponse.json({ detail: 'Job not found' }, { status: 404 });
        }),
      );

      await expect(getJobLineage('job-missing')).rejects.toThrow();
    });
  });

  describe('retryJob', () => {
    it('retries a failed job and returns new run info', async () => {
      server.use(
        http.post('/v1/jobs/job-failed/retry', () => {
          return HttpResponse.json({
            run_id: 'job-retry-1',
            status: 'PENDING',
          });
        }),
      );

      const result = await retryJob('job-failed');

      expect(result.run_id).toBe('job-retry-1');
      expect(result.status).toBe('PENDING');
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.post('/v1/jobs/job-missing/retry', () => {
          return HttpResponse.json({ detail: 'Job not found' }, { status: 404 });
        }),
      );

      await expect(retryJob('job-missing')).rejects.toThrow();
    });
  });
});
