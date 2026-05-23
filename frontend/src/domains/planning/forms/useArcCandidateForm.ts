import { useArcPlanning } from '../useArcPlanning';

export function useArcCandidateForm(tab: string) {
  const arcs = useArcPlanning(tab);
  return {
    arcCandidateCreateOpen: arcs.arcCandidateCreateOpen,
    arcCandidateCreateId: arcs.arcCandidateCreateId,
    arcCandidateCreateName: arcs.arcCandidateCreateName,
    arcCandidateCreateSummary: arcs.arcCandidateCreateSummary,
    setArcCandidateCreateOpen: arcs.setArcCandidateCreateOpen,
    setArcCandidateCreateId: arcs.setArcCandidateCreateId,
    setArcCandidateCreateName: arcs.setArcCandidateCreateName,
    setArcCandidateCreateSummary: arcs.setArcCandidateCreateSummary,
  };
}
