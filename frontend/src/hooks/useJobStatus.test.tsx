import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { useJobStatus } from './useJobStatus';

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

const WithProviders = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>
    {children}
  </QueryClientProvider>
);

describe('useJobStatus', () => {
  it('returns null values when jobId is null', () => {
    const { result } = renderHook(() => useJobStatus(null), { wrapper: WithProviders });
    expect(result.current.status).toBeNull();
    expect(result.current.phase).toBeNull();
    expect(result.current.progress).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.currentStep).toBeNull();
    expect(result.current.currentPhase).toBeNull();
    expect(result.current.attemptNumber).toBeNull();
  });

  it('returns loading state initially', () => {
    server.use(
      http.get('/jobs/:id/status', () => {
        return HttpResponse.json({
          id: 'j1',
          phase: 'P-100',
          status: 'PROCESSING',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        });
      }),
    );

    const { result } = renderHook(() => useJobStatus('j1'), { wrapper: WithProviders });
    expect(result.current.status).toBeNull();
  });

  it('fetches and returns job status on mount', async () => {
    server.use(
      http.get('/jobs/:id/status', () => {
        return HttpResponse.json({
          id: 'j1',
          phase: 'P-200',
          status: 'PROCESSING',
          current_step: 'sequencing',
          current_phase: 'P-200',
          attempt_number: 1,
          progress_current: 3,
          progress_total: 5,
        });
      }),
    );

    const { result } = renderHook(() => useJobStatus('j1'), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.status).toBe('PROCESSING');
    });

    expect(result.current.phase).toBe('P-200');
    expect(result.current.progress).toBe(60);
    expect(result.current.currentStep).toBe('sequencing');
    expect(result.current.currentPhase).toBe('P-200');
    expect(result.current.attemptNumber).toBe(1);
  });

  it('returns completed status', async () => {
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

    const { result } = renderHook(() => useJobStatus('j2'), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.status).toBe('COMPLETED');
    });

    expect(result.current.progress).toBe(100);
  });

  it('returns failed status with error', async () => {
    server.use(
      http.get('/jobs/:id/status', () => {
        return HttpResponse.json({
          id: 'j3',
          phase: 'P-400',
          status: 'FAILED',
          error: 'LLM inference timeout',
        });
      }),
    );

    const { result } = renderHook(() => useJobStatus('j3'), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.status).toBe('FAILED');
    });

    expect(result.current.error).toBe('LLM inference timeout');
  });

  it('returns null progress when progress fields are missing', async () => {
    server.use(
      http.get('/jobs/:id/status', () => {
        return HttpResponse.json({
          id: 'j4',
          phase: 'P-100',
          status: 'PENDING',
        });
      }),
    );

    const { result } = renderHook(() => useJobStatus('j4'), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.status).toBe('PENDING');
    });

    expect(result.current.progress).toBeNull();
  });
});
