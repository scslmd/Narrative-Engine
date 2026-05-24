import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArcBuilder } from '../characters/ArcBuilder';
import { WorkspaceStatus } from '../planning/ui';
import { createArcCandidate, getArcCandidates } from '../../services/arcs';
import type { ArcCandidate, ArcCandidateCreateRequest } from '../../types/arcs';

type ArcEditorMode = 'list' | 'create';

interface StudioArcsPanelProps {
  projectId: string;
}

export function StudioArcsPanel({ projectId }: StudioArcsPanelProps) {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<ArcEditorMode>('list');

  const arcsQuery = useQuery({
    queryKey: ['studio', 'arcs', projectId],
    queryFn: () => getArcCandidates(projectId),
    enabled: Boolean(projectId),
  });

  const arcs = useMemo(
    () => arcsQuery.data ?? [],
    [arcsQuery.data],
  );

  const saveMutation = useMutation({
    mutationFn: (arc: Partial<ArcCandidate>) => {
      const payload: ArcCandidateCreateRequest = {
        project_id: projectId,
        arc_id: arc.arc_id?.trim() || '',
        name: arc.name || '',
        summary: arc.summary || '',
        stage_map_notes: arc.stage_map_notes || [],
        fit_notes: arc.fit_notes || [],
        tags: arc.tags || [],
      };
      return createArcCandidate(payload);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['studio', 'arcs', projectId] });
      setMode('list');
    },
  });

  if (arcsQuery.error) {
    return (
      <WorkspaceStatus
        title="Could not load arcs"
        detail="Arc candidates are unavailable."
        tone="error"
      />
    );
  }

  if (mode === 'list') {
    return (
      <div className="flex h-full flex-col">
        <div className="flex shrink-0 items-center justify-between px-2.5 py-1 border-b border-[var(--border-primary)]">
          <span className="text-[9px] text-[var(--text-tertiary)]">
            {arcs.length} candidates
          </span>
          <button
            onClick={() => setMode('create')}
            className="px-1.5 py-0.5 bg-violet-500 text-white text-[9px] font-medium rounded hover:bg-violet-600 transition-colors"
          >
            New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          <div className="grid grid-cols-1 gap-2">
            {arcs.map((arc) => (
              <div
                key={arc.arc_id}
                className="text-left rounded-lg border p-2.5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-violet-300 dark:hover:border-slate-700 hover:shadow-card transition-all duration-150"
              >
                <h3 className="text-xs font-medium text-slate-900 dark:text-slate-100">
                  {arc.name}
                </h3>
                <p className="text-[10px] mt-0.5 text-slate-500 dark:text-slate-400 line-clamp-2">
                  {arc.summary}
                </p>
                {arc.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {arc.tags.map((tag, i) => (
                      <span
                        key={i}
                        className="px-1 py-0.5 text-[9px] rounded bg-violet-100 dark:bg-violet-900/40 text-violet-800 dark:text-violet-300"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {arcs.length === 0 && (
            <div className="text-center py-4 text-[10px] text-slate-500 dark:text-slate-400">
              No arc candidates configured. Create an arc to start building story threads.
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <ArcBuilder
      projectId={projectId}
      onSave={(arc) => saveMutation.mutate(arc)}
      onCancel={() => setMode('list')}
    />
  );
}
