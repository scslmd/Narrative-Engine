import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  updateRelationship,
  deleteRelationship,
  createRelationship,
  extractRelationships,
  type RelationshipUpdateRequest,
  type RelationshipExtractRequest,
} from '../services/relationships';
import type { RelationshipEdge, RelationshipEdgeCreateRequest } from '../types/characters';

export function useRelationships(projectId: string) {
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (data: RelationshipEdgeCreateRequest) =>
      createRelationship(data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['relationships', projectId] });
    },
  });

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

  const extractMutation = useMutation({
    mutationFn: (data: RelationshipExtractRequest) =>
      extractRelationships(projectId, data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['relationships', projectId] });
    },
  });

  return {
    createRelationship: (data: RelationshipEdgeCreateRequest) =>
      createMutation.mutateAsync(data),
    updateRelationship: (edgeId: string, data: Partial<RelationshipEdge>) =>
      updateMutation.mutateAsync({ edgeId, data }),
    deleteRelationship: (edgeId: string) => deleteMutation.mutateAsync(edgeId),
    extractRelationships: (data: RelationshipExtractRequest) =>
      extractMutation.mutateAsync(data),
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isExtracting: extractMutation.isPending,
  };
}
