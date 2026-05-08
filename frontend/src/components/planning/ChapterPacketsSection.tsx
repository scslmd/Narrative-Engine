import { Section } from './ui';
import { useIsDark } from './hooks';
import type { ChapterPacket } from '../../types/planning';
import type { ApiError } from '../../lib/api';
import { ErrorBanner } from '../ui/ErrorBanner';
import { LoadingState } from '../ui/LoadingState';
import { EmptyState } from '../ui/EmptyState';

export interface ChapterPacketsSectionProps {
  packets: ChapterPacket[];
  isLoading: boolean;
  error: ApiError | null;
  onRetry: () => void;
  createOpen: boolean;
  createChapterId: string;
  onCreateOpen: () => void;
  onCreateClose: () => void;
  onCreateChapterIdChange: (value: string) => void;
  onCreate: () => void;
  onCreateButtonDisabled: boolean;
}

export function ChapterPacketsSection({
  packets,
  isLoading,
  createOpen,
  createChapterId,
  onCreateOpen,
  onCreateClose,
  onCreateChapterIdChange,
  onCreate,
  onCreateButtonDisabled,
  error,
  onRetry,
}: ChapterPacketsSectionProps) {
  const isDark = useIsDark();
  const inputClass = `text-sm px-2 py-1 rounded border w-40 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`;

  return (
    <Section
      title="Chapter Packets"
      count={packets.length}
      actions={
        <div className="flex justify-end mb-2">
          {!createOpen ? (
            <button
              onClick={onCreateOpen}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-indigo-950 text-indigo-300 hover:bg-indigo-900' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'}`}
            >
              + New Packet
            </button>
          ) : (
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Chapter ID"
                value={createChapterId}
                onChange={(e) => onCreateChapterIdChange(e.target.value)}
                className={inputClass}
              />
              <button
                onClick={onCreate}
                disabled={onCreateButtonDisabled}
                className="text-xs px-2.5 py-1 rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-40"
              >
                Create
              </button>
              <button onClick={onCreateClose} className={`text-xs px-2 py-1 rounded-md ${isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-700'}`}>
                Cancel
              </button>
            </div>
          )}
        </div>
      }
    >
      {error ? (
        <ErrorBanner error={error} onRetry={onRetry} />
      ) : (
        <LoadingState isLoading={isLoading}>
          {packets.length === 0 ? (
            <EmptyState title="No chapter packets" description="Packets will appear once chapters are ready for drafting." actionLabel="Create Packet" onAction={onCreateOpen} />
          ) : (
            <div className="space-y-2">
              {packets.map((packet) => (
                <div key={packet.packet_id} className={`p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                  <div className="font-medium">{packet.chapter_id}</div>
                  <span className="text-xs text-subtle">{packet.included_reference_ids.length} references included</span>
                </div>
              ))}
            </div>
          )}
        </LoadingState>
      )}
    </Section>
  );
}
