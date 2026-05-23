import { usePlanningController } from './usePlanningController';

export function useStoryboardPlanning(tab: string) {
  const { state, callbacks } = usePlanningController(tab);
  return {
    storyboardCards: state.storyboardCards,
    cardsLoading: state.cardsLoading,
    cardsError: state.cardsError,
    cardCreateOpen: state.cardCreateOpen,
    cardCreateTitle: state.cardCreateTitle,
    cardCreateContent: state.cardCreateContent,
    cardCreateType: state.cardCreateType,
    cardEditOpenId: state.cardEditOpenId,
    cardEditTitle: state.cardEditTitle,
    cardEditContent: state.cardEditContent,
    cardEditType: state.cardEditType,
    setCardCreateOpen: callbacks.setCardCreateOpen,
    setCardCreateTitle: callbacks.setCardCreateTitle,
    setCardCreateContent: callbacks.setCardCreateContent,
    setCardCreateType: callbacks.setCardCreateType,
    cardCreateSubmit: callbacks.cardCreateSubmit,
    setCardEditOpenId: callbacks.setCardEditOpenId,
    setCardEditTitle: callbacks.setCardEditTitle,
    setCardEditContent: callbacks.setCardEditContent,
    setCardEditType: callbacks.setCardEditType,
    cardUpdateSubmit: callbacks.cardUpdateSubmit,
    cardDelete: callbacks.cardDelete,
    cardReorder: callbacks.cardReorder,
    openEditCard: callbacks.openEditCard,
  };
}
