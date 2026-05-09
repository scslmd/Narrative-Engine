import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  createSequencePlan,
  updateSequencePlan,
  createChapterPlan,
  updateChapterPlan,
  createScenePlan,
  updateScenePlan,
  createBeatPlan,
  updateBeatPlan,
  createChapterPacket,
  reorderPlanObjects,
} from '../../services/planning';
import { invalidateMany } from '../shared/invalidation';
import { queryKeys } from '../shared/queryKeys';

interface PlanningMutationsArgs {
  projectId: string;
}

export function usePlanningMutations({ projectId }: PlanningMutationsArgs) {
  const queryClient = useQueryClient();

  const sequencePlanCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createSequencePlan>[1]) => createSequencePlan(projectId, data),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.sequencePlans(projectId)]);
    },
  });

  const sequencePlanUpdateMutation = useMutation({
    mutationFn: (data: { sequenceId: string; projectId: string; title: string; summary?: string }) =>
      updateSequencePlan(data.sequenceId, data.projectId, { title: data.title, summary: data.summary }),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.sequencePlans(projectId)]);
    },
  });

  const chapterPlanCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createChapterPlan>[1]) => createChapterPlan(projectId, data),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.chapterPlans(projectId)]);
    },
  });

  const chapterPlanUpdateMutation = useMutation({
    mutationFn: (data: { chapterId: string; projectId: string; title: string; objective: string; conflict?: string; stakes?: string }) =>
      updateChapterPlan(data.chapterId, data.projectId, {
        title: data.title,
        objective: data.objective,
        conflict: data.conflict,
        stakes: data.stakes,
      }),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.chapterPlans(projectId)]);
    },
  });

  const scenePlanCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createScenePlan>[1]) => createScenePlan(projectId, data),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.scenePlans(projectId)]);
    },
  });

  const scenePlanUpdateMutation = useMutation({
    mutationFn: (data: { sceneId: string; projectId: string; title: string; objective: string; conflict?: string; stakes?: string }) =>
      updateScenePlan(data.sceneId, data.projectId, {
        title: data.title,
        objective: data.objective,
        conflict: data.conflict,
        stakes: data.stakes,
      }),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.scenePlans(projectId)]);
    },
  });

  const beatPlanCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createBeatPlan>[1]) => createBeatPlan(projectId, data),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.beatPlans(projectId)]);
    },
  });

  const beatPlanUpdateMutation = useMutation({
    mutationFn: (data: { beatId: string; projectId: string; objective: string; conflict?: string; stakes?: string; arc_stage?: string }) =>
      updateBeatPlan(data.beatId, data.projectId, {
        objective: data.objective,
        conflict: data.conflict,
        stakes: data.stakes,
        arc_stage: data.arc_stage,
      }),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.beatPlans(projectId)]);
    },
  });

  const chapterPacketCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createChapterPacket>[1]) => createChapterPacket(projectId, data),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.chapterPackets(projectId)]);
    },
  });

  const sequenceReorderMutation = useMutation({
    mutationFn: (orderedIds: string[]) =>
      reorderPlanObjects({
        project_id: projectId,
        plan_kind: 'sequence',
        ordered_plan_ids: orderedIds,
      }),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.sequencePlans(projectId)]);
    },
  });

  const chapterReorderMutation = useMutation({
    mutationFn: (orderedIds: string[]) =>
      reorderPlanObjects({
        project_id: projectId,
        plan_kind: 'chapter',
        ordered_plan_ids: orderedIds,
      }),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.chapterPlans(projectId)]);
    },
  });

  const sceneReorderMutation = useMutation({
    mutationFn: (orderedIds: string[]) =>
      reorderPlanObjects({
        project_id: projectId,
        plan_kind: 'scene',
        ordered_plan_ids: orderedIds,
      }),
    onSuccess: () => {
      void invalidateMany(queryClient, [queryKeys.planning.scenePlans(projectId)]);
    },
  });

  return {
    sequencePlanCreateMutation,
    sequencePlanUpdateMutation,
    chapterPlanCreateMutation,
    chapterPlanUpdateMutation,
    scenePlanCreateMutation,
    scenePlanUpdateMutation,
    beatPlanCreateMutation,
    beatPlanUpdateMutation,
    chapterPacketCreateMutation,
    sequenceReorderMutation,
    chapterReorderMutation,
    sceneReorderMutation,
  };
}
