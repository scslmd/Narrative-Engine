import { useChapterPackets } from '../useChapterPackets';

export function usePacketForm(tab: string) {
  const packet = useChapterPackets(tab);
  return {
    packetCreateOpen: packet.packetCreateOpen,
    packetCreateChapterId: packet.packetCreateChapterId,
    setPacketCreateOpen: packet.setPacketCreateOpen,
    setPacketCreateChapterId: packet.setPacketCreateChapterId,
  };
}
