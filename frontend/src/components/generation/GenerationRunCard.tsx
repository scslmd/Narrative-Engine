import type { GenerationRunResponse } from '../../types/storyGeneration';

interface GenerationRunCardProps {
  run: GenerationRunResponse;
}

export function GenerationRunCard({ run }: GenerationRunCardProps) {
  return (
    <div className="rounded border border-slate-300 p-3 text-sm">
      <p className="font-semibold">{run.generation_id || 'Pending Generation'}</p>
      <p>Status: {run.status}</p>
      <p>Jobs: {run.job_ids.length}</p>
      <p>Warnings: {run.warnings.length}</p>
    </div>
  );
}
