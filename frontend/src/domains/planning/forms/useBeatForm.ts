import { useBeatPlanning } from '../useBeatPlanning';

export function useBeatForm(tab: string) {
  const beat = useBeatPlanning(tab);
  return {
    beatCreateOpen: beat.beatCreateOpen,
    beatCreateObjective: beat.beatCreateObjective,
    beatCreateConflict: beat.beatCreateConflict,
    beatCreateStakes: beat.beatCreateStakes,
    beatEditOpenId: beat.beatEditOpenId,
    beatEditObjective: beat.beatEditObjective,
    beatEditConflict: beat.beatEditConflict,
    beatEditStakes: beat.beatEditStakes,
    beatEditArcStage: beat.beatEditArcStage,
    setBeatCreateOpen: beat.setBeatCreateOpen,
    setBeatCreateObjective: beat.setBeatCreateObjective,
    setBeatCreateConflict: beat.setBeatCreateConflict,
    setBeatCreateStakes: beat.setBeatCreateStakes,
    setBeatEditOpenId: beat.setBeatEditOpenId,
    setBeatEditObjective: beat.setBeatEditObjective,
    setBeatEditConflict: beat.setBeatEditConflict,
    setBeatEditStakes: beat.setBeatEditStakes,
    setBeatEditArcStage: beat.setBeatEditArcStage,
  };
}
