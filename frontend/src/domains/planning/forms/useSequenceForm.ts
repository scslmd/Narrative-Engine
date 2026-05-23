import { useSequencePlanning } from '../useSequencePlanning';

export function useSequenceForm(tab: string) {
  const sequence = useSequencePlanning(tab);
  return {
    sequenceCreateOpen: sequence.sequenceCreateOpen,
    sequenceCreateTitle: sequence.sequenceCreateTitle,
    sequenceCreateSummary: sequence.sequenceCreateSummary,
    sequenceEditOpenId: sequence.sequenceEditOpenId,
    sequenceEditTitle: sequence.sequenceEditTitle,
    sequenceEditSummary: sequence.sequenceEditSummary,
    setSequenceCreateOpen: sequence.setSequenceCreateOpen,
    setSequenceCreateTitle: sequence.setSequenceCreateTitle,
    setSequenceCreateSummary: sequence.setSequenceCreateSummary,
    setSequenceEditOpenId: sequence.setSequenceEditOpenId,
    setSequenceEditTitle: sequence.setSequenceEditTitle,
    setSequenceEditSummary: sequence.setSequenceEditSummary,
  };
}
