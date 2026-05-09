import {
  usePlanningController,
  type PlanningTabCallbacks,
  type PlanningTabState,
} from '../domains/planning/usePlanningController';

export type { PlanningTabCallbacks, PlanningTabState };

export function usePlanningTab(tab: string): {
  state: PlanningTabState;
  callbacks: PlanningTabCallbacks;
} {
  return usePlanningController(tab);
}
