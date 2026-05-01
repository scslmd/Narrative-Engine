import { describe, it, expect, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { vi } from 'vitest';
import { useJobMonitor } from './useJobMonitor';
import { useJobStore } from '../stores/jobStore';
import { useJobStatus } from './useJobStatus';

vi.mock('./useJobStatus', () => ({
  useJobStatus: vi.fn(),
}));

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
    vi.clearAllMocks();
    act(() => {
      useJobStore.setState({ activeJobId: null, isVisible: false });
    });
  });

  it('returns null jobId when no active job', () => {
    vi.mocked(useJobStatus).mockReturnValue({
      status: null,
      phase: null,
      progress: null,
      error: null,
      isPolling: false,
      currentStep: null,
      currentPhase: null,
      attemptNumber: null,
    });

    const { result, unmount } = renderHook(() => useJobMonitor(), { wrapper: WithProviders });
    expect(result.current.jobId).toBeNull();
    expect(result.current.isVisible).toBe(false);
    unmount();
  });

  it('exposes onDismiss that clears the store', () => {
    vi.mocked(useJobStatus).mockReturnValue({
      status: null,
      phase: null,
      progress: null,
      error: null,
      isPolling: false,
      currentStep: null,
      currentPhase: null,
      attemptNumber: null,
    });

    act(() => {
      useJobStore.setState({ activeJobId: 'j1', isVisible: true });
    });

    const { result, unmount } = renderHook(() => useJobMonitor(), { wrapper: WithProviders });
    expect(result.current.jobId).toBe('j1');

    act(() => {
      result.current.onDismiss();
    });

    expect(result.current.jobId).toBeNull();
    expect(result.current.isVisible).toBe(false);
    unmount();
  });

  it('fetches status when active job is set', async () => {
    vi.mocked(useJobStatus).mockReturnValue({
      phase: 'P-100',
      status: 'RUNNING',
      progress: null,
      error: null,
      isPolling: true,
      currentStep: 'architecting',
      currentPhase: null,
      attemptNumber: 1,
    });

    act(() => {
      useJobStore.setState({ activeJobId: 'j1', isVisible: true });
    });

    const { result, unmount } = renderHook(() => useJobMonitor(), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.status).toBe('RUNNING');
    });

    expect(result.current.jobId).toBe('j1');
    expect(result.current.phase).toBe('P-100');
    expect(result.current.currentStep).toBe('architecting');
    unmount();
  });

  it('reflects completed job status', async () => {
    vi.mocked(useJobStatus).mockReturnValue({
      phase: 'P-300',
      status: 'COMPLETED',
      progress: 100,
      error: null,
      isPolling: false,
      currentStep: null,
      currentPhase: null,
      attemptNumber: 1,
    });

    act(() => {
      useJobStore.setState({ activeJobId: 'j2', isVisible: true });
    });

    const { result, unmount } = renderHook(() => useJobMonitor(), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.status).toBe('COMPLETED');
    });

    expect(result.current.progress).toBe(100);
    unmount();
  });

  it('onDismiss resets store and clears monitor state', () => {
    vi.mocked(useJobStatus).mockReturnValue({
      status: null,
      phase: null,
      progress: null,
      error: null,
      isPolling: false,
      currentStep: null,
      currentPhase: null,
      attemptNumber: null,
    });

    act(() => {
      useJobStore.setState({ activeJobId: 'j5', isVisible: true });
    });

    const { result, unmount } = renderHook(() => useJobMonitor(), { wrapper: WithProviders });
    expect(result.current.jobId).toBe('j5');

    act(() => {
      result.current.onDismiss();
    });

    expect(useJobStore.getState().activeJobId).toBeNull();
    expect(useJobStore.getState().isVisible).toBe(false);
    unmount();
  });
});
