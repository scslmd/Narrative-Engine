import { describe, it, expect } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { ToastProvider } from './useToast';
import { useHealthCheck } from './useHealthCheck';

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

const WithProviders = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>
    <ToastProvider>{children}</ToastProvider>
  </QueryClientProvider>
);

describe('useHealthCheck', () => {
  it('starts with null status', () => {
    const { result } = renderHook(() => useHealthCheck(), { wrapper: WithProviders });
    expect(result.current.isLlmAvailable).toBeNull();
  });

  it('sets status from health check on mount (llama.cpp backend)', async () => {
    server.use(
      http.get('/health/ready', () => {
        return HttpResponse.json({ components: { inference: { backend: 'llama.cpp' } } });
      }),
    );

    const { result } = renderHook(() => useHealthCheck(), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.isLlmAvailable).toBe(true);
    });
  });

  it('sets unavailable status when backend is stub', async () => {
    server.use(
      http.get('/health/ready', () => {
        return HttpResponse.json({ components: { inference: { backend: 'stub' } } });
      }),
    );

    const { result } = renderHook(() => useHealthCheck(), { wrapper: WithProviders });

    await waitFor(() => {
      expect(result.current.isLlmAvailable).toBe(false);
    });
  });

  it('provides checkBeforeImport callback', async () => {
    server.use(
      http.get('/health/ready', () => {
        return HttpResponse.json({ components: { inference: { backend: 'llama.cpp' } } });
      }),
    );

    const { result } = renderHook(() => useHealthCheck(), { wrapper: WithProviders });

    let returnedValue: boolean;
    await act(async () => {
      returnedValue = await result.current.checkBeforeImport();
    });

    expect(returnedValue).toBe(true);
  });
});
