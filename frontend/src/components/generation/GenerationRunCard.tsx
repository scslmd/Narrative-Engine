import type { GenerationRunResponse } from '../../types/storyGeneration';

interface GenerationRunCardProps {
  run: GenerationRunResponse;
  onRetry?: () => void;
  isRetrying?: boolean;
}

export function GenerationRunCard({ run, onRetry, isRetrying }: GenerationRunCardProps) {
  const isFailed = run.status === 'failed';

  return (
    <div className="rounded border border-slate-300 p-3 text-sm">
      <p className="font-semibold">{run.generation_id || 'Pending Generation'}</p>
      <p>Status: {run.status}</p>
      <p>Jobs: {run.job_ids.length}</p>
      <p>Warnings: {run.warnings.length}</p>
      {isFailed && onRetry && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRetry();
          }}
          disabled={isRetrying}
          className={`mt-2 rounded px-3 py-1 text-xs font-medium ${
            isRetrying
              ? 'cursor-not-allowed bg-slate-200 text-slate-400'
              : 'bg-red-600 text-white hover:bg-red-700'
          }`}
        >
          {isRetrying ? 'Retrying...' : 'Retry'}
        </button>
      )}
    </div>
  );
}
