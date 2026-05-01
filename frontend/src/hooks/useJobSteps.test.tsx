import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { useJobSteps } from './useJobSteps';

describe('useJobSteps', () => {
  beforeEach(() => {
    server.use(
      http.get('/jobs/:id/steps', () => HttpResponse.json({ items: [] })),
      http.get('/role-model-checker/:id/steps', () => HttpResponse.json({ items: [] })),
    );
  });

  it('returns loading state initially', () => {
    const { result } = renderHook(() =>
      useJobSteps('j1', 'pipeline_job'),
    );
    expect(result.current.loading).toBe(true);
    expect(result.current.steps).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('fetches steps for pipeline job on mount', async () => {
    server.use(
      http.get('/jobs/:id/steps', () => {
        return HttpResponse.json({
          items: [
            {
              step_record_id: 's1',
              logical_run_id: 'j1',
              run_id: 'j1',
              run_kind: 'pipeline_job',
              attempt_number: 1,
              step_name: 'architect',
              step_index: 0,
              state: 'COMPLETED',
              project_id: 'proj-1',
            },
            {
              step_record_id: 's2',
              logical_run_id: 'j1',
              run_id: 'j1',
              run_kind: 'pipeline_job',
              attempt_number: 1,
              step_name: 'sequence',
              step_index: 1,
              state: 'COMPLETED',
              project_id: 'proj-1',
            },
          ],
        });
      }),
    );

    const { result } = renderHook(() =>
      useJobSteps('j1', 'pipeline_job'),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.steps).toHaveLength(2);
    expect(result.current.steps[0].step_name).toBe('architect');
  });

  it('fetches steps for role model check on mount', async () => {
    server.use(
      http.get('/role-model-checker/:id/steps', () => {
        return HttpResponse.json({
          items: [
            {
              step_record_id: 's3',
              logical_run_id: 'rmc-1',
              run_id: 'rmc-1',
              run_kind: 'role_model_check',
              attempt_number: 1,
              step_name: 'evaluate',
              step_index: 0,
              state: 'COMPLETED',
              project_id: 'proj-1',
            },
          ],
        });
      }),
    );

    const { result } = renderHook(() =>
      useJobSteps('rmc-1', 'role_model_check'),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.steps[0].step_name).toBe('evaluate');
  });

  it('includes attempt number as query param when provided', async () => {
    let receivedAttempt: string | null | undefined;
    server.use(
      http.get('/jobs/:id/steps', ({ request }) => {
        const url = new URL(request.url);
        receivedAttempt = url.searchParams.get('attempt');
        return HttpResponse.json({ items: [] });
      }),
    );

    const { result } = renderHook(() =>
      useJobSteps('j1', 'pipeline_job', 2),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(receivedAttempt).toBe('2');
  });

  it('handles empty steps response', async () => {
    server.use(
      http.get('/jobs/:id/steps', () => {
        return HttpResponse.json({ items: [] });
      }),
    );

    const { result } = renderHook(() =>
      useJobSteps('j-empty', 'pipeline_job'),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.steps).toEqual([]);
  });

  it('handles fetch error gracefully', async () => {
    server.use(
      http.get('/jobs/:id/steps', () => {
        return HttpResponse.json({ detail: 'not found' }, { status: 404 });
      }),
    );

    const { result } = renderHook(() =>
      useJobSteps('j-missing', 'pipeline_job'),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).not.toBeNull();
    expect(result.current.steps).toEqual([]);
  });

  it('exposes refetch function', async () => {
    let callCount = 0;
    server.use(
      http.get('/jobs/:id/steps', () => {
        callCount++;
        return HttpResponse.json({
          items: [
            {
              step_record_id: `s${callCount}`,
              logical_run_id: 'j1',
              run_id: 'j1',
              run_kind: 'pipeline_job',
              attempt_number: 1,
              step_name: callCount === 1 ? 'architect' : 'sequence',
              step_index: callCount - 1,
              state: 'COMPLETED',
              project_id: 'proj-1',
            },
          ],
        });
      }),
    );

    const { result } = renderHook(() =>
      useJobSteps('j1', 'pipeline_job'),
    );

    await waitFor(() => {
      expect(result.current.steps[0]?.step_name).toBe('architect');
    });

    await act(async () => {
      await result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.steps[0]?.step_name).toBe('sequence');
    });
  });
});
