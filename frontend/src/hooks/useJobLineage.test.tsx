import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { useJobLineage } from './useJobLineage';

describe('useJobLineage', () => {
  beforeEach(() => {
    server.use(
      http.get('/jobs/:id/lineage', () => HttpResponse.json({ items: [] })),
      http.get('/role-model-checker/:id/lineage', () => HttpResponse.json({ items: [] })),
    );
  });

  it('returns loading state initially', () => {
    const { result } = renderHook(() =>
      useJobLineage('j1', 'pipeline_job'),
    );
    expect(result.current.loading).toBe(true);
    expect(result.current.artifacts).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('fetches lineage for pipeline job on mount', async () => {
    server.use(
      http.get('/jobs/:id/lineage', () => {
        return HttpResponse.json({
          items: [
            {
              artifact_id: 'a1',
              artifact_kind: 'PROJECT_BRIEF',
              state: 'CANONICAL',
              run_id: 'j1',
              step_name: 'architect',
              created_at: '2026-01-01T00:00:00Z',
            },
          ],
        });
      }),
    );

    const { result } = renderHook(() =>
      useJobLineage('j1', 'pipeline_job'),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.artifacts).toHaveLength(1);
    expect(result.current.artifacts[0].artifact_id).toBe('a1');
  });

  it('fetches lineage for role model check on mount', async () => {
    server.use(
      http.get('/role-model-checker/:id/lineage', () => {
        return HttpResponse.json({
          items: [
            {
              artifact_id: 'a2',
              artifact_kind: 'SCENE_STORYBOARD',
              state: 'DRAFT',
              run_id: 'rmc-1',
              step_name: 'evaluate',
              created_at: '2026-01-01T00:00:00Z',
            },
          ],
        });
      }),
    );

    const { result } = renderHook(() =>
      useJobLineage('rmc-1', 'role_model_check'),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.artifacts[0].artifact_id).toBe('a2');
  });

  it('includes attempt number as query param when provided', async () => {
    let receivedAttempt: string | null | undefined;
    server.use(
      http.get('/jobs/:id/lineage', ({ request }) => {
        const url = new URL(request.url);
        receivedAttempt = url.searchParams.get('attempt');
        return HttpResponse.json({ items: [] });
      }),
    );

    const { result } = renderHook(() =>
      useJobLineage('j1', 'pipeline_job', 3),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(receivedAttempt).toBe('3');
  });

  it('handles empty lineage response', async () => {
    server.use(
      http.get('/jobs/:id/lineage', () => {
        return HttpResponse.json({ items: [] });
      }),
    );

    const { result } = renderHook(() =>
      useJobLineage('j-empty', 'pipeline_job'),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.artifacts).toEqual([]);
  });

  it('handles fetch error gracefully', async () => {
    server.use(
      http.get('/jobs/:id/lineage', () => {
        return HttpResponse.json({ detail: 'not found' }, { status: 404 });
      }),
    );

    const { result } = renderHook(() =>
      useJobLineage('j-missing', 'pipeline_job'),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).not.toBeNull();
    expect(result.current.artifacts).toEqual([]);
  });

  it('exposes refetch function', async () => {
    let callCount = 0;
    server.use(
      http.get('/jobs/:id/lineage', () => {
        callCount++;
        return HttpResponse.json({
          items: [
            {
              artifact_id: `a${callCount}`,
              artifact_kind: 'PROJECT_BRIEF',
              state: 'CANONICAL',
              run_id: 'j1',
              step_name: 'architect',
              created_at: '2026-01-01T00:00:00Z',
            },
          ],
        });
      }),
    );

    const { result } = renderHook(() =>
      useJobLineage('j1', 'pipeline_job'),
    );

    await waitFor(() => {
      expect(result.current.artifacts[0]?.artifact_id).toBe('a1');
    });

    await act(async () => {
      await result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.artifacts[0]?.artifact_id).toBe('a2');
    });
  });
});
