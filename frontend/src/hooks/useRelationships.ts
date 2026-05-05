import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  updateRelationship,
  deleteRelationship,
  type RelationshipUpdateRequest,
} from '../services/relationships';
import type { RelationshipEdge } from '../types/characters';

export function useRelationships(projectId: string) {
  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: ({ edgeId, data }: { edgeId: string; data: Partial<RelationshipEdge> }) =>
      updateRelationship(edgeId, data as RelationshipUpdateRequest, projectId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['relationships', projectId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (edgeId: string) => deleteRelationship(edgeId, projectId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['relationships', projectId] });
    },
  });

  return {
    updateRelationship: (edgeId: string, data: Partial<RelationshipEdge>) =>
      updateMutation.mutateAsync({ edgeId, data }),
    deleteRelationship: (edgeId: string) => deleteMutation.mutateAsync(edgeId),
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
