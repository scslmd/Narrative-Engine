import { usePlanningController } from './usePlanningController';

export function useArcPlanning(tab: string) {
  const { state, callbacks } = usePlanningController(tab);
  return {
    arcCandidates: state.arcCandidates,
    arcSelections: state.arcSelections,
    arcStageMaps: state.arcStageMaps,
    arcComparisons: state.arcComparisons,
    selectedArcId: state.selectedArcId,
    candidatesLoading: state.candidatesLoading,
    selectionsLoading: state.selectionsLoading,
    stageMapsLoading: state.stageMapsLoading,
    comparisonsLoading: state.comparisonsLoading,
    arcCandidateCreateOpen: state.arcCandidateCreateOpen,
    arcCandidateCreateId: state.arcCandidateCreateId,
    arcCandidateCreateName: state.arcCandidateCreateName,
    arcCandidateCreateSummary: state.arcCandidateCreateSummary,
    stageMapCreateOpen: state.stageMapCreateOpen,
    stageMapCreateArcId: state.stageMapCreateArcId,
    stageMapCreateNotes: state.stageMapCreateNotes,
    stageMapCreateKinds: state.stageMapCreateKinds,
    setArcCandidateCreateOpen: callbacks.setArcCandidateCreateOpen,
    setArcCandidateCreateId: callbacks.setArcCandidateCreateId,
    setArcCandidateCreateName: callbacks.setArcCandidateCreateName,
    setArcCandidateCreateSummary: callbacks.setArcCandidateCreateSummary,
    arcCandidateCreateSubmit: callbacks.arcCandidateCreateSubmit,
    setStageMapCreateOpen: callbacks.setStageMapCreateOpen,
    setStageMapCreateArcId: callbacks.setStageMapCreateArcId,
    setStageMapCreateNotes: callbacks.setStageMapCreateNotes,
    setStageMapCreateKinds: callbacks.setStageMapCreateKinds,
    stageMapCreateSubmit: callbacks.stageMapCreateSubmit,
    toggleStageKind: callbacks.toggleStageKind,
    selectArc: callbacks.selectArc,
    deselectArc: callbacks.deselectArc,
    arcUpdateSelection: callbacks.arcUpdateSelection,
    arcDeleteSelection: callbacks.arcDeleteSelection,
  };
}
