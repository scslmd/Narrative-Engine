import { usePlanningController } from './usePlanningController';

export function useChapterPackets(tab: string) {
  const { state, callbacks } = usePlanningController(tab);
  return {
    chapterPackets: state.chapterPackets,
    packetsLoading: state.packetsLoading,
    packetsError: state.packetsError,
    packetCreateOpen: state.packetCreateOpen,
    packetCreateChapterId: state.packetCreateChapterId,
    setPacketCreateOpen: callbacks.setPacketCreateOpen,
    setPacketCreateChapterId: callbacks.setPacketCreateChapterId,
    packetCreateSubmit: callbacks.packetCreateSubmit,
  };
}
