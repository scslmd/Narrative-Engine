import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { useJobMonitor } from './useJobMonitor';
import { useJobStore } from '../stores/jobStore';

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

const WithProviders = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>
    {children}
  </QueryClientProvider>
);

describe('useJobMonitor', () => {
  afterEach(() => {
    useJobStore.setState({ activeJobId: null, isVisible: false });
  });

  it('returns null jobId when no active job', () => {
    const { result } = renderHook(() => useJobMonitor(), { wrapper: WithProviders });
    expect(result.current.jobId).toBeNull();
    expect(result.current.isVisible).toBe(false);
  });

  it('exposes onDismiss that clears the store', () => {
    act(() => {
      useJobStore.setState({ activeJobId: 'j1', isVisible: true });
    });

    const { result } = renderHook(() => useJobMonitor(), { wrapper: WithProviders });
    expect(result.current.jobId).toBe('j1');

    act(() => {
      result.current.onDismiss();
    });

    expect(result.current.jobId).toBeNull();
    expect(result.current.isVisible).toBe(false);
  });

  it('fetches status when active job is set', async () => {
    server.use(
      http.get('/jobs/:id/status', () => {
        return HttpResponse.json({
          id: 'j1',
          phase: 'P-100',
          status: 'RUNNING',
          current_step: 'architecting',
          attempt_number: 1,
        });
      }),
    );

    act(() => {
      useJobStore.setState({ activeJobId: 'j1', isVisible: true });
    });

    const { result } = renderHook(() => useJobMonitor(), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.status).toBe('RUNNING');
    });

    expect(result.current.jobId).toBe('j1');
    expect(result.current.phase).toBe('P-100');
    expect(result.current.currentStep).toBe('architecting');
  });

  it('reflects completed job status', async () => {
    server.use(
      http.get('/jobs/:id/status', () => {
        return HttpResponse.json({
          id: 'j2',
          phase: 'P-300',
          status: 'COMPLETED',
          progress_current: 1,
          progress_total: 1,
        });
      }),
    );

    act(() => {
      useJobStore.setState({ activeJobId: 'j2', isVisible: true });
    });

    const { result } = renderHook(() => useJobMonitor(), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.status).toBe('COMPLETED');
    });

    expect(result.current.progress).toBe(100);
  });

  it('onDismiss resets store and clears monitor state', () => {
    act(() => {
      useJobStore.setState({ activeJobId: 'j5', isVisible: true });
    });

    const { result } = renderHook(() => useJobMonitor(), { wrapper: WithProviders });
    expect(result.current.jobId).toBe('j5');

    act(() => {
      result.current.onDismiss();
    });

    expect(useJobStore.getState().activeJobId).toBeNull();
    expect(useJobStore.getState().isVisible).toBe(false);
  });
});
