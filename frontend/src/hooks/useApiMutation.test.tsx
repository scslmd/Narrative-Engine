import { describe, it, expect, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { ToastProvider } from './useToast';
import { ApiError } from '../lib/api';
import { useApiMutation } from './useApiMutation';

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

const WithProviders = ({ children, queryClient }: { children: ReactNode; queryClient?: QueryClient }) => {
  const client = queryClient || createQueryClient();
  return (
    <QueryClientProvider client={client}>
      <ToastProvider>{children}</ToastProvider>
    </QueryClientProvider>
  );
};

describe('useApiMutation', () => {
  it('returns initial idle state', () => {
    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.resolve('ok') }),
      { wrapper: WithProviders },
    );

    expect(result.current.isPending).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('returns data on successful mutation via mutateAsync', async () => {
    const mockData = { id: 'new-1', name: 'Created' };

    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.resolve(mockData) }),
      { wrapper: WithProviders },
    );

    let resolvedData: typeof mockData | undefined;
    await act(async () => {
      resolvedData = await result.current.mutateAsync(undefined);
    });

    expect(resolvedData).toEqual(mockData);
  });

  it('shows isPending during mutation', async () => {
    let resolveFn: (v: string) => void;
    const pending = new Promise<string>((resolve) => { resolveFn = resolve; });

    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => pending }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      result.current.mutate(undefined);
    });

    await waitFor(() => {
      expect(result.current.isPending).toBe(true);
    });

    act(() => { resolveFn!('done'); });
  });

  it('shows error toast for 401 status', async () => {
    const apiError = new ApiError('Authentication required', 401);

    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.reject(apiError) }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      try {
        await result.current.mutateAsync(undefined);
      } catch {
        // expected
      }
    });

    const toasts = result.current.allToasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].variant).toBe('error');
    expect(toasts[0].message).toBe('API key required — see Settings > API Keys and User Guide §Authentication');
  });

  it('shows error toast for 403 status', async () => {
    const apiError = new ApiError('Access denied', 403);

    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.reject(apiError) }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      try {
        await result.current.mutateAsync(undefined);
      } catch {
        // expected
      }
    });

    const toasts = result.current.allToasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].variant).toBe('error');
    expect(toasts[0].message).toBe('Access denied');
  });

  it('shows error toast with ApiError message for 404 status', async () => {
    const apiError = new ApiError('Project not found', 404);

    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.reject(apiError) }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      try {
        await result.current.mutateAsync(undefined);
      } catch {
        // expected
      }
    });

    const toasts = result.current.allToasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].variant).toBe('error');
    expect(toasts[0].message).toBe('Project not found');
  });

  it('shows error toast with ApiError message for 409 status', async () => {
    const apiError = new ApiError('Version conflict detected', 409);

    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.reject(apiError) }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      try {
        await result.current.mutateAsync(undefined);
      } catch {
        // expected
      }
    });

    const toasts = result.current.allToasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].variant).toBe('error');
    expect(toasts[0].message).toBe('Version conflict detected');
  });

  it('shows generic server error toast for 5xx status', async () => {
    const apiError = new ApiError('Internal Server Error', 500);

    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.reject(apiError) }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      try {
        await result.current.mutateAsync(undefined);
      } catch {
        // expected
      }
    });

    const toasts = result.current.allToasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].variant).toBe('error');
    expect(toasts[0].message).toBe('Server error occurred. Please try again later.');
  });

  it('suppresses toast when onErrorToast is false', async () => {
    const apiError = new ApiError('Resource not found', 404);

    const { result } = renderHook(
      () => useApiMutation({
        mutationFn: () => Promise.reject(apiError),
        onErrorToast: false,
      }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      try {
        await result.current.mutateAsync(undefined);
      } catch {
        // expected
      }
    });

    await waitFor(() => {
      expect(result.current.error).toBe(apiError);
    });
    expect(result.current.allToasts).toHaveLength(0);
  });

  it('shows success toast when onSuccessToast is set', async () => {
    const mockData = { id: 'created-1' };

    const { result } = renderHook(
      () => useApiMutation({
        mutationFn: () => Promise.resolve(mockData),
        onSuccessToast: 'Item created successfully',
      }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      await result.current.mutateAsync(undefined);
    });

    const toasts = result.current.allToasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].variant).toBe('success');
    expect(toasts[0].message).toBe('Item created successfully');
  });

  it('does not show success toast when onSuccessToast is null', async () => {
    const mockData = { id: 'no-toast' };

    const { result } = renderHook(
      () => useApiMutation({
        mutationFn: () => Promise.resolve(mockData),
        onSuccessToast: null,
      }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      await result.current.mutateAsync(undefined);
    });

    expect(result.current.allToasts).toHaveLength(0);
  });

  it('invalidates queries on success when invalidateKeys is set', async () => {
    const queryClient = createQueryClient();
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
    queryClient.setQueryData(['projects'], [{ id: 'p-1' }]);

    const mockData = { id: 'new-1' };
    const { result } = renderHook(
      () => useApiMutation({
        mutationFn: () => Promise.resolve(mockData),
        invalidateKeys: [['projects']],
      }),
      { wrapper: ({ children }) => <WithProviders queryClient={queryClient}>{children}</WithProviders> },
    );

    await act(async () => {
      await result.current.mutateAsync(undefined);
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['projects'] });
  });

  it('invalidates multiple query keys on success', async () => {
    const queryClient = createQueryClient();
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
    queryClient.setQueryData(['projects'], [{ id: 'p-1' }]);
    queryClient.setQueryData(['branches'], [{ id: 'b-1' }]);

    const { result } = renderHook(
      () => useApiMutation({
        mutationFn: () => Promise.resolve({ ok: true }),
        invalidateKeys: [['projects'], ['branches']],
      }),
      { wrapper: ({ children }) => <WithProviders queryClient={queryClient}>{children}</WithProviders> },
    );

    await act(async () => {
      await result.current.mutateAsync(undefined);
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['projects'] });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['branches'] });
  });

  it('does not invalidate queries when invalidateKeys is empty', async () => {
    const queryClient = createQueryClient();
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(
      () => useApiMutation({
        mutationFn: () => Promise.resolve({ ok: true }),
      }),
      { wrapper: ({ children }) => <WithProviders queryClient={queryClient}>{children}</WithProviders> },
    );

    await act(async () => {
      await result.current.mutateAsync(undefined);
    });

    expect(invalidateSpy).not.toHaveBeenCalled();
  });

  it('resetError clears the error state', async () => {
    const apiError = new ApiError('Fail', 500);

    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.reject(apiError) }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      try {
        await result.current.mutateAsync(undefined);
      } catch {
        // expected
      }
    });

    expect(result.current.error).toBe(apiError);

    await act(async () => {
      result.current.resetError();
    });

    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });
  });

  it('mutate triggers mutation without awaiting', async () => {
    const mockData = { id: 'fire-and-forget' };
    let called = false;
    const mutationFn = () => {
      called = true;
      return Promise.resolve(mockData);
    };

    const { result } = renderHook(
      () => useApiMutation({ mutationFn }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      result.current.mutate(undefined);
    });

    await waitFor(() => {
      expect(called).toBe(true);
    });
  });

  it('passes variables to mutationFn', async () => {
    let receivedVars: unknown;
    const mutationFn = (vars: { name: string }) => {
      receivedVars = vars;
      return Promise.resolve({ ok: true });
    };

    const { result } = renderHook(
      () => useApiMutation<{ name: string }, { ok: boolean }>({ mutationFn }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      await result.current.mutateAsync({ name: 'test' });
    });

    expect(receivedVars).toEqual({ name: 'test' });
  });

  it('returns error in return value on failure', async () => {
    const apiError = new ApiError('Something went wrong', 500);

    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.reject(apiError) }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      try {
        await result.current.mutateAsync(undefined);
      } catch {
        // expected
      }
    });

    expect(result.current.error).toBe(apiError);
  });

  it('handles non-ApiError errors gracefully', async () => {
    const plainError = new Error('Network failure');

    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.reject(plainError) }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      try {
        await result.current.mutateAsync(undefined);
      } catch {
        // expected
      }
    });

    const toasts = result.current.allToasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].variant).toBe('error');
    expect(toasts[0].message).toBe('Network failure');
  });

  it('shows generic message for unknown error type', async () => {
    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.reject({ weird: true }) }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      try {
        await result.current.mutateAsync(undefined);
      } catch {
        // expected
      }
    });

    const toasts = result.current.allToasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].variant).toBe('error');
    expect(toasts[0].message).toBe('An unexpected error occurred');
  });

  it('wraps non-ApiError in ApiError with status 0', async () => {
    const plainError = new Error('Network failure');

    const { result } = renderHook(
      () => useApiMutation({ mutationFn: () => Promise.reject(plainError) }),
      { wrapper: WithProviders },
    );

    await act(async () => {
      try {
        await result.current.mutateAsync(undefined);
      } catch {
        // expected
      }
    });

    expect(result.current.error).toBeInstanceOf(ApiError);
    expect((result.current.error as ApiError).status).toBe(0);
  });
});
