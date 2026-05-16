import { GenerationGatePanel } from '../generation/GenerationGatePanel';
import { GenerationRunCard } from '../generation/GenerationRunCard';
import { StoryGenerationWizard } from '../generation/StoryGenerationWizard';
import { ErrorBanner } from '../ui/ErrorBanner';
import { LoadingState } from '../ui/LoadingState';
import { useGenerationController } from '../../domains/generation/useGenerationController';

interface StudioGenerationPanelProps {
  projectId: string;
}

export function StudioGenerationPanel({ projectId }: StudioGenerationPanelProps) {
  const {
    characters,
    worldEntries,
    runs,
    runsLoading,
    runsError,
    retryRuns,
    gates,
    selectedRun,
    selectedRunStatus,
    forkIsPending,
    retryIsPending,
    retryVariables,
    handleRunSubmitted,
    handleRunSelected,
    handleRetryRun,
    handleForkSelectedRun,
    submitGenerationRun,
    previewForkRun,
  } = useGenerationController(projectId);

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-slate-100">Generation</h3>

      <StoryGenerationWizard
        projectId={projectId}
        characters={characters}
        worldEntries={worldEntries}
        onPreview={previewForkRun}
        onSubmit={submitGenerationRun}
        onSubmitted={handleRunSubmitted}
      />

      <ErrorBanner error={runsError} onRetry={retryRuns} />

      <LoadingState isLoading={runsLoading}>
        {runs.length === 0 ? (
          <p className="text-xs text-slate-500">No generation runs yet.</p>
        ) : (
          <div className="space-y-3">
            {runs.slice(0, 5).map((run) => (
              <div
                key={run.generation_id || `run-${run.source_project_id}-${run.target_project_id}`}
                onClick={() => handleRunSelected(run)}
                className="cursor-pointer text-left"
              >
                <GenerationRunCard
                  run={run}
                  onRetry={() => handleRetryRun(run.generation_id)}
                  isRetrying={retryIsPending && retryVariables === run.generation_id}
                />
              </div>
            ))}
          </div>
        )}
      </LoadingState>

      <GenerationGatePanel gates={gates} />

      {selectedRun && (
        <div className="space-y-2 rounded border border-slate-300 p-3 text-sm dark:border-slate-600">
          <div>Latest status: {selectedRunStatus || selectedRun.status}</div>
          <button
            type="button"
            className="rounded bg-slate-900 px-3 py-1.5 text-xs text-white disabled:opacity-50"
            disabled={forkIsPending}
            onClick={handleForkSelectedRun}
          >
            {forkIsPending ? 'Forking...' : 'Fork Project from Run'}
          </button>
        </div>
      )}
    </div>
  );
}
