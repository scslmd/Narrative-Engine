import { usePlanningController } from './usePlanningController';

export function usePlanningRetries(tab: string) {
  const { callbacks } = usePlanningController(tab);
  return {
    retrySequences: callbacks.retrySequences,
    retryChapters: callbacks.retryChapters,
    retryScenes: callbacks.retryScenes,
    retryBeats: callbacks.retryBeats,
    retryDependencies: callbacks.retryDependencies,
    retryPackets: callbacks.retryPackets,
    retryCards: callbacks.retryCards,
  };
}
