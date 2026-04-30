import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useToast, ToastProvider } from './useToast';

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

const WithToastProvider = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>
    <ToastProvider>{children}</ToastProvider>
  </QueryClientProvider>
);

describe('useToast', () => {
  it('throws when used outside ToastProvider', () => {
    const NoopWrapper = ({ children }: { children: ReactNode }) => <>{children}</>;
    expect(() => {
      renderHook(() => useToast(), { wrapper: NoopWrapper });
    }).toThrow('useToast must be used within ToastProvider');
  });

  it('starts with empty toasts array', () => {
    const { result } = renderHook(() => useToast(), { wrapper: WithToastProvider });
    expect(result.current.toasts).toEqual([]);
  });

  it('adds a toast with default variant (info)', () => {
    const { result } = renderHook(() => useToast(), { wrapper: WithToastProvider });
    act(() => {
      result.current.addToast('Test message');
    });
    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0].variant).toBe('info');
    expect(result.current.toasts[0].message).toBe('Test message');
  });

  it('adds a toast with specified variant', () => {
    const { result } = renderHook(() => useToast(), { wrapper: WithToastProvider });

    act(() => {
      result.current.addToast('Error message', 'error');
    });
    expect(result.current.toasts[0].variant).toBe('error');

    act(() => {
      result.current.addToast('Success message', 'success');
    });
    expect(result.current.toasts[1].variant).toBe('success');
  });

  it('removes a toast by ID', () => {
    const { result } = renderHook(() => useToast(), { wrapper: WithToastProvider });

    act(() => {
      result.current.addToast('First');
    });
    act(() => {
      result.current.addToast('Second');
    });

    const idToRemove = result.current.toasts[0].id;
    act(() => {
      result.current.removeToast(idToRemove);
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0].message).toBe('Second');
  });

  it('limits toasts to maximum of 3, removing oldest', () => {
    const { result } = renderHook(() => useToast(), { wrapper: WithToastProvider });

    act(() => {
      result.current.addToast('One');
    });
    act(() => {
      result.current.addToast('Two');
    });
    act(() => {
      result.current.addToast('Three');
    });

    expect(result.current.toasts).toHaveLength(3);

    act(() => {
      result.current.addToast('Four');
    });

    expect(result.current.toasts).toHaveLength(3);
    expect(result.current.toasts[0].message).toBe('Two');
    expect(result.current.toasts[1].message).toBe('Three');
    expect(result.current.toasts[2].message).toBe('Four');
  });
});
