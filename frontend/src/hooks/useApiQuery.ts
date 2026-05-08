import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ApiError } from '../lib/api';
import { useToast, type ToastItem } from './useToast';

export interface UseApiQueryOptions<T> {
  queryKey: string[];
  serviceFn: () => Promise<T>;
  deps?: unknown[];
  onErrorToast?: boolean;
  onSuccessToast?: string | null;
}

export interface UseApiQueryReturn<T> {
  data: T | undefined;
  isLoading: boolean;
  error: ApiError | null;
  retry: () => Promise<void>;
  refetch: () => Promise<void>;
  allToasts: ToastItem[];
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        return 'API key required — see Settings > API Keys and User Guide §Authentication';
      case 403:
        return 'Access denied';
      case 500:
      case 502:
      case 503:
      case 504:
        return 'Server error occurred. Please try again later.';
      default:
        return error.message;
    }
  }
  return error instanceof Error ? error.message : 'An unexpected error occurred';
}

export function useApiQuery<T>(options: UseApiQueryOptions<T>): UseApiQueryReturn<T> {
  const { queryKey, serviceFn, onErrorToast = true, onSuccessToast } = options;
  const { addToast, toasts } = useToast();
  const successShown = useRef(false);

  const { data, isLoading, error, refetch } = useQuery<T, Error>({
    queryKey,
    queryFn: serviceFn,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  useEffect(() => {
    if (error && onErrorToast) {
      const message = getErrorMessage(error);
      addToast(message, 'error');
    }
  }, [error, onErrorToast, addToast]);

  useEffect(() => {
    if (data !== undefined && onSuccessToast && !successShown.current) {
      successShown.current = true;
      addToast(onSuccessToast, 'success');
    }
    if (error) {
      successShown.current = false;
    }
  }, [data, error, onSuccessToast, addToast]);

  const apiError = error ? (error instanceof ApiError ? error : new ApiError(error?.message ?? 'Unknown error', 0)) : null;

  return {
    data,
    isLoading,
    error: apiError,
    retry: async () => { await refetch(); },
    refetch: async () => { await refetch(); },
    allToasts: toasts,
  };
}
