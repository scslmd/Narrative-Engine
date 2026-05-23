import { useStoryboardPlanning } from '../useStoryboardPlanning';

export function useStoryboardForm(tab: string) {
  const storyboard = useStoryboardPlanning(tab);
  return {
    cardCreateOpen: storyboard.cardCreateOpen,
    cardCreateTitle: storyboard.cardCreateTitle,
    cardCreateContent: storyboard.cardCreateContent,
    cardCreateType: storyboard.cardCreateType,
    cardEditOpenId: storyboard.cardEditOpenId,
    cardEditTitle: storyboard.cardEditTitle,
    cardEditContent: storyboard.cardEditContent,
    cardEditType: storyboard.cardEditType,
    setCardCreateOpen: storyboard.setCardCreateOpen,
    setCardCreateTitle: storyboard.setCardCreateTitle,
    setCardCreateContent: storyboard.setCardCreateContent,
    setCardCreateType: storyboard.setCardCreateType,
    setCardEditOpenId: storyboard.setCardEditOpenId,
    setCardEditTitle: storyboard.setCardEditTitle,
    setCardEditContent: storyboard.setCardEditContent,
    setCardEditType: storyboard.setCardEditType,
  };
}
