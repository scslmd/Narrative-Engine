import { useQueries } from '@tanstack/react-query';
import {
  getSequencePlans,
  getChapterPlans,
  getScenePlans,
  getBeatPlans,
  getPlanningDependencies,
  getChapterPackets,
} from '../../services/planning';
import { queryKeys } from '../shared/queryKeys';

interface PlanningQueriesArgs {
  projectId: string;
  tab: string;
}

export function usePlanningQueries({ projectId, tab }: PlanningQueriesArgs) {
  const results = useQueries({
    queries: [
      {
        queryKey: queryKeys.planning.sequencePlans(projectId),
        queryFn: () => getSequencePlans(projectId),
        enabled: Boolean(projectId) && tab === 'planning',
      },
      {
        queryKey: queryKeys.planning.chapterPlans(projectId),
        queryFn: () => getChapterPlans(projectId),
        enabled: Boolean(projectId) && tab === 'planning',
      },
      {
        queryKey: queryKeys.planning.scenePlans(projectId),
        queryFn: () => getScenePlans(projectId),
        enabled: Boolean(projectId) && tab === 'planning',
      },
      {
        queryKey: queryKeys.planning.beatPlans(projectId),
        queryFn: () => getBeatPlans(projectId),
        enabled: Boolean(projectId) && tab === 'planning',
      },
      {
        queryKey: queryKeys.planning.dependencies(projectId),
        queryFn: () => getPlanningDependencies(projectId),
        enabled: Boolean(projectId) && tab === 'planning',
      },
      {
        queryKey: queryKeys.planning.chapterPackets(projectId),
        queryFn: () => getChapterPackets(projectId),
        enabled: Boolean(projectId) && tab === 'planning',
      },
    ],
  });

  return {
    sequencePlansQuery: results[0],
    chapterPlansQuery: results[1],
    scenePlansQuery: results[2],
    beatPlansQuery: results[3],
    dependenciesQuery: results[4],
    chapterPacketsQuery: results[5],
  };
}
