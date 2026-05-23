import { usePlanningController } from './usePlanningController';

export function useScenePlanning(tab: string) {
  const { state, callbacks } = usePlanningController(tab);
  return {
    scenePlans: state.scenePlans,
    scenesLoading: state.scenesLoading,
    scenesError: state.scenesError,
    sceneCreateOpen: state.sceneCreateOpen,
    sceneCreateTitle: state.sceneCreateTitle,
    sceneCreateObjective: state.sceneCreateObjective,
    sceneCreateConflict: state.sceneCreateConflict,
    sceneCreateStakes: state.sceneCreateStakes,
    sceneCreateChapterId: state.sceneCreateChapterId,
    sceneEditOpenId: state.sceneEditOpenId,
    sceneEditTitle: state.sceneEditTitle,
    sceneEditObjective: state.sceneEditObjective,
    sceneEditConflict: state.sceneEditConflict,
    sceneEditStakes: state.sceneEditStakes,
    setSceneCreateOpen: callbacks.setSceneCreateOpen,
    setSceneCreateTitle: callbacks.setSceneCreateTitle,
    setSceneCreateObjective: callbacks.setSceneCreateObjective,
    setSceneCreateConflict: callbacks.setSceneCreateConflict,
    setSceneCreateStakes: callbacks.setSceneCreateStakes,
    setSceneCreateChapterId: callbacks.setSceneCreateChapterId,
    sceneCreateSubmit: callbacks.sceneCreateSubmit,
    setSceneEditOpenId: callbacks.setSceneEditOpenId,
    setSceneEditTitle: callbacks.setSceneEditTitle,
    setSceneEditObjective: callbacks.setSceneEditObjective,
    setSceneEditConflict: callbacks.setSceneEditConflict,
    setSceneEditStakes: callbacks.setSceneEditStakes,
    sceneUpdateSubmit: callbacks.sceneUpdateSubmit,
    sceneReorder: callbacks.sceneReorder,
    openEditScene: callbacks.openEditScene,
  };
}
