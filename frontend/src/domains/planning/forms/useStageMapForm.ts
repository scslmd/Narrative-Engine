import { useArcPlanning } from '../useArcPlanning';

export function useStageMapForm(tab: string) {
  const arcs = useArcPlanning(tab);
  return {
    stageMapCreateOpen: arcs.stageMapCreateOpen,
    stageMapCreateArcId: arcs.stageMapCreateArcId,
    stageMapCreateNotes: arcs.stageMapCreateNotes,
    stageMapCreateKinds: arcs.stageMapCreateKinds,
    setStageMapCreateOpen: arcs.setStageMapCreateOpen,
    setStageMapCreateArcId: arcs.setStageMapCreateArcId,
    setStageMapCreateNotes: arcs.setStageMapCreateNotes,
    setStageMapCreateKinds: arcs.setStageMapCreateKinds,
  };
}
