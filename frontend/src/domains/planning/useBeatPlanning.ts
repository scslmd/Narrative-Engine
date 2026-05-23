import { usePlanningController } from './usePlanningController';

export function useBeatPlanning(tab: string) {
  const { state, callbacks } = usePlanningController(tab);
  return {
    beatPlans: state.beatPlans,
    beatsLoading: state.beatsLoading,
    beatsError: state.beatsError,
    beatCreateOpen: state.beatCreateOpen,
    beatCreateObjective: state.beatCreateObjective,
    beatCreateConflict: state.beatCreateConflict,
    beatCreateStakes: state.beatCreateStakes,
    beatEditOpenId: state.beatEditOpenId,
    beatEditObjective: state.beatEditObjective,
    beatEditConflict: state.beatEditConflict,
    beatEditStakes: state.beatEditStakes,
    beatEditArcStage: state.beatEditArcStage,
    setBeatCreateOpen: callbacks.setBeatCreateOpen,
    setBeatCreateObjective: callbacks.setBeatCreateObjective,
    setBeatCreateConflict: callbacks.setBeatCreateConflict,
    setBeatCreateStakes: callbacks.setBeatCreateStakes,
    beatCreateSubmit: callbacks.beatCreateSubmit,
    setBeatEditOpenId: callbacks.setBeatEditOpenId,
    setBeatEditObjective: callbacks.setBeatEditObjective,
    setBeatEditConflict: callbacks.setBeatEditConflict,
    setBeatEditStakes: callbacks.setBeatEditStakes,
    setBeatEditArcStage: callbacks.setBeatEditArcStage,
    beatUpdateSubmit: callbacks.beatUpdateSubmit,
    openEditBeat: callbacks.openEditBeat,
  };
}
