import { useScenePlanning } from '../useScenePlanning';

export function useSceneForm(tab: string) {
  const scene = useScenePlanning(tab);
  return {
    sceneCreateOpen: scene.sceneCreateOpen,
    sceneCreateTitle: scene.sceneCreateTitle,
    sceneCreateObjective: scene.sceneCreateObjective,
    sceneCreateConflict: scene.sceneCreateConflict,
    sceneCreateStakes: scene.sceneCreateStakes,
    sceneCreateChapterId: scene.sceneCreateChapterId,
    sceneEditOpenId: scene.sceneEditOpenId,
    sceneEditTitle: scene.sceneEditTitle,
    sceneEditObjective: scene.sceneEditObjective,
    sceneEditConflict: scene.sceneEditConflict,
    sceneEditStakes: scene.sceneEditStakes,
    setSceneCreateOpen: scene.setSceneCreateOpen,
    setSceneCreateTitle: scene.setSceneCreateTitle,
    setSceneCreateObjective: scene.setSceneCreateObjective,
    setSceneCreateConflict: scene.setSceneCreateConflict,
    setSceneCreateStakes: scene.setSceneCreateStakes,
    setSceneCreateChapterId: scene.setSceneCreateChapterId,
    setSceneEditOpenId: scene.setSceneEditOpenId,
    setSceneEditTitle: scene.setSceneEditTitle,
    setSceneEditObjective: scene.setSceneEditObjective,
    setSceneEditConflict: scene.setSceneEditConflict,
    setSceneEditStakes: scene.setSceneEditStakes,
  };
}
