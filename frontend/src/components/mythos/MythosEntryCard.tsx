import { InlineActions } from '../ui/InlineActions';
import type { MythosEntry } from '../../types/mythos';

interface MythosEntryCardProps {
  entry: MythosEntry;
  selected: boolean;
  onToggleUse: (mythosId: string) => void;
  onDelete?: (mythosId: string) => void;
}

export function MythosEntryCard({ entry, selected, onToggleUse, onDelete }: MythosEntryCardProps) {
  return (
    <div className="rounded border border-slate-200 bg-white p-3">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-slate-900">{entry.name}</div>
        <label className="text-xs flex items-center gap-1">
          <input type="checkbox" checked={selected} onChange={() => onToggleUse(entry.mythos_id)} />
          Use in Generation
        </label>
      </div>
      <div className="text-xs text-slate-500 mt-1">{entry.entry_type}</div>
      <div className="text-sm text-slate-700 mt-1">{entry.summary}</div>
      {onDelete && (
        <div className="mt-2">
          <InlineActions actions={[{ label: 'Delete', variant: 'ghost', danger: true, onClick: () => onDelete(entry.mythos_id) }]} />
        </div>
      )}
    </div>
  );
}
