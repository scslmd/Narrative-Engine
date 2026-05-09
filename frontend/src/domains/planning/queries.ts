import { useQuery } from '@tanstack/react-query';
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
  const sequencePlansQuery = useQuery({
    queryKey: queryKeys.planning.sequencePlans(projectId),
    queryFn: () => getSequencePlans(projectId),
    enabled: Boolean(projectId) && tab === 'planning',
  });

  const chapterPlansQuery = useQuery({
    queryKey: queryKeys.planning.chapterPlans(projectId),
    queryFn: () => getChapterPlans(projectId),
    enabled: Boolean(projectId) && tab === 'planning',
  });

  const scenePlansQuery = useQuery({
    queryKey: queryKeys.planning.scenePlans(projectId),
    queryFn: () => getScenePlans(projectId),
    enabled: Boolean(projectId) && tab === 'planning',
  });

  const beatPlansQuery = useQuery({
    queryKey: queryKeys.planning.beatPlans(projectId),
    queryFn: () => getBeatPlans(projectId),
    enabled: Boolean(projectId) && tab === 'planning',
  });

  const dependenciesQuery = useQuery({
    queryKey: queryKeys.planning.dependencies(projectId),
    queryFn: () => getPlanningDependencies(projectId),
    enabled: Boolean(projectId) && tab === 'planning',
  });

  const chapterPacketsQuery = useQuery({
    queryKey: queryKeys.planning.chapterPackets(projectId),
    queryFn: () => getChapterPackets(projectId),
    enabled: Boolean(projectId) && tab === 'planning',
  });

  return {
    sequencePlansQuery,
    chapterPlansQuery,
    scenePlansQuery,
    beatPlansQuery,
    dependenciesQuery,
    chapterPacketsQuery,
  };
}
