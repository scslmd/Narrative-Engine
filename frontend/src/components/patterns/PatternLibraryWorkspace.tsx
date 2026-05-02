import type { PatternEntry } from '../../types/patterns';
import { PatternEntryCard } from './PatternEntryCard';

interface PatternLibraryWorkspaceProps {
  entries: PatternEntry[];
  selectedPatternIds: string[];
  onToggleUse: (patternId: string) => void;
}

export function PatternLibraryWorkspace({
  entries,
  selectedPatternIds,
  onToggleUse,
}: PatternLibraryWorkspaceProps) {
  return (
    <div className="space-y-2">
      <div className="text-sm font-semibold text-slate-900">Pattern Library</div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {entries.map((entry) => (
          <PatternEntryCard
            key={entry.pattern_id}
            entry={entry}
            selected={selectedPatternIds.includes(entry.pattern_id)}
            onToggleUse={onToggleUse}
          />
        ))}
      </div>
    </div>
  );
}
