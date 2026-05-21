import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getBeatPlans, getSequencePlans } from '../../services/planning';
import type { BeatPlan, SequencePlan } from '../../types/planning';
import { WorkspaceStatus } from '../planning/ui';

interface StudioStructurePanelProps {
  projectId: string;
}

const STATUS_COLORS: Record<string, string> = {
  completed: 'bg-emerald-500',
  in_progress: 'bg-amber-500',
  current: 'bg-amber-500',
  planned: 'bg-slate-400 dark:bg-slate-600',
  pending: 'bg-slate-400 dark:bg-slate-600',
  draft: 'bg-blue-500',
  review: 'bg-purple-500',
};

const STATUS_LABELS: Record<string, string> = {
  completed: 'Done',
  in_progress: 'In Progress',
  current: 'Current',
  planned: 'Planned',
  pending: 'Pending',
  draft: 'Draft',
  review: 'Review',
};

function BeatIndicator({ beat }: { beat: BeatPlan }) {
  const color = STATUS_COLORS[beat.status] || 'bg-slate-400 dark:bg-slate-600';
  const label = STATUS_LABELS[beat.status] || beat.status;

  return (
    <div className="group relative" title={`${beat.objective} (${label})`}>
      <div className={`h-2 w-full rounded-full ${color} transition-all group-hover:opacity-80`} />
      {beat.active_character_ids.length > 0 && (
        <div className="pointer-events-none absolute inset-x-0 -bottom-6 z-10 opacity-0 transition-opacity group-hover:opacity-100">
          <div className="rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] px-2 py-1 text-[10px] text-[var(--text-secondary)] shadow-lg">
            <div className="font-medium text-[var(--text-primary)]">{beat.objective}</div>
            <div>{beat.active_character_ids.join(', ')}</div>
          </div>
        </div>
      )}
    </div>
  );
}

function SequenceBlock({ sequence, beats }: { sequence: SequencePlan; beats: BeatPlan[] }) {
  const seqBeats = beats.filter((b) => sequence.beat_ids.includes(b.beat_id));
  const completedCount = seqBeats.filter((b) => b.status === 'completed').length;
  const progress = seqBeats.length > 0 ? (completedCount / seqBeats.length) * 100 : 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-[var(--text-primary)]">{sequence.title}</h4>
        <span className="text-[10px] text-[var(--text-tertiary)]">
          {completedCount}/{seqBeats.length} beats
        </span>
      </div>
      <div className="flex gap-1">
        {seqBeats.map((beat) => (
          <div key={beat.beat_id} className="flex-1">
            <BeatIndicator beat={beat} />
          </div>
        ))}
        {seqBeats.length === 0 && (
          <div className="h-2 w-full rounded-full bg-slate-200 dark:bg-slate-700" />
        )}
      </div>
      <div className="h-1 w-full rounded-full bg-slate-200 dark:bg-slate-700">
        <div
          className="h-full rounded-full bg-emerald-500 transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

export function StudioStructurePanel({ projectId }: StudioStructurePanelProps) {
  const sequencesQuery = useQuery({
    queryKey: ['studio', 'structure', 'sequences', projectId],
    queryFn: () => getSequencePlans(projectId),
    enabled: Boolean(projectId),
  });

  const beatsQuery = useQuery({
    queryKey: ['studio', 'structure', 'beats', projectId],
    queryFn: () => getBeatPlans(projectId),
    enabled: Boolean(projectId),
  });

  const sequences = useMemo(
    () => (sequencesQuery.data as SequencePlan[] | undefined) ?? [],
    [sequencesQuery.data],
  );

  const beats = useMemo(
    () => (beatsQuery.data as BeatPlan[] | undefined) ?? [],
    [beatsQuery.data],
  );

  const isLoading = sequencesQuery.isLoading || beatsQuery.isLoading;
  const error = sequencesQuery.error || beatsQuery.error;

  if (isLoading) {
    return <WorkspaceStatus title="Loading structure" detail="Fetching story framework..." />;
  }

  if (error) {
    return (
      <WorkspaceStatus
        title="Could not load structure"
        detail="Story framework data is unavailable."
        tone="error"
      />
    );
  }

  const totalBeats = beats.length;
  const completedBeats = beats.filter((b) => b.status === 'completed').length;
  const overallProgress = totalBeats > 0 ? (completedBeats / totalBeats) * 100 : 0;

  return (
    <div data-structure-panel className="space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">Structure</h3>
          <p className="text-[10px] text-[var(--text-tertiary)]">
            {sequences.length} sequences · {totalBeats} beats
          </p>
        </div>
        <div className="text-right">
          <div className="text-[10px] font-medium text-[var(--text-secondary)]">
            {Math.round(overallProgress)}%
          </div>
        </div>
      </div>

      <div className="h-1 w-full rounded-full bg-slate-200 dark:bg-slate-700">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all"
          style={{ width: `${overallProgress}%` }}
        />
      </div>

      {sequences.length === 0 && beats.length === 0 ? (
        <div className="py-6 text-center">
          <p className="text-xs text-[var(--text-tertiary)]">
            No structure planned yet.
          </p>
          <p className="mt-1 text-[10px] text-[var(--text-tertiary)]">
            Create sequences and beats to track story progress.
          </p>
        </div>
      ) : sequences.length > 0 ? (
        <div className="space-y-2">
          {sequences.map((seq) => (
            <SequenceBlock key={seq.sequence_id} sequence={seq} beats={beats} />
          ))}
        </div>
      ) : (
        <div className="space-y-1.5">
          <p className="text-[10px] font-medium text-[var(--text-secondary)]">Standalone Beats</p>
          {beats.map((beat) => (
            <div key={beat.beat_id} className="flex items-center gap-1.5">
              <div className="w-2">
                <BeatIndicator beat={beat} />
              </div>
              <span className="text-[10px] text-[var(--text-secondary)] truncate">
                {beat.objective}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
