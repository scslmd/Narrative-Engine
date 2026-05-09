import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { getModelCatalog, runChecker, getCheckerStatus, retryChecker, getCheckerAttempts } from './checker';
import type { ModelCatalog, RoleModelCheckStatus, RoleModelCheckRequest } from '../types/checker';

const mockStatus: RoleModelCheckStatus = {
  run_id: 'run-123',
  status: 'COMPLETED',
  attempt_number: 1,
};

const mockCatalog: ModelCatalog = {
  workflow_order: ['architect', 'drafter'],
  discovered_models: [
    { role: 'architect', model_id: 'model-a', name: 'Architect Model' },
    { role: 'drafter', model_id: 'model-d', name: 'Drafter Model' },
  ],
};

const mockRequest: RoleModelCheckRequest = {
  project_id: 'proj-1',
  models: { architect: 'model-a' },
};

describe('checker service', () => {
  describe('getModelCatalog', () => {
    it('returns the model catalog on 200', async () => {
      server.use(
        http.get('/v1/models', () => {
          return HttpResponse.json(mockCatalog);
        }),
      );

      const result = await getModelCatalog();

      expect(result.workflow_order).toEqual(['architect', 'drafter']);
      expect(result.discovered_models).toHaveLength(2);
    });

    it('throws on non-200 response', async () => {
      server.use(
        http.get('/v1/models', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getModelCatalog()).rejects.toThrow('Not found');
    });
  });

  describe('runChecker', () => {
    it('runs a checker and returns 202 response', async () => {
      server.use(
        http.post('/v1/role-model-checker/run', async ({ request }) => {
          const body = (await request.json()) as { project_id?: string };
          return HttpResponse.json(
            { ...mockStatus, run_id: `run-${body.project_id}` },
            { status: 202 },
          );
        }),
      );

      const result = await runChecker(mockRequest);

      expect(result.run_id).toBe('run-proj-1');
      expect(result.status).toBe('COMPLETED');
    });

    it('runs a checker and accepts 200 response', async () => {
      server.use(
        http.post('/v1/role-model-checker/run', () => {
          return HttpResponse.json(mockStatus, { status: 200 });
        }),
      );

      const result = await runChecker(mockRequest);

      expect(result.run_id).toBe('run-123');
    });

    it('throws on 400 invalid request', async () => {
      server.use(
        http.post('/v1/role-model-checker/run', () => {
          return HttpResponse.json({ detail: 'Invalid project' }, { status: 400 });
        }),
      );

      await expect(runChecker(mockRequest)).rejects.toThrow('Invalid project');
    });

    it('throws on 500 server error', async () => {
      server.use(
        http.post('/v1/role-model-checker/run', () => {
          return HttpResponse.json({ detail: 'Internal error' }, { status: 500 });
        }),
      );

      await expect(runChecker(mockRequest)).rejects.toThrow('Server error occurred. Please try again later.');
    });
  });

  describe('getCheckerStatus', () => {
    it('returns checker status by run ID', async () => {
      server.use(
        http.get('/v1/role-model-checker/run-123/status', () => {
          return HttpResponse.json(mockStatus);
        }),
      );

      const result = await getCheckerStatus('run-123');

      expect(result.run_id).toBe('run-123');
      expect(result.status).toBe('COMPLETED');
      expect(result.attempt_number).toBe(1);
    });

    it('returns RUNNING status with progress', async () => {
      server.use(
        http.get('/v1/role-model-checker/run-running/status', () => {
          return HttpResponse.json({
            run_id: 'run-running',
            status: 'RUNNING' as const,
            attempt_number: 1,
            progress_current: 3,
            progress_total: 5,
          });
        }),
      );

      const result = await getCheckerStatus('run-running');

      expect(result.status).toBe('RUNNING');
      expect(result.progress_current).toBe(3);
      expect(result.progress_total).toBe(5);
    });

    it('returns FAILED status with error', async () => {
      server.use(
        http.get('/v1/role-model-checker/run-failed/status', () => {
          return HttpResponse.json({
            run_id: 'run-failed',
            status: 'FAILED' as const,
            attempt_number: 2,
            error: 'Inference timeout',
          });
        }),
      );

      const result = await getCheckerStatus('run-failed');

      expect(result.status).toBe('FAILED');
      expect(result.error).toBe('Inference timeout');
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.get('/v1/role-model-checker/run-missing/status', () => {
          return HttpResponse.json({ detail: 'Run not found' }, { status: 404 });
        }),
      );

      await expect(getCheckerStatus('run-missing')).rejects.toThrow('Run not found');
    });
  });

  describe('retryChecker', () => {
    it('retries a failed checker run', async () => {
      server.use(
        http.post('/v1/role-model-checker/run-123/retry', () => {
          return HttpResponse.json(
            { ...mockStatus, status: 'QUEUED', attempt_number: 2 },
            { status: 202 },
          );
        }),
      );

      const result = await retryChecker('run-123');

      expect(result.status).toBe('QUEUED');
      expect(result.attempt_number).toBe(2);
    });

    it('throws on non-202 response', async () => {
      server.use(
        http.post('/v1/role-model-checker/run-404/retry', () => {
          return HttpResponse.json({ detail: 'Run not found' }, { status: 404 });
        }),
      );

      await expect(retryChecker('run-404')).rejects.toThrow('Run not found');
    });

    it('throws on 500 server error', async () => {
      server.use(
        http.post('/v1/role-model-checker/run-123/retry', () => {
          return HttpResponse.json({ detail: 'Internal error' }, { status: 500 });
        }),
      );

      await expect(retryChecker('run-123')).rejects.toThrow('Server error occurred. Please try again later.');
    });
  });

  describe('getCheckerAttempts', () => {
    it('returns attempt history for a run', async () => {
      const mockAttempts = {
        run_id: 'run-123',
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
        ],
        meta: { total_attempts: '1' },
      };

      server.use(
        http.get('/v1/role-model-checker/run-123/attempts', () => {
          return HttpResponse.json(mockAttempts);
        }),
      );

      const result = await getCheckerAttempts('run-123');

      expect(result.run_id).toBe('run-123');
      expect(result.items).toHaveLength(1);
      expect(result.items[0].attempt_number).toBe(1);
      expect(result.items[0].status).toBe('FAILED');
    });

    it('returns multiple attempts with retries', async () => {
      const mockAttempts = {
        run_id: 'run-retries',
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
        http.get('/v1/role-model-checker/run-retries/attempts', () => {
          return HttpResponse.json(mockAttempts);
        }),
      );

      const result = await getCheckerAttempts('run-retries');

      expect(result.items).toHaveLength(2);
      expect(result.items[0].status).toBe('FAILED');
      expect(result.items[1].status).toBe('COMPLETED');
      expect(result.meta.total_attempts).toBe('2');
    });

    it('returns empty attempt list', async () => {
      server.use(
        http.get('/v1/role-model-checker/run-empty/attempts', () => {
          return HttpResponse.json({ run_id: 'run-empty', items: [], meta: {} });
        }),
      );

      const result = await getCheckerAttempts('run-empty');

      expect(result.items).toEqual([]);
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.get('/v1/role-model-checker/run-missing/attempts', () => {
          return HttpResponse.json({ detail: 'Run not found' }, { status: 404 });
        }),
      );

      await expect(getCheckerAttempts('run-missing')).rejects.toThrow('Run not found');
    });
  });
});


