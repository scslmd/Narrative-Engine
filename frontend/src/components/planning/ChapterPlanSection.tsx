import { ChevronUp, ChevronDown } from 'lucide-react';
import { Section } from './ui';
import { useIsDark } from './hooks';
import type { ChapterPlan } from '../../types/planning';
import type { ApiError } from '../../lib/api';
import { ErrorBanner } from '../ui/ErrorBanner';
import { LoadingState } from '../ui/LoadingState';
import { EmptyState } from '../ui/EmptyState';

export interface ChapterPlanSectionProps {
  plans: ChapterPlan[];
  isLoading: boolean;
  error: ApiError | null;
  onRetry: () => void;
  createOpen: boolean;
  createTitle: string;
  createObjective: string;
  createConflict: string;
  createStakes: string;
  createSequenceId: string;
  editOpenId: string | null;
  editTitle: string;
  editObjective: string;
  editConflict: string;
  editStakes: string;
  onCreateOpen: () => void;
  onCreateClose: () => void;
  onCreateTitleChange: (value: string) => void;
  onCreateObjectiveChange: (value: string) => void;
  onCreateConflictChange: (value: string) => void;
  onCreateStakesChange: (value: string) => void;
  onCreateSequenceIdChange: (value: string) => void;
  onCreate: () => void;
  onEditOpen: (plan: ChapterPlan) => void;
  onEditClose: () => void;
  onEditTitleChange: (value: string) => void;
  onEditObjectiveChange: (value: string) => void;
  onEditConflictChange: (value: string) => void;
  onEditStakesChange: (value: string) => void;
  onUpdate: (chapterId: string) => void;
  onReorderUp: (index: number) => void;
  onReorderDown: (index: number) => void;
  onCreateButtonDisabled: boolean;
  onUpdateButtonDisabled: boolean;
}

export function ChapterPlanSection({
  plans,
  isLoading,
  createOpen,
  createTitle,
  createObjective,
  createConflict,
  createStakes,
  createSequenceId,
  editOpenId,
  editTitle,
  editObjective,
  editConflict,
  editStakes,
  onCreateOpen,
  onCreateClose,
  onCreateTitleChange,
  onCreateObjectiveChange,
  onCreateConflictChange,
  onCreateStakesChange,
  onCreateSequenceIdChange,
  onCreate,
  onEditOpen,
  onEditClose,
  onEditTitleChange,
  onEditObjectiveChange,
  onEditConflictChange,
  onEditStakesChange,
  onUpdate,
  onReorderUp,
  onReorderDown,
  onCreateButtonDisabled,
  onUpdateButtonDisabled,
  error,
  onRetry,
}: ChapterPlanSectionProps) {
  const isDark = useIsDark();
  const inputClass = `text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`;
  const cardClass = `p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`;
  const reorderClass = (index: number, isDown: boolean) =>
    `p-0.5 rounded transition-colors ${index === (isDown ? plans.length - 1 : 0) ? 'opacity-20 cursor-not-allowed' : isDark ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'}`;

  return (
    <Section
      title="Chapters"
      count={plans.length}
      actions={
        <div className="flex justify-end mb-2">
          {!createOpen ? (
            <button
              onClick={onCreateOpen}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-indigo-950 text-indigo-300 hover:bg-indigo-900' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'}`}
            >
              + New Chapter
            </button>
          ) : (
            <div className="flex flex-col gap-2 w-80">
              <input type="text" placeholder="Chapter title" value={createTitle} onChange={(e) => onCreateTitleChange(e.target.value)} className={inputClass} />
              <input type="text" placeholder="Objective" value={createObjective} onChange={(e) => onCreateObjectiveChange(e.target.value)} className={inputClass} />
              <input type="text" placeholder="Conflict" value={createConflict} onChange={(e) => onCreateConflictChange(e.target.value)} className={inputClass} />
              <input type="text" placeholder="Stakes" value={createStakes} onChange={(e) => onCreateStakesChange(e.target.value)} className={inputClass} />
              <input type="text" placeholder="Sequence ID (optional)" value={createSequenceId} onChange={(e) => onCreateSequenceIdChange(e.target.value)} className={inputClass} />
              <div className="flex gap-2">
                <button onClick={onCreate} disabled={onCreateButtonDisabled} className="text-xs px-3 py-1 rounded bg-green-600 text-white disabled:opacity-50">Create</button>
                <button onClick={onCreateClose} className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600">Cancel</button>
              </div>
            </div>
          )}
        </div>
      }
    >
      {error ? (
        <ErrorBanner error={error} onRetry={onRetry} />
      ) : (
        <LoadingState isLoading={isLoading}>
          {plans.length === 0 ? (
            <EmptyState title="No chapters yet" description="Define story structure with chapters." actionLabel="Add Chapter" onAction={onCreateOpen} />
          ) : (
            <div className="space-y-2">
              {plans.map((chap, index) => (
                <div key={chap.chapter_id} className={cardClass}>
                  {editOpenId === chap.chapter_id ? (
                    <div className="flex flex-col gap-2">
                      <input type="text" value={editTitle} onChange={(e) => onEditTitleChange(e.target.value)} className={inputClass} placeholder="Title" />
                      <input type="text" value={editObjective} onChange={(e) => onEditObjectiveChange(e.target.value)} className={inputClass} placeholder="Objective" />
                      <input type="text" value={editConflict} onChange={(e) => onEditConflictChange(e.target.value)} className={inputClass} placeholder="Conflict" />
                      <input type="text" value={editStakes} onChange={(e) => onEditStakesChange(e.target.value)} className={inputClass} placeholder="Stakes" />
                      {chap.sequence_id && <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Sequence: {chap.sequence_id}</span>}
                      <div className="flex gap-2">
                        <button onClick={() => onUpdate(chap.chapter_id)} disabled={!editTitle.trim() || !editObjective.trim() || onUpdateButtonDisabled} className="text-xs px-3 py-1 rounded bg-green-600 text-white disabled:opacity-50">Save</button>
                        <button onClick={onEditClose} className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600">Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex justify-between items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{chap.title}</div>
                        {chap.sequence_id && <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Sequence: {chap.sequence_id}</span>}
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
                        <button onClick={() => onEditOpen(chap)} className={`text-xs px-2 py-0.5 rounded ${isDark ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'}`}>Edit</button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </LoadingState>
      )}
    </Section>
  );
}
