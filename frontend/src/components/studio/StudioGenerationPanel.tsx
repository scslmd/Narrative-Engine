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
 <div className="flex h-full flex-col">
        <div className="flex shrink-0 items-center justify-between px-3 py-2 border-b border-[var(--border-primary)]">
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">Generation</h3>
        </div>

        <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
          <ErrorBanner error={runsError} onRetry={retryRuns} />

          <LoadingState isLoading={runsLoading}>
            {runs.length === 0 ? (
              <p className="text-[10px] text-[var(--text-tertiary)]">No generation runs yet.</p>
            ) : (
              <div className="space-y-1.5">
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

          {selectedRun && (
            <div className="space-y-1.5 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-2 text-[10px]">
              <div className="text-[var(--text-secondary)]">Latest status: {selectedRunStatus || selectedRun.status}</div>
              <div className="flex gap-1.5">
                <button
                  type="button"
                  className="rounded bg-[var(--accent-primary)] px-2 py-1 text-[10px] text-white disabled:opacity-50"
                  disabled={forkIsPending}
                  onClick={handleForkSelectedRun}
                >
                  {forkIsPending ? 'Forking...' : 'Fork Project'}
                </button>
              </div>
            </div>
          )}

          <GenerationGatePanel gates={gates} />

          <StoryGenerationWizard
            projectId={projectId}
            characters={characters}
            worldEntries={worldEntries}
            onPreview={previewForkRun}
            onSubmit={submitGenerationRun}
            onSubmitted={handleRunSubmitted}
          />
        </div>
      </div>
  );
}
