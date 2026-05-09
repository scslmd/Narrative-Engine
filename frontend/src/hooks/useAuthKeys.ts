import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { ApiKeyInfo } from '../types/authKeys';

export function useAuthKeys() {
  const queryClient = useQueryClient();

  const keysQuery = useQuery({
    queryKey: ['auth-keys'],
    queryFn: () => api.get('/v1/auth/keys').then(r => r.data as ApiKeyInfo[]),
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => api.post('/v1/auth/keys', { name }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['auth-keys'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (prefix: string) => api.delete(`/v1/auth/keys/${prefix}`),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['auth-keys'] });
    },
  });

  return {
    keys: keysQuery.data ?? [],
    isLoading: keysQuery.isLoading,
    createKey: (name: string) => createMutation.mutateAsync(name),
    deleteKey: (prefix: string) => deleteMutation.mutateAsync(prefix),
    isCreating: createMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
