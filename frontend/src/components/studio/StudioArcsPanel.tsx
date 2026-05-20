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
      <div className="rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] p-5">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Arcs</h2>
            <p className="text-sm mt-0.5 text-slate-500 dark:text-slate-400">
              {arcs.length} candidates
            </p>
          </div>
          <button
            onClick={() => setMode('create')}
            className="px-3 py-1.5 bg-gradient-to-r from-violet-500 to-violet-600 text-white text-xs font-medium rounded-lg hover:from-violet-600 hover:to-violet-700 shadow-sm transition-all"
          >
            New Arc
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {arcs.map((arc) => (
            <div
              key={arc.arc_id}
              className="text-left rounded-lg border p-4 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-violet-300 dark:hover:border-slate-700 hover:shadow-card transition-all duration-150"
            >
              <h3 className="font-medium text-slate-900 dark:text-slate-100">
                {arc.name}
              </h3>
              <p className="text-sm mt-1 text-slate-500 dark:text-slate-400 line-clamp-2">
                {arc.summary}
              </p>
              {arc.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {arc.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.5 text-xs rounded bg-violet-100 dark:bg-violet-900/40 text-violet-800 dark:text-violet-300"
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
          <div className="text-center py-8 text-sm text-slate-500 dark:text-slate-400">
            No arc candidates configured. Create an arc to start building story threads.
          </div>
        )}
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
