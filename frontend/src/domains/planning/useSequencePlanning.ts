import { usePlanningController } from './usePlanningController';

export function useSequencePlanning(tab: string) {
  const { state, callbacks } = usePlanningController(tab);
  return {
    sequencePlans: state.sequencePlans,
    sequencesLoading: state.sequencesLoading,
    sequencesError: state.sequencesError,
    sequenceCreateOpen: state.sequenceCreateOpen,
    sequenceCreateTitle: state.sequenceCreateTitle,
    sequenceCreateSummary: state.sequenceCreateSummary,
    sequenceEditOpenId: state.sequenceEditOpenId,
    sequenceEditTitle: state.sequenceEditTitle,
    sequenceEditSummary: state.sequenceEditSummary,
    setSequenceCreateOpen: callbacks.setSequenceCreateOpen,
    setSequenceCreateTitle: callbacks.setSequenceCreateTitle,
    setSequenceCreateSummary: callbacks.setSequenceCreateSummary,
    sequenceCreateSubmit: callbacks.sequenceCreateSubmit,
    setSequenceEditOpenId: callbacks.setSequenceEditOpenId,
    setSequenceEditTitle: callbacks.setSequenceEditTitle,
    setSequenceEditSummary: callbacks.setSequenceEditSummary,
    sequenceUpdateSubmit: callbacks.sequenceUpdateSubmit,
    sequenceReorder: callbacks.sequenceReorder,
    openEditSequence: callbacks.openEditSequence,
  };
}
