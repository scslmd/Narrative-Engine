import type { PatternEntry } from '../../types/patterns';
import { InlineActions } from '../ui/InlineActions';
import { PatternModeSelector } from './PatternModeSelector';

interface PatternEntryCardProps {
  entry: PatternEntry;
  selected: boolean;
  onToggleUse: (patternId: string) => void;
  onDelete?: (patternId: string) => void;
}

export function PatternEntryCard({ entry, selected, onToggleUse, onDelete }: PatternEntryCardProps) {
  return (
    <div className="rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">{entry.name}</div>
        <label className="text-xs flex items-center gap-1">
          <input type="checkbox" checked={selected} onChange={() => onToggleUse(entry.pattern_id)} />
          Use in Generation
        </label>
      </div>
      <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">{entry.pattern_type}</div>
      <div className="text-sm text-slate-700 dark:text-slate-300 mt-1">{entry.summary}</div>
      <div className="mt-2">
        <PatternModeSelector modes={entry.generation_modes} />
      </div>
      {onDelete && (
        <div className="mt-2">
          <InlineActions actions={[{ label: 'Delete', variant: 'ghost', danger: true, onClick: () => onDelete(entry.pattern_id) }]} />
        </div>
      )}
    </div>
  );
}
