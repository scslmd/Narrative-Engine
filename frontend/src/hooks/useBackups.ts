import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { BackupInfo } from '../types/backup';

export function useBackups() {
  const queryClient = useQueryClient();

  const backupsQuery = useQuery({
    queryKey: ['backups'],
    queryFn: () => api.get('/v1/backup/list').then(r => r.data as BackupInfo[]),
  });

  const createMutation = useMutation({
    mutationFn: () => api.post('/v1/backup/create'),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['backups'] });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: (backupId: string) => api.post(`/v1/backup/restore/${backupId}`),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['backups'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (backupId: string) => api.delete(`/v1/backup/${backupId}`),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['backups'] });
    },
  });

  return {
    backups: backupsQuery.data ?? [],
    isLoading: backupsQuery.isLoading,
    createBackup: () => createMutation.mutateAsync(),
    restoreBackup: (backupId: string) => restoreMutation.mutateAsync(backupId),
    deleteBackup: (backupId: string) => deleteMutation.mutateAsync(backupId),
    isCreating: createMutation.isPending,
    isRestoring: restoreMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
