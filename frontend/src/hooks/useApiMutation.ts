import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../lib/api';
import { useToast } from './useToast';

interface UseApiMutationOptions<TVariables, TData> {
  mutationFn: (variables: TVariables) => Promise<TData>;
  invalidateKeys?: string[][];
  onSuccessToast?: string | null;
  onErrorToast?: boolean;
}

interface UseApiMutationReturn<TVariables, TData> {
  mutate: (variables: TVariables) => void;
  mutateAsync: (variables: TVariables) => Promise<TData>;
  isPending: boolean;
  error: ApiError | null;
  resetError: () => void;
  allToasts: Array<{ id: string; message: string; variant: 'success' | 'error' | 'info' }>;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        return 'Authentication required';
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

export function useApiMutation<TVariables, TData>(
  options: UseApiMutationOptions<TVariables, TData>,
): UseApiMutationReturn<TVariables, TData> {
  const {
    mutationFn,
    invalidateKeys,
    onSuccessToast,
    onErrorToast = true,
  } = options;

  const queryClient = useQueryClient();
  const { addToast, toasts } = useToast();

  const { mutate, mutateAsync, isPending, error, reset: resetMutation } = useMutation<TData, Error, TVariables>({
    mutationFn,
    retry: false,
    onSuccess: async () => {
      if (invalidateKeys) {
        await Promise.all(
          invalidateKeys.map((key) => queryClient.invalidateQueries({ queryKey: key })),
        );
      }
      if (onSuccessToast) {
        addToast(onSuccessToast, 'success');
      }
    },
    onError: (err) => {
      if (onErrorToast) {
        const message = getErrorMessage(err);
        addToast(message, 'error');
      }
    },
  });

  const apiError = error
    ? error instanceof ApiError
      ? error
      : new ApiError(error?.message ?? 'Unknown error', 0)
    : null;

  return {
    mutate,
    mutateAsync,
    isPending,
    error: apiError,
    resetError: resetMutation,
    allToasts: toasts,
  };
}
