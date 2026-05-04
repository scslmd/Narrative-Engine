import { describe, it, expect } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { ToastProvider } from './useToast';
import { ApiError } from '../lib/api';
import { useApiQuery } from './useApiQuery';

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

const WithProviders = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>
    <ToastProvider>{children}</ToastProvider>
  </QueryClientProvider>
);

describe('useApiQuery', () => {
  it('returns loading state initially', async () => {
    let resolveFn: (v: string) => void;
    const pending = new Promise<string>((resolve) => { resolveFn = resolve; });

    const { result } = renderHook(
      () => useApiQuery({ queryKey: ['test'], serviceFn: () => pending }),
      { wrapper: WithProviders },
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
    expect(result.current.error).toBeNull();

    act(() => { resolveFn!('ok'); });
  });

  it('returns data on successful query', async () => {
    const mockData = { id: 'proj-1', name: 'Test Project' };

    const { result } = renderHook(
      () => useApiQuery({ queryKey: ['project'], serviceFn: () => Promise.resolve(mockData) }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
  });

  it('returns ApiError on failed query', async () => {
    const apiError = new ApiError('Resource not found', 404);

    const { result } = renderHook(
      () => useApiQuery({ queryKey: ['project'], serviceFn: () => Promise.reject(apiError) }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe(apiError);
    expect(result.current.data).toBeUndefined();
  });

  it('shows error toast for 401 status', async () => {
    const apiError = new ApiError('Authentication required', 401);

    const { result } = renderHook(
      () => useApiQuery({
        queryKey: ['auth'],
        serviceFn: () => Promise.reject(apiError),
      }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const toast = result.current.allToasts[0];
    expect(toast).toBeDefined();
    expect(toast.variant).toBe('error');
    expect(toast.message).toBe('Authentication required');
  });

  it('shows error toast for 403 status', async () => {
    const apiError = new ApiError('Access denied', 403);

    const { result } = renderHook(
      () => useApiQuery({
        queryKey: ['forbidden'],
        serviceFn: () => Promise.reject(apiError),
      }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const toast = result.current.allToasts[0];
    expect(toast).toBeDefined();
    expect(toast.variant).toBe('error');
    expect(toast.message).toBe('Access denied');
  });

  it('shows error toast with ApiError message for 404 status', async () => {
    const apiError = new ApiError('Project not found', 404);

    const { result } = renderHook(
      () => useApiQuery({
        queryKey: ['project'],
        serviceFn: () => Promise.reject(apiError),
      }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const toast = result.current.allToasts[0];
    expect(toast).toBeDefined();
    expect(toast.variant).toBe('error');
    expect(toast.message).toBe('Project not found');
  });

  it('shows error toast with ApiError message for 409 status', async () => {
    const apiError = new ApiError('Version conflict detected', 409);

    const { result } = renderHook(
      () => useApiQuery({
        queryKey: ['document'],
        serviceFn: () => Promise.reject(apiError),
      }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const toast = result.current.allToasts[0];
    expect(toast).toBeDefined();
    expect(toast.variant).toBe('error');
    expect(toast.message).toBe('Version conflict detected');
  });

  it('shows generic server error toast for 5xx status', async () => {
    const apiError = new ApiError('Internal Server Error', 500);

    const { result } = renderHook(
      () => useApiQuery({
        queryKey: ['server'],
        serviceFn: () => Promise.reject(apiError),
      }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const toast = result.current.allToasts[0];
    expect(toast).toBeDefined();
    expect(toast.variant).toBe('error');
    expect(toast.message).toBe('Server error occurred. Please try again later.');
  });

  it('suppresses toast when onErrorToast is false', async () => {
    const apiError = new ApiError('Resource not found', 404);

    const { result } = renderHook(
      () => useApiQuery({
        queryKey: ['silent'],
        serviceFn: () => Promise.reject(apiError),
        onErrorToast: false,
      }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe(apiError);
    expect(result.current.allToasts).toHaveLength(0);
  });

  it('shows success toast when onSuccessToast is set', async () => {
    const mockData = { id: 'proj-1' };

    const { result } = renderHook(
      () => useApiQuery({
        queryKey: ['success'],
        serviceFn: () => Promise.resolve(mockData),
        onSuccessToast: 'Project loaded successfully',
      }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockData);
    const toast = result.current.allToasts[0];
    expect(toast).toBeDefined();
    expect(toast.variant).toBe('success');
    expect(toast.message).toBe('Project loaded successfully');
  });

  it('does not show success toast when onSuccessToast is null', async () => {
    const mockData = { id: 'proj-1' };

    const { result } = renderHook(
      () => useApiQuery({
        queryKey: ['no-toast'],
        serviceFn: () => Promise.resolve(mockData),
        onSuccessToast: null,
      }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.allToasts).toHaveLength(0);
  });

  it('retry re-executes the query', async () => {
    let callCount = 0;
    const serviceFn = () => {
      callCount++;
      if (callCount === 1) return Promise.reject(new ApiError('Fail', 500));
      return Promise.resolve({ id: 'recovered' });
    };

    const { result } = renderHook(
      () => useApiQuery({ queryKey: ['retry'], serviceFn }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).not.toBeNull();
    expect(callCount).toBe(1);

    await act(async () => {
      await result.current.retry();
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual({ id: 'recovered' });
    expect(result.current.error).toBeNull();
    expect(callCount).toBe(2);
  });

  it('refetch re-executes the query', async () => {
    let callCount = 0;
    const serviceFn = () => {
      callCount++;
      return Promise.resolve({ id: `call-${callCount}` });
    };

    const { result } = renderHook(
      () => useApiQuery({ queryKey: ['refetch'], serviceFn }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual({ id: 'call-1' });
    expect(callCount).toBe(1);

    await act(async () => {
      await result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual({ id: 'call-2' });
    expect(callCount).toBe(2);
  });

  it('uses configured staleTime of 5 minutes', async () => {
    const { result } = renderHook(
      () => useApiQuery({ queryKey: ['stale'], serviceFn: () => Promise.resolve({ ok: true }) }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual({ ok: true });
  });

  it('does not auto-retry on error (retry disabled)', async () => {
    let callCount = 0;
    const serviceFn = () => {
      callCount++;
      return Promise.reject(new ApiError('Transient failure', 502));
    };

    const { result } = renderHook(
      () => useApiQuery({ queryKey: ['transient'], serviceFn }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).not.toBeNull();
    expect(callCount).toBe(1);
  });
});
