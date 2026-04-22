import { ChevronUp, ChevronDown } from 'lucide-react';
import { Section, EmptyState, WorkspaceStatus } from './ui';
import { useIsDark } from './hooks';
import type { SequencePlan } from '../../types/planning';

export interface SequencePlanSectionProps {
  plans: SequencePlan[];
  isLoading: boolean;
  createOpen: boolean;
  createTitle: string;
  createSummary: string;
  editOpenId: string | null;
  editTitle: string;
  editSummary: string;
  onCreateOpen: () => void;
  onCreateClose: () => void;
  onCreateTitleChange: (value: string) => void;
  onCreateSummaryChange: (value: string) => void;
  onCreate: () => void;
  onEditOpen: (plan: SequencePlan) => void;
  onEditClose: () => void;
  onEditTitleChange: (value: string) => void;
  onEditSummaryChange: (value: string) => void;
  onUpdate: (sequenceId: string) => void;
  onReorderUp: (index: number) => void;
  onReorderDown: (index: number) => void;
  onCreateButtonDisabled: boolean;
  onUpdateButtonDisabled: boolean;
}

export function SequencePlanSection({
  plans,
  isLoading,
  createOpen,
  createTitle,
  createSummary,
  editOpenId,
  editTitle,
  editSummary,
  onCreateOpen,
  onCreateClose,
  onCreateTitleChange,
  onCreateSummaryChange,
  onCreate,
  onEditOpen,
  onEditClose,
  onEditTitleChange,
  onEditSummaryChange,
  onUpdate,
  onReorderUp,
  onReorderDown,
  onCreateButtonDisabled,
  onUpdateButtonDisabled,
}: SequencePlanSectionProps) {
  const isDark = useIsDark();
  const inputClass = `text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`;
  const createInputClass = `text-sm px-2 py-1 rounded border w-48 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`;
  const cardClass = `p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`;
  const reorderClass = (index: number, isDown: boolean) =>
    `p-0.5 rounded transition-colors ${index === (isDown ? plans.length - 1 : 0) ? 'opacity-20 cursor-not-allowed' : isDark ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'}`;

  return (
    <Section
      title="Sequences"
      count={plans.length}
      actions={
        <div className="flex justify-end mb-2">
          {!createOpen ? (
            <button
              onClick={onCreateOpen}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-indigo-950 text-indigo-300 hover:bg-indigo-900' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'}`}
            >
              + New Sequence
            </button>
          ) : (
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Sequence title"
                value={createTitle}
                onChange={(e) => onCreateTitleChange(e.target.value)}
                className={`${createInputClass} w-40`}
              />
              <input
                type="text"
                placeholder="Summary (optional)"
                value={createSummary}
                onChange={(e) => onCreateSummaryChange(e.target.value)}
                className={createInputClass}
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
      {isLoading ? (
        <WorkspaceStatus title="Loading sequences" detail="Fetching sequence plans..." />
      ) : plans.length === 0 ? (
        <EmptyState text="No sequence plans configured. Create a sequence to define the high-level story structure." />
      ) : (
        <div className="space-y-2">
          {plans.map((seq, index) => (
            <div key={seq.sequence_id} className={cardClass}>
              {editOpenId === seq.sequence_id ? (
                <div className="flex flex-col gap-2">
                  <input type="text" value={editTitle} onChange={(e) => onEditTitleChange(e.target.value)} className={inputClass} />
                  <input type="text" value={editSummary} onChange={(e) => onEditSummaryChange(e.target.value)} className={inputClass} />
                  <div className="flex gap-2">
                    <button onClick={() => onUpdate(seq.sequence_id)} disabled={!editTitle.trim() || onUpdateButtonDisabled} className="text-xs px-3 py-1 rounded bg-green-600 text-white disabled:opacity-50">Save</button>
                    <button onClick={onEditClose} className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600">Cancel</button>
                  </div>
                </div>
              ) : (
                <div className="flex justify-between items-start gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{seq.title}</div>
                    {seq.summary && <p className={`text-sm mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{seq.summary}</p>}
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                      onClick={() => onReorderUp(index)}
                      disabled={index === 0}
                      className={reorderClass(index, false)}
                    >
                      <ChevronUp className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => onReorderDown(index)}
                      disabled={index === plans.length - 1}
                      className={reorderClass(index, true)}
                    >
                      <ChevronDown className="w-3 h-3" />
                    </button>
                    <button onClick={() => onEditOpen(seq)} className={`text-xs px-2 py-0.5 rounded ${isDark ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'}`}>Edit</button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}
