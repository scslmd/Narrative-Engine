import { describe, it, expect } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { ToastProvider } from './useToast';
import { useJobs, useJob, useCreateJob, useJobLogs as useJobLogsFromJobs } from './useJobs';
import type { JobDetail } from '../lib/jobsApi';

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

const WithProviders = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>
    <ToastProvider>{children}</ToastProvider>
  </QueryClientProvider>
);

describe('useJobs', () => {
  it('returns empty data when no jobs exist', async () => {
    const { result } = renderHook(() => useJobs('proj-1'), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual([]);
  });

  it('does not fetch when projectId is undefined', () => {
    const { result } = renderHook(() => useJobs(undefined), { wrapper: WithProviders });
    expect(result.current.isEnabled).toBe(false);
  });
});

describe('useJob', () => {
  it('returns loading state initially', () => {
    server.use(
      http.get('/v1/jobs/:id/status', () => {
        return HttpResponse.json({
          id: 'j1',
          phase: 'P-100',
          status: 'PROCESSING',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        });
      }),
    );

    const { result } = renderHook(() => useJob('j1'), { wrapper: WithProviders });
    expect(result.current.isLoading).toBe(true);
  });

  it('fetches job detail on mount', async () => {
    server.use(
      http.get('/v1/jobs/:id/status', () => {
        return HttpResponse.json({
          id: 'j1',
          phase: 'P-100',
          status: 'COMPLETED',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        });
      }),
    );

    const { result } = renderHook(() => useJob('j1'), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data?.job_id).toBe('j1');
    expect(result.current.data?.status).toBe('COMPLETED');
  });

  it('does not fetch when jobId is undefined', () => {
    const { result } = renderHook(() => useJob(undefined), { wrapper: WithProviders });
    expect(result.current.isEnabled).toBe(false);
  });
});

describe('useCreateJob', () => {
  it('throws error when projectId is undefined', async () => {
    const { result } = renderHook(() => useCreateJob(undefined), { wrapper: WithProviders });

    let errorMessage = '';
    await act(async () => {
      try {
        await result.current.mutateAsync('P-100');
      } catch (error: unknown) {
        errorMessage = error instanceof Error ? error.message : String(error);
      }
    });

    expect(errorMessage).toBe('No project ID provided');
  });

  it('creates a job and invalidates queries', async () => {
    server.use(
      http.post('/v1/jobs/create', async ({ request }) => {
        const body = (await request.json()) as { phase: string; payload?: Record<string, unknown> };
        return HttpResponse.json({
          id: 'j-new',
          phase: body.phase,
          status: 'PENDING',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        });
      }),
    );

    const { result } = renderHook(() => useCreateJob('proj-1'), { wrapper: WithProviders });

    let createdJob: JobDetail | undefined;
    await act(async () => {
      createdJob = await result.current.mutateAsync('P-200');
    });

    expect(createdJob?.job_id).toBe('j-new');
  });
});

describe('useJobLogs (from useJobs)', () => {
  it('returns loading state initially', () => {
    server.use(
      http.get('/v1/jobs/:id/logs', () => {
        return HttpResponse.json({
          id: 'j1',
          entries: [
            { timestamp: '2026-01-01T00:00:00Z', level: 'INFO', message: 'Started' },
          ],
        });
      }),
    );

    const { result } = renderHook(() => useJobLogsFromJobs('j1'), { wrapper: WithProviders });
    expect(result.current.isLoading).toBe(true);
  });

  it('fetches logs on mount', async () => {
    server.use(
      http.get('/v1/jobs/:id/logs', () => {
        return HttpResponse.json({
          id: 'j1',
          entries: [
            { timestamp: '2026-01-01T00:00:00Z', level: 'INFO', message: 'Started' },
            { timestamp: '2026-01-01T00:00:01Z', level: 'INFO', message: 'Done' },
          ],
        });
      }),
    );

    const { result } = renderHook(() => useJobLogsFromJobs('j1'), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data?.entries).toHaveLength(2);
  });

  it('does not fetch when jobId is undefined', () => {
    const { result } = renderHook(() => useJobLogsFromJobs(undefined), { wrapper: WithProviders });
    expect(result.current.isEnabled).toBe(false);
  });
});
