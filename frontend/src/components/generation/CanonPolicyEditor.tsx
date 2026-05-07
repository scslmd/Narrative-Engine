import type { CanonPolicy } from '../../types/storyGeneration';

interface CanonPolicyEditorProps {
  policy: CanonPolicy;
  onChange: (policy: CanonPolicy) => void;
}

export function CanonPolicyEditor({ policy, onChange }: CanonPolicyEditorProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-semibold text-slate-900 dark:text-slate-100">Continuity Strictness</label>
      <select
        value={policy.continuity_strictness}
        onChange={(event) =>
          onChange({
            ...policy,
            continuity_strictness: event.target.value as CanonPolicy['continuity_strictness'],
          })
        }
        className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"
      >
        <option value="warn">Warn</option>
        <option value="block">Block</option>
        <option value="repair_once">Repair Once</option>
        <option value="repair_twice">Repair Twice</option>
      </select>
    </div>
  );
}
