import type { MythosEntryType } from '../../types/mythos';

interface MythosTypeFilterProps {
  value: MythosEntryType | 'all';
  onChange: (value: MythosEntryType | 'all') => void;
}

const types: Array<MythosEntryType | 'all'> = ['all', 'archetype', 'motif', 'cosmic_rule', 'symbol', 'ritual', 'deity', 'cycle', 'theme'];

export function MythosTypeFilter({ value, onChange }: MythosTypeFilterProps) {
  return (
    <select
      className="rounded border border-slate-300 dark:border-slate-600 px-2 py-1.5 text-sm"
      value={value}
      onChange={(event) => onChange(event.target.value as MythosEntryType | 'all')}
    >
      {types.map((type) => (
        <option key={type} value={type}>{type}</option>
      ))}
    </select>
  );
}
