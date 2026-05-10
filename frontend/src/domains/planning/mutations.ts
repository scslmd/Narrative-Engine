import { useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
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
import { queryKeys } from '../shared/queryKeys';

interface PlanningMutationsArgs {
  projectId: string;
}

export function usePlanningMutations({ projectId }: PlanningMutationsArgs) {
  const queryClient = useQueryClient();

  return useMemo(() => {
    const invalidate = (key: readonly unknown[]) => void queryClient.invalidateQueries({ queryKey: key });
    const seqKey = queryKeys.planning.sequencePlans(projectId);
    const chapKey = queryKeys.planning.chapterPlans(projectId);
    const sceneKey = queryKeys.planning.scenePlans(projectId);
    const beatKey = queryKeys.planning.beatPlans(projectId);

    return {
      sequencePlanCreateMutation: { mutateAsync: (data: Parameters<typeof createSequencePlan>[1]) => createSequencePlan(projectId, data).then(() => invalidate(seqKey)) },
      sequencePlanUpdateMutation: { mutateAsync: (data: { sequenceId: string; projectId: string; title: string; summary?: string }) => updateSequencePlan(data.sequenceId, data.projectId, { title: data.title, summary: data.summary }).then(() => invalidate(seqKey)) },
      chapterPlanCreateMutation: { mutateAsync: (data: Parameters<typeof createChapterPlan>[1]) => createChapterPlan(projectId, data).then(() => invalidate(chapKey)) },
      chapterPlanUpdateMutation: { mutateAsync: (data: { chapterId: string; projectId: string; title: string; objective: string; conflict?: string; stakes?: string }) => updateChapterPlan(data.chapterId, data.projectId, { title: data.title, objective: data.objective, conflict: data.conflict, stakes: data.stakes }).then(() => invalidate(chapKey)) },
      scenePlanCreateMutation: { mutateAsync: (data: Parameters<typeof createScenePlan>[1]) => createScenePlan(projectId, data).then(() => invalidate(sceneKey)) },
      scenePlanUpdateMutation: { mutateAsync: (data: { sceneId: string; projectId: string; title: string; objective: string; conflict?: string; stakes?: string }) => updateScenePlan(data.sceneId, data.projectId, { title: data.title, objective: data.objective, conflict: data.conflict, stakes: data.stakes }).then(() => invalidate(sceneKey)) },
      beatPlanCreateMutation: { mutateAsync: (data: Parameters<typeof createBeatPlan>[1]) => createBeatPlan(projectId, data).then(() => invalidate(beatKey)) },
      beatPlanUpdateMutation: { mutateAsync: (data: { beatId: string; projectId: string; objective: string; conflict?: string; stakes?: string; arc_stage?: string }) => updateBeatPlan(data.beatId, data.projectId, { objective: data.objective, conflict: data.conflict, stakes: data.stakes, arc_stage: data.arc_stage }).then(() => invalidate(beatKey)) },
      chapterPacketCreateMutation: { mutateAsync: (data: Parameters<typeof createChapterPacket>[1]) => createChapterPacket(projectId, data).then(() => invalidate(queryKeys.planning.chapterPackets(projectId))) },
      sequenceReorderMutation: { mutateAsync: (orderedIds: string[]) => reorderPlanObjects({ project_id: projectId, plan_kind: 'sequence', ordered_plan_ids: orderedIds }).then(() => invalidate(seqKey)) },
      chapterReorderMutation: { mutateAsync: (orderedIds: string[]) => reorderPlanObjects({ project_id: projectId, plan_kind: 'chapter', ordered_plan_ids: orderedIds }).then(() => invalidate(chapKey)) },
      sceneReorderMutation: { mutateAsync: (orderedIds: string[]) => reorderPlanObjects({ project_id: projectId, plan_kind: 'scene', ordered_plan_ids: orderedIds }).then(() => invalidate(sceneKey)) },
    };
  }, [projectId, queryClient]);
}
