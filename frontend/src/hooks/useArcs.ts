import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getArcCandidates, getArcSelections, updateArcSelection, deleteArcSelection } from '../services/arcs';
import type { ArcSelectionUpdateRequest } from '../types/arcs';

export function useArcs(projectId: string) {
  const queryClient = useQueryClient();

  const candidatesQuery = useQuery({
    queryKey: ['arc-candidates', projectId],
    queryFn: () => getArcCandidates(projectId),
    enabled: Boolean(projectId),
  });

  const selectionsQuery = useQuery({
    queryKey: ['arc-selections', projectId],
    queryFn: () => getArcSelections(projectId),
    enabled: Boolean(projectId),
  });

  const updateMutation = useMutation({
    mutationFn: ({ selectionId, data }: { selectionId: string; data: ArcSelectionUpdateRequest }) =>
      updateArcSelection(selectionId, data, projectId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['arc-selections', projectId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (selectionId: string) => deleteArcSelection(selectionId, projectId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['arc-selections', projectId] });
    },
  });

  return {
    candidates: candidatesQuery.data ?? [],
    selections: selectionsQuery.data ?? [],
    isLoading: candidatesQuery.isLoading || selectionsQuery.isLoading,
    updateArcSelection: (selectionId: string, data: ArcSelectionUpdateRequest) =>
      updateMutation.mutateAsync({ selectionId, data }),
    deleteArcSelection: (selectionId: string) => deleteMutation.mutateAsync(selectionId),
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
