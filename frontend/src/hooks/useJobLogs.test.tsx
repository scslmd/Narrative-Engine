import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { useJobLogs } from './useJobLogs';

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

const WithProviders = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>
    {children}
  </QueryClientProvider>
);

describe('useJobLogs', () => {
  it('returns null values when jobId is null', () => {
    const { result } = renderHook(() => useJobLogs(null), { wrapper: WithProviders });
    expect(result.current.logs).toEqual([]);
    expect(result.current.error).toBeNull();
  });

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

    const { result } = renderHook(() => useJobLogs('j1'), { wrapper: WithProviders });
    expect(result.current.isLoading).toBe(true);
  });

  it('fetches logs on mount', async () => {
    server.use(
      http.get('/v1/jobs/:id/logs', () => {
        return HttpResponse.json({
          id: 'j1',
          entries: [
            { timestamp: '2026-01-01T00:00:00Z', level: 'INFO', message: 'Job started' },
            { timestamp: '2026-01-01T00:00:01Z', level: 'WARNING', message: 'Slow response' },
            { timestamp: '2026-01-01T00:00:02Z', level: 'INFO', message: 'Job completed' },
          ],
        });
      }),
    );

    const { result } = renderHook(() => useJobLogs('j1'), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.logs).toHaveLength(3);
    expect(result.current.logs[0].message).toBe('Job started');
    expect(result.current.logs[1].level).toBe('WARNING');
  });

  it('handles empty log entries', async () => {
    server.use(
      http.get('/v1/jobs/:id/logs', () => {
        return HttpResponse.json({
          id: 'j-empty',
          entries: [],
        });
      }),
    );

    const { result } = renderHook(() => useJobLogs('j-empty'), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.logs).toEqual([]);
  });

  it('handles fetch error', async () => {
    server.use(
      http.get('/v1/jobs/:id/logs', () => {
        return HttpResponse.json({ detail: 'not found' }, { status: 404 });
      }),
    );

    const noRetryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, retryDelay: 0 },
        mutations: { retry: false },
      },
    });

    const NoRetryProviders = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={noRetryClient}>
        {children}
      </QueryClientProvider>
    );

    const { result } = renderHook(() => useJobLogs('j-missing'), {
      wrapper: NoRetryProviders,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).not.toBeNull();
    expect(result.current.logs).toEqual([]);
  });
});
