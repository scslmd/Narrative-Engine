import type { MythosEntry } from '../../types/mythos';

interface MythosEntryEditorProps {
  entry: MythosEntry;
  onChange: (entry: MythosEntry) => void;
}

export function MythosEntryEditor({ entry, onChange }: MythosEntryEditorProps) {
  return (
    <div className="rounded border border-slate-200 bg-white p-3 space-y-2">
      <input
        className="w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
        value={entry.name}
        onChange={(event) => onChange({ ...entry, name: event.target.value })}
      />
      <textarea
        className="w-full rounded border border-slate-300 px-2 py-1.5 text-sm min-h-20"
        value={entry.summary}
        onChange={(event) => onChange({ ...entry, summary: event.target.value })}
      />
    </div>
  );
}
