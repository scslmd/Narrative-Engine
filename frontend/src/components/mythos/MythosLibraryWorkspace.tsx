import { useMemo, useState } from 'react';
import type { MythosEntry, MythosEntryType } from '../../types/mythos';
import { MythosEntryCard } from './MythosEntryCard';
import { MythosTypeFilter } from './MythosTypeFilter';

interface MythosLibraryWorkspaceProps {
  entries: MythosEntry[];
  selectedMythosIds: string[];
  onToggleUse: (mythosId: string) => void;
}

export function MythosLibraryWorkspace({
  entries,
  selectedMythosIds,
  onToggleUse,
}: MythosLibraryWorkspaceProps) {
  const [filter, setFilter] = useState<MythosEntryType | 'all'>('all');
  const filtered = useMemo(
    () => (filter === 'all' ? entries : entries.filter((entry) => entry.entry_type === filter)),
    [entries, filter],
  );
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-slate-900">Mythos Library</div>
        <MythosTypeFilter value={filter} onChange={setFilter} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {filtered.map((entry) => (
          <MythosEntryCard
            key={entry.mythos_id}
            entry={entry}
            selected={selectedMythosIds.includes(entry.mythos_id)}
            onToggleUse={onToggleUse}
          />
        ))}
      </div>
    </div>
  );
}
