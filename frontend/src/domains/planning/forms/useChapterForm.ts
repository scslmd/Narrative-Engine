import { useChapterPlanning } from '../useChapterPlanning';

export function useChapterForm(tab: string) {
  const chapter = useChapterPlanning(tab);
  return {
    chapterCreateOpen: chapter.chapterCreateOpen,
    chapterCreateTitle: chapter.chapterCreateTitle,
    chapterCreateObjective: chapter.chapterCreateObjective,
    chapterCreateConflict: chapter.chapterCreateConflict,
    chapterCreateStakes: chapter.chapterCreateStakes,
    chapterCreateSequenceId: chapter.chapterCreateSequenceId,
    chapterEditOpenId: chapter.chapterEditOpenId,
    chapterEditTitle: chapter.chapterEditTitle,
    chapterEditObjective: chapter.chapterEditObjective,
    chapterEditConflict: chapter.chapterEditConflict,
    chapterEditStakes: chapter.chapterEditStakes,
    setChapterCreateOpen: chapter.setChapterCreateOpen,
    setChapterCreateTitle: chapter.setChapterCreateTitle,
    setChapterCreateObjective: chapter.setChapterCreateObjective,
    setChapterCreateConflict: chapter.setChapterCreateConflict,
    setChapterCreateStakes: chapter.setChapterCreateStakes,
    setChapterCreateSequenceId: chapter.setChapterCreateSequenceId,
    setChapterEditOpenId: chapter.setChapterEditOpenId,
    setChapterEditTitle: chapter.setChapterEditTitle,
    setChapterEditObjective: chapter.setChapterEditObjective,
    setChapterEditConflict: chapter.setChapterEditConflict,
    setChapterEditStakes: chapter.setChapterEditStakes,
  };
}
