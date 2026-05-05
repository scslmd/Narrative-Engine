import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createFoundation, getFoundation, getFoundationRevisions, getReviewCues, updateFoundation } from '../services/foundation';
import type { FoundationCreateRequest, FoundationUpdateRequest } from '../types/foundation';

export function useFoundation(projectId: string) {
  const queryClient = useQueryClient();

  const profileQuery = useQuery({
    queryKey: ['foundation', projectId],
    queryFn: () => getFoundation(projectId),
    enabled: Boolean(projectId),
  });

  const revisionsQuery = useQuery({
    queryKey: ['foundation-revisions', projectId],
    queryFn: () => getFoundationRevisions(projectId),
    enabled: Boolean(projectId),
  });

  const reviewCuesQuery = useQuery({
    queryKey: ['foundation-review-cues', projectId],
    queryFn: () => getReviewCues(projectId),
    enabled: Boolean(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (data: FoundationCreateRequest) => createFoundation(data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['foundation', projectId] });
      await queryClient.invalidateQueries({ queryKey: ['foundation-revisions', projectId] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: FoundationUpdateRequest) => updateFoundation(projectId, data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['foundation', projectId] });
      await queryClient.invalidateQueries({ queryKey: ['foundation-revisions', projectId] });
    },
  });

  const profile = profileQuery.data?.active_profile ?? null;

  return {
    profile,
    revisions: revisionsQuery.data ?? [],
    reviewCues: reviewCuesQuery.data ?? [],
    isLoading: profileQuery.isLoading,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    createProfile: (data: FoundationCreateRequest) => createMutation.mutateAsync(data),
    updateProfile: (data: FoundationUpdateRequest) => updateMutation.mutateAsync(data),
  };
}
