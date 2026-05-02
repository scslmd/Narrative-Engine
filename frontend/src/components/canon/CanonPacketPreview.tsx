import type { CanonGenerationPacket } from '../../types/storyGeneration';

interface CanonPacketPreviewProps {
  packet: CanonGenerationPacket | null;
}

export function CanonPacketPreview({ packet }: CanonPacketPreviewProps) {
  if (!packet) {
    return <div className="rounded border border-slate-200 bg-white p-3 text-sm text-slate-500">No packet preview.</div>;
  }
  return (
    <div className="rounded border border-indigo-200 bg-indigo-50 p-3 text-sm text-indigo-900">
      <div className="font-semibold mb-1">Packet {packet.packet_id}</div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-1">
        <span>Characters: {packet.characters.length}</span>
        <span>World: {packet.world_bible.length}</span>
        <span>Mythos: {packet.mythos_entries.length}</span>
        <span>Patterns: {packet.pattern_entries.length}</span>
      </div>
    </div>
  );
}
