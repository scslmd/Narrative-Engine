import type { CanonPolicy } from '../../types/storyGeneration';

interface CanonGenerationRulesEditorProps {
  policy: CanonPolicy;
  onChange: (policy: CanonPolicy) => void;
}

export function CanonGenerationRulesEditor({ policy, onChange }: CanonGenerationRulesEditorProps) {
  return (
    <div className="rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3 space-y-2">
      <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">Generation Rules</div>
      <label className="text-xs text-slate-600 dark:text-slate-400 block">
        Continuity strictness
        <select
          className="mt-1 w-full rounded border border-slate-300 dark:border-slate-600 px-2 py-1 text-sm"
          value={policy.continuity_strictness}
          onChange={(event) =>
            onChange({ ...policy, continuity_strictness: event.target.value as CanonPolicy['continuity_strictness'] })
          }
        >
          <option value="warn">warn</option>
          <option value="block">block</option>
          <option value="repair_once">repair_once</option>
          <option value="repair_twice">repair_twice</option>
        </select>
      </label>
    </div>
  );
}
