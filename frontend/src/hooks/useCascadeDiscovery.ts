import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import {
  submitScan,
  getJobStatus,
  getStagedEntities,
  updateEntityApproval,
  applyStagedEntities,
  undoApply,
  discardStaging,
} from '../services/discovery';
import type {
  CascadeScanRequest,
  EntityApprovalUpdate,
} from '../types/discovery';

export function useCascadeDiscovery() {
  const queryClient = useQueryClient();
  const [currentStageId, setCurrentStageId] = useState<string | null>(null);

  const scanMutation = useMutation({
    mutationFn: (request: CascadeScanRequest) => submitScan(request),
  });

  const useJobQuery = (jobId: string) => useQuery({
    queryKey: ['discovery-job', jobId],
    queryFn: () => getJobStatus(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'completed' || status === 'failed' ? false : 2000;
    },
  });

  const stagingQuery = useQuery({
    queryKey: ['discovery-staging', currentStageId],
    queryFn: () =>
      currentStageId
        ? getStagedEntities(currentStageId)
        : Promise.resolve({ stage_id: '', project_id: '', characters: [], relationships: [], world_bible: [] }),
    enabled: !!currentStageId,
  });

  const approvalMutation = useMutation({
    mutationFn: ({ stageId, updates }: { stageId: string; updates: EntityApprovalUpdate[] }) =>
      updateEntityApproval(stageId, updates),
  });

  const applyMutation = useMutation({
    mutationFn: (stageId: string) => applyStagedEntities(stageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['characters'] });
      queryClient.invalidateQueries({ queryKey: ['relationships'] });
      queryClient.invalidateQueries({ queryKey: ['world-bible'] });
    },
  });

  const undoMutation = useMutation({
    mutationFn: (stageId: string) => undoApply(stageId),
  });

  const discardMutation = useMutation({
    mutationFn: (stageId: string) => discardStaging(stageId),
  });

  return {
    scanMutation,
    useJobQuery,
    stagingQuery,
    approvalMutation,
    applyMutation,
    undoMutation,
    discardMutation,
    currentStageId,
    setCurrentStageId,
  };
}