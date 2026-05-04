import { Section } from './ui';
import { useIsDark } from './hooks';
import type { BeatPlan } from '../../types/planning';
import type { ApiError } from '../../lib/api';
import { ErrorBanner } from '../ui/ErrorBanner';
import { LoadingState } from '../ui/LoadingState';
import { EmptyState } from '../ui/EmptyState';

export interface BeatPlanSectionProps {
  plans: BeatPlan[];
  isLoading: boolean;
  error: ApiError | null;
  onRetry: () => void;
  createOpen: boolean;
  createObjective: string;
  createConflict: string;
  createStakes: string;
  editOpenId: string | null;
  editObjective: string;
  editConflict: string;
  editStakes: string;
  editArcStage: string;
  onCreateOpen: () => void;
  onCreateClose: () => void;
  onCreateObjectiveChange: (value: string) => void;
  onCreateConflictChange: (value: string) => void;
  onCreateStakesChange: (value: string) => void;
  onCreate: () => void;
  onEditOpen: (plan: BeatPlan) => void;
  onEditClose: () => void;
  onEditObjectiveChange: (value: string) => void;
  onEditConflictChange: (value: string) => void;
  onEditStakesChange: (value: string) => void;
  onEditArcStageChange: (value: string) => void;
  onUpdate: (beatId: string) => void;
  onCreateButtonDisabled: boolean;
  onUpdateButtonDisabled: boolean;
}

export function BeatPlanSection({
  plans,
  isLoading,
  createOpen,
  createObjective,
  createConflict,
  createStakes,
  editOpenId,
  editObjective,
  editConflict,
  editStakes,
  editArcStage,
  onCreateOpen,
  onCreateClose,
  onCreateObjectiveChange,
  onCreateConflictChange,
  onCreateStakesChange,
  onCreate,
  onEditOpen,
  onEditClose,
  onEditObjectiveChange,
  onEditConflictChange,
  onEditStakesChange,
  onEditArcStageChange,
  onUpdate,
  onCreateButtonDisabled,
  onUpdateButtonDisabled,
  error,
  onRetry,
}: BeatPlanSectionProps) {
  const isDark = useIsDark();
  const inputClass = `text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`;
  const cardClass = `p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`;

  return (
    <Section
      title="Beats"
      count={plans.length}
      actions={
        <div className="flex justify-end mb-2">
          {!createOpen ? (
            <button
              onClick={onCreateOpen}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-indigo-950 text-indigo-300 hover:bg-indigo-900' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'}`}
            >
              + New Beat
            </button>
          ) : (
            <div className="flex flex-col gap-2 w-80">
              <input type="text" placeholder="Objective" value={createObjective} onChange={(e) => onCreateObjectiveChange(e.target.value)} className={inputClass} />
              <input type="text" placeholder="Conflict" value={createConflict} onChange={(e) => onCreateConflictChange(e.target.value)} className={inputClass} />
              <input type="text" placeholder="Stakes" value={createStakes} onChange={(e) => onCreateStakesChange(e.target.value)} className={inputClass} />
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
            <EmptyState title="No beats yet" description="Define granular story moments with beats." actionLabel="Add Beat" onAction={onCreateOpen} />
          ) : (
            <div className="space-y-2">
              {plans.map((beat) => (
                <div key={beat.beat_id} className={cardClass}>
                  {editOpenId === beat.beat_id ? (
                    <div className="flex flex-col gap-2">
                      <input type="text" value={editObjective} onChange={(e) => onEditObjectiveChange(e.target.value)} className={inputClass} placeholder="Objective" />
                      <input type="text" value={editConflict} onChange={(e) => onEditConflictChange(e.target.value)} className={inputClass} placeholder="Conflict" />
                      <input type="text" value={editStakes} onChange={(e) => onEditStakesChange(e.target.value)} className={inputClass} placeholder="Stakes" />
                      <input type="text" value={editArcStage} onChange={(e) => onEditArcStageChange(e.target.value)} className={inputClass} placeholder="Arc Stage (optional)" />
                      <div className="flex gap-2">
                        <button onClick={() => onUpdate(beat.beat_id)} disabled={!editObjective.trim() || onUpdateButtonDisabled} className="text-xs px-3 py-1 rounded bg-green-600 text-white disabled:opacity-50">Save</button>
                        <button onClick={onEditClose} className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600">Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex justify-between items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{beat.objective}</div>
                        <div className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Conflict: {beat.conflict}</div>
                        <div className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Stakes: {beat.stakes}</div>
                        {beat.arc_stage && <span className={`text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400`}>{beat.arc_stage}</span>}
                      </div>
                      <button onClick={() => onEditOpen(beat)} className={`text-xs px-2 py-0.5 rounded ${isDark ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'}`}>Edit</button>
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
