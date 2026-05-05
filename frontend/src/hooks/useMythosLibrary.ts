import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createMythosEntry, deleteMythosEntry, getMythosEntries, updateMythosEntry } from '../services/mythosLibrary';
import type { MythosEntryCreateRequest, MythosEntryUpdateRequest } from '../types/mythos';

export function useMythosLibrary(projectId: string) {
  const queryClient = useQueryClient();

  const entriesQuery = useQuery({
    queryKey: ['mythos-entries', projectId],
    queryFn: () => getMythosEntries(projectId),
    enabled: Boolean(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (data: Omit<MythosEntryCreateRequest, 'project_id'>) =>
      createMythosEntry({ ...data, project_id: projectId }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['mythos-entries', projectId] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ mythosId, data }: { mythosId: string; data: MythosEntryUpdateRequest }) =>
      updateMythosEntry(mythosId, projectId, data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['mythos-entries', projectId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (mythosId: string) => deleteMythosEntry(projectId, mythosId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['mythos-entries', projectId] });
    },
  });

  return {
    entries: entriesQuery.data ?? [],
    isLoading: entriesQuery.isLoading,
    createEntry: (data: Omit<MythosEntryCreateRequest, 'project_id'>) => createMutation.mutateAsync(data),
    updateEntry: (mythosId: string, data: MythosEntryUpdateRequest) => updateMutation.mutateAsync({ mythosId, data }),
    deleteEntry: (mythosId: string) => deleteMutation.mutateAsync(mythosId),
  };
}
