import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { WorkspaceStatus } from '../planning/ui';
import {
  completeRevisionPass,
  createRevisionPass,
  getRevisionPasses,
  updateRevisionPass,
} from '../../services/revision';
import type { RevisionChecklistItem, RevisionPass, RevisionPassCreateRequest } from '../../types/revision';

interface StudioRevisionPanelProps {
  projectId: string;
}

const passTypeOptions = ['line_edit', 'continuity', 'tone', 'pacing', 'character_voice', 'custom'];

export function StudioRevisionPanel({ projectId }: StudioRevisionPanelProps) {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [newPassType, setNewPassType] = useState('line_edit');
  const [newNotes, setNewNotes] = useState('');

  const { data: passes = [], isLoading, error } = useQuery<RevisionPass[]>({
    queryKey: ['revision-passes', projectId],
    queryFn: () => getRevisionPasses(projectId),
    enabled: Boolean(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (req: RevisionPassCreateRequest) => createRevisionPass(req),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['revision-passes', projectId] });
      setNewPassType('line_edit');
      setNewNotes('');
      setIsCreating(false);
    },
  });

  const completeMutation = useMutation({
    mutationFn: (passId: string) => completeRevisionPass(passId, projectId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['revision-passes', projectId] });
    },
  });

  const toggleChecklistItem = (pass: RevisionPass, itemId: string) => {
    const updatedChecklist = pass.checklist.map((item) =>
      item.item_id === itemId ? { ...item, done: !item.done } : item,
    );
    void updateRevisionPass(pass.pass_id, projectId, { checklist: updatedChecklist }).then(() => {
      void queryClient.invalidateQueries({ queryKey: ['revision-passes', projectId] });
    });
  };

  if (isLoading) {
    return <WorkspaceStatus title="Loading revisions" detail="Fetching revision passes." />;
  }

  if (error) {
    return (
      <WorkspaceStatus
        title="Could not load revisions"
        detail="Revision passes are unavailable."
        tone="error"
      />
    );
  }

  if (isCreating) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex shrink-0 items-center justify-between px-2.5 py-1 border-b border-[var(--border-primary)]">
          <span className="text-[9px] text-[var(--text-tertiary)]">New Revision Pass</span>
          <button
            onClick={() => {
              setIsCreating(false);
              setNewPassType('line_edit');
              setNewNotes('');
            }}
            className="text-[9px] text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
          >
            Cancel
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2.5 space-y-2.5">
          <select
            value={newPassType}
            onChange={(e) => setNewPassType(e.target.value)}
            className="w-full px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-400"
          >
            {passTypeOptions.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>

          <textarea
            placeholder="Notes (optional)"
            value={newNotes}
            onChange={(e) => setNewNotes(e.target.value)}
            rows={4}
            className="w-full px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-400 resize-none"
          />

          <button
            disabled={createMutation.isPending}
            onClick={() =>
              createMutation.mutate({
                project_id: projectId,
                pass_type: newPassType,
                notes: newNotes.trim() || null,
              })
            }
            className="w-full px-2 py-1.5 text-xs font-medium rounded bg-emerald-500 text-white hover:bg-emerald-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {createMutation.isPending ? 'Creating...' : 'Create Pass'}
          </button>
        </div>
      </div>
    );
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300';
      case 'in_progress':
        return 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300';
      default:
        return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400';
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between px-2.5 py-1 border-b border-[var(--border-primary)]">
        <span className="text-[9px] text-[var(--text-tertiary)]">
          {passes.length} passes
        </span>
        <button
          onClick={() => setIsCreating(true)}
          className="px-1.5 py-0.5 bg-emerald-500 text-white text-[9px] font-medium rounded hover:bg-emerald-600 transition-colors"
        >
          New Pass
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        <div className="grid grid-cols-1 gap-2">
          {passes.map((pass) => {
            const doneCount = pass.checklist.filter((i) => i.done).length;
            const totalCount = pass.checklist.length;

            return (
              <div
                key={pass.pass_id}
                className="rounded-lg border p-2.5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-xs font-medium text-slate-900 dark:text-slate-100 truncate">
                      {pass.pass_type}
                    </h3>
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className={`text-[9px] px-1.5 py-0.5 rounded ${statusColor(pass.status)}`}>
                        {pass.status}
                      </span>
                      <span className="text-[9px] text-slate-500 dark:text-slate-400">
                        {doneCount}/{totalCount} checklist
                      </span>
                    </div>
                  </div>

                  {pass.status !== 'completed' && (
                    <button
                      onClick={() => completeMutation.mutate(pass.pass_id)}
                      disabled={completeMutation.isPending}
                      className="shrink-0 ml-2 text-[9px] px-1.5 py-0.5 rounded bg-emerald-500 text-white hover:bg-emerald-600 disabled:opacity-40 transition-colors"
                    >
                      Complete
                    </button>
                  )}
                </div>

                {pass.notes && (
                  <p className="text-[10px] mt-1.5 text-slate-500 dark:text-slate-400 line-clamp-2">
                    {pass.notes}
                  </p>
                )}

                {pass.checklist.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {pass.checklist.map((item) => (
                      <ChecklistRow
                        key={item.item_id}
                        item={item}
                        pass={pass}
                        onToggle={() => toggleChecklistItem(pass, item.item_id)}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {passes.length === 0 && (
          <div className="text-center py-4 text-[10px] text-slate-500 dark:text-slate-400">
            No revision passes. Create one to track editing work.
          </div>
        )}
      </div>
    </div>
  );
}

interface ChecklistRowProps {
  item: RevisionChecklistItem;
  pass: RevisionPass;
  onToggle: () => void;
}

function ChecklistRow({ item, onToggle }: ChecklistRowProps) {
  return (
    <label className="flex items-center gap-1.5 cursor-pointer group">
      <input
        type="checkbox"
        checked={item.done}
        onChange={onToggle}
        className="w-3 h-3 rounded border-slate-300 dark:border-slate-600 text-emerald-500 focus:ring-emerald-400"
      />
      <span
        className={`text-[10px] ${
          item.done
            ? 'line-through text-slate-400 dark:text-slate-500'
            : 'text-slate-600 dark:text-slate-300'
        }`}
      >
        {item.label}
      </span>
    </label>
  );
}
