import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createPatternEntry, deletePatternEntry, getPatternEntries, updatePatternEntry } from '../services/patternLibrary';
import type { PatternEntryCreateRequest, PatternEntryUpdateRequest } from '../types/patterns';

export function usePatternLibrary(projectId: string) {
  const queryClient = useQueryClient();

  const entriesQuery = useQuery({
    queryKey: ['pattern-entries', projectId],
    queryFn: () => getPatternEntries(projectId),
    enabled: Boolean(projectId),
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: (data: Omit<PatternEntryCreateRequest, 'project_id'>) =>
      createPatternEntry({ ...data, project_id: projectId }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['pattern-entries', projectId] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ patternId, data }: { patternId: string; data: PatternEntryUpdateRequest }) =>
      updatePatternEntry(patternId, projectId, data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['pattern-entries', projectId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (patternId: string) => deletePatternEntry(projectId, patternId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['pattern-entries', projectId] });
    },
  });

  return {
    entries: entriesQuery.data ?? [],
    isLoading: entriesQuery.isLoading,
    createEntry: (data: Omit<PatternEntryCreateRequest, 'project_id'>) => createMutation.mutateAsync(data),
    updateEntry: (patternId: string, data: PatternEntryUpdateRequest) => updateMutation.mutateAsync({ patternId, data }),
    deleteEntry: (patternId: string) => deleteMutation.mutateAsync(patternId),
  };
}
