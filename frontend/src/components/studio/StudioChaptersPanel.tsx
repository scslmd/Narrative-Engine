import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getChapterPlans, getChapterPackets } from '../../services/planning';
import type { ChapterPlan, ChapterPacket } from '../../types/planning';
import { WorkspaceStatus } from '../planning/ui';

interface StudioChaptersPanelProps {
  projectId: string;
}

const CHAPTER_STATUS_COLORS: Record<string, string> = {
  completed: 'border-l-emerald-500',
  in_progress: 'border-l-amber-500',
  current: 'border-l-amber-500',
  planned: 'border-l-slate-400 dark:border-l-slate-600',
  pending: 'border-l-slate-400 dark:border-l-slate-600',
  draft: 'border-l-blue-500',
  review: 'border-l-purple-500',
};

const CHAPTER_STATUS_DOTS: Record<string, string> = {
  completed: 'bg-emerald-500',
  in_progress: 'bg-amber-500',
  current: 'bg-amber-500',
  planned: 'bg-slate-400 dark:bg-slate-600',
  pending: 'bg-slate-400 dark:bg-slate-600',
  draft: 'bg-blue-500',
  review: 'bg-purple-500',
};

function ChapterRow({
  chapter,
  packet,
  isSelected,
  onSelect,
}: {
  chapter: ChapterPlan;
  packet?: ChapterPacket;
  isSelected: boolean;
  onSelect: (chapterId: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const borderColor = CHAPTER_STATUS_COLORS[chapter.status] || 'border-l-slate-300 dark:border-l-slate-700';
  const dotColor = CHAPTER_STATUS_DOTS[chapter.status] || 'bg-slate-400';

  return (
    <div
      className={`cursor-pointer rounded-lg border border-[var(--border-primary)] border-l-4 ${borderColor} bg-[var(--bg-secondary)] transition-all hover:bg-[var(--bg-primary)] ${
        isSelected ? 'ring-1 ring-[var(--accent-primary)]' : ''
      }`}
      onClick={() => onSelect(chapter.chapter_id)}
    >
      <div className="flex items-center gap-2 px-2.5 py-1.5">
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
          className="flex h-4 w-4 items-center justify-center text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
        >
          {expanded ? '▾' : '▸'}
        </button>
        <div className={`h-2 w-2 rounded-full ${dotColor}`} />
        <div className="min-w-0 flex-1">
          <div className="truncate text-xs font-medium text-[var(--text-primary)]">
            {chapter.title || `Chapter ${chapter.chapter_id}`}
          </div>
          <div className="truncate text-[10px] text-[var(--text-tertiary)]">
            {chapter.objective || 'No objective set'}
          </div>
        </div>
        {packet && (
          <span className="shrink-0 rounded bg-blue-100 px-1.5 py-0.5 text-[9px] font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
            packet
          </span>
        )}
      </div>

      {expanded && (
         <div className="border-t border-[var(--border-primary)] px-2.5 py-1.5 space-y-1">
          {chapter.summary && (
            <p className="text-[10px] leading-relaxed text-[var(--text-secondary)]">
              {chapter.summary}
            </p>
          )}
          {chapter.conflict && (
            <p className="text-[10px] leading-relaxed text-[var(--text-secondary)]">
              <span className="font-medium text-[var(--text-tertiary)]">Conflict: </span>
              {chapter.conflict}
            </p>
          )}
          {chapter.stakes && (
            <p className="text-[10px] leading-relaxed text-[var(--text-secondary)]">
              <span className="font-medium text-[var(--text-tertiary)]">Stakes: </span>
              {chapter.stakes}
            </p>
          )}
          {chapter.active_character_ids.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {chapter.active_character_ids.map((cid) => (
                <span
                  key={cid}
                  className="rounded bg-[var(--bg-primary)] px-1.5 py-0.5 text-[9px] text-[var(--text-secondary)]"
                >
                  {cid}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function StudioChaptersPanel({ projectId }: StudioChaptersPanelProps) {
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);

  const chaptersQuery = useQuery({
    queryKey: ['studio', 'chapters', projectId],
    queryFn: () => getChapterPlans(projectId),
    enabled: Boolean(projectId),
  });

  const packetsQuery = useQuery({
    queryKey: ['studio', 'chapter-packets', projectId],
    queryFn: () => getChapterPackets(projectId),
    enabled: Boolean(projectId),
  });

  const chapters = useMemo(
    () => (chaptersQuery.data as ChapterPlan[] | undefined) ?? [],
    [chaptersQuery.data],
  );

  const packets = useMemo(
    () => (packetsQuery.data as ChapterPacket[] | undefined) ?? [],
    [packetsQuery.data],
  );

  const packetMap = useMemo(() => {
    const map: Record<string, ChapterPacket> = {};
    for (const packet of packets) {
      map[packet.chapter_id] = packet;
    }
    return map;
  }, [packets]);

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const ch of chapters) {
      counts[ch.status] = (counts[ch.status] || 0) + 1;
    }
    return counts;
  }, [chapters]);

  const isLoading = chaptersQuery.isLoading;
  const error = chaptersQuery.error;

  if (isLoading) {
    return <WorkspaceStatus title="Loading chapters" detail="Fetching chapter plans..." />;
  }

  if (error) {
    return (
      <WorkspaceStatus
        title="Could not load chapters"
        detail="Chapter plans are unavailable."
        tone="error"
      />
    );
  }

  return (
    <div data-chapters-panel className="space-y-1.5">
       <div className="flex items-center gap-1.5">
         {Object.entries(statusCounts).map(([status, count]) => (
           <span key={status} className="flex items-center gap-0.5 text-[9px] text-[var(--text-tertiary)]">
             <div className={`h-1 w-1 rounded-full ${CHAPTER_STATUS_DOTS[status] || 'bg-slate-400'}`} />
             {count}
           </span>
         ))}
       </div>

     {chapters.length === 0 ? (
         <div className="py-3 text-center">
           <p className="text-[10px] text-[var(--text-tertiary)]">No chapters planned yet.</p>
           <p className="mt-0.5 text-[9px] text-[var(--text-tertiary)]">
             Create chapter plans to structure your story.
           </p>
         </div>
      ) : (
        <div className="space-y-1 max-h-[400px] overflow-y-auto">
          {chapters.map((chapter) => (
            <ChapterRow
              key={chapter.chapter_id}
              chapter={chapter}
              packet={packetMap[chapter.chapter_id]}
              isSelected={selectedChapterId === chapter.chapter_id}
              onSelect={setSelectedChapterId}
            />
          ))}
        </div>
      )}
    </div>
  );
}
