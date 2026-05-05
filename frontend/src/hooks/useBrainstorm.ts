import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getBrainstormItems, createBrainstormItem, clusterBrainstormItems, promoteBrainstormItem } from '../services/brainstorm';
import type { BrainstormItemCreateRequest, BrainstormPromotionResult } from '../types/brainstorm';

export function useBrainstorm(projectId: string) {
  const queryClient = useQueryClient();

  const itemsQuery = useQuery({
    queryKey: ['brainstorm-items', projectId],
    queryFn: () => getBrainstormItems(projectId),
    enabled: Boolean(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (data: Omit<BrainstormItemCreateRequest, 'project_id'>) =>
      createBrainstormItem({ ...data, project_id: projectId }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['brainstorm-items', projectId] });
    },
  });

  const clusterMutation = useMutation({
    mutationFn: (itemIds: string[]) =>
      clusterBrainstormItems({ item_ids: itemIds, project_id: projectId }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['brainstorm-items', projectId] });
    },
  });

  const promoteMutation = useMutation({
    mutationFn: ({ itemId, targetKind, targetId }: { itemId: string; targetKind: string; targetId: string }) =>
      promoteBrainstormItem(itemId, projectId, targetKind, targetId),
    onSuccess: async (result: BrainstormPromotionResult) => {
      await queryClient.invalidateQueries({ queryKey: ['brainstorm-items', projectId] });
      return result;
    },
  });

  return {
    items: itemsQuery.data ?? [],
    isLoading: itemsQuery.isLoading,
    addItem: (data: Omit<BrainstormItemCreateRequest, 'project_id'>) => createMutation.mutateAsync(data),
    clusterItems: (itemIds: string[]) => clusterMutation.mutateAsync(itemIds),
    promoteItem: (itemId: string, targetKind: string, targetId: string) =>
      promoteMutation.mutateAsync({ itemId, targetKind, targetId }),
    isPromoting: promoteMutation.isPending,
  };
}
