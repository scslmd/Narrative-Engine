interface CanonScopeSummaryProps {
  character_ids: string[];
  world_count: number;
  mythos_ids: string[];
  pattern_ids: string[];
}

export function CanonScopeSummary({
  character_ids,
  world_count,
  mythos_ids,
  pattern_ids,
}: CanonScopeSummaryProps) {
  return (
    <div className="rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3 text-sm text-slate-700 dark:text-slate-300">
      <span>Scope: </span>
      <span>{character_ids.length} characters, </span>
      <span>{world_count} world entries, </span>
      <span>{mythos_ids.length} mythos, </span>
      <span>{pattern_ids.length} patterns</span>
    </div>
  );
}
