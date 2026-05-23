import { usePlanningController } from './usePlanningController';

export function useChapterPlanning(tab: string) {
  const { state, callbacks } = usePlanningController(tab);
  return {
    chapterPlans: state.chapterPlans,
    chaptersLoading: state.chaptersLoading,
    chaptersError: state.chaptersError,
    chapterCreateOpen: state.chapterCreateOpen,
    chapterCreateTitle: state.chapterCreateTitle,
    chapterCreateObjective: state.chapterCreateObjective,
    chapterCreateConflict: state.chapterCreateConflict,
    chapterCreateStakes: state.chapterCreateStakes,
    chapterCreateSequenceId: state.chapterCreateSequenceId,
    chapterEditOpenId: state.chapterEditOpenId,
    chapterEditTitle: state.chapterEditTitle,
    chapterEditObjective: state.chapterEditObjective,
    chapterEditConflict: state.chapterEditConflict,
    chapterEditStakes: state.chapterEditStakes,
    setChapterCreateOpen: callbacks.setChapterCreateOpen,
    setChapterCreateTitle: callbacks.setChapterCreateTitle,
    setChapterCreateObjective: callbacks.setChapterCreateObjective,
    setChapterCreateConflict: callbacks.setChapterCreateConflict,
    setChapterCreateStakes: callbacks.setChapterCreateStakes,
    setChapterCreateSequenceId: callbacks.setChapterCreateSequenceId,
    chapterCreateSubmit: callbacks.chapterCreateSubmit,
    setChapterEditOpenId: callbacks.setChapterEditOpenId,
    setChapterEditTitle: callbacks.setChapterEditTitle,
    setChapterEditObjective: callbacks.setChapterEditObjective,
    setChapterEditConflict: callbacks.setChapterEditConflict,
    setChapterEditStakes: callbacks.setChapterEditStakes,
    chapterUpdateSubmit: callbacks.chapterUpdateSubmit,
    chapterReorder: callbacks.chapterReorder,
    openEditChapter: callbacks.openEditChapter,
  };
}
