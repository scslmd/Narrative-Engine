import type { PatternEntry } from '../../types/patterns';
import { PatternModeSelector } from './PatternModeSelector';

interface PatternEntryCardProps {
  entry: PatternEntry;
  selected: boolean;
  onToggleUse: (patternId: string) => void;
}

export function PatternEntryCard({ entry, selected, onToggleUse }: PatternEntryCardProps) {
  return (
    <div className="rounded border border-slate-200 bg-white p-3">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-slate-900">{entry.name}</div>
        <label className="text-xs flex items-center gap-1">
          <input type="checkbox" checked={selected} onChange={() => onToggleUse(entry.pattern_id)} />
          Use in Generation
        </label>
      </div>
      <div className="text-xs text-slate-500 mt-1">{entry.pattern_type}</div>
      <div className="text-sm text-slate-700 mt-1">{entry.summary}</div>
      <div className="mt-2">
        <PatternModeSelector modes={entry.generation_modes} />
      </div>
    </div>
  );
}
