import { useParams } from 'react-router-dom';
import { GenerationGatePanel } from '../components/generation/GenerationGatePanel';
import { GeneratedStoryReview } from '../components/generation/GeneratedStoryReview';
import { GenerationRunCard } from '../components/generation/GenerationRunCard';
import { StoryGenerationWizard } from '../components/generation/StoryGenerationWizard';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { LoadingState } from '../components/ui/LoadingState';
import { ViewShell } from '../components/shell/ViewShell';
import { useGenerationController } from '../domains/generation/useGenerationController';

export function GenerationView() {
  const { projectId } = useParams<{ projectId: string }>();
  const {
    selectedRun,
    selectedPacketSize,
    characters,
    worldEntries,
    runs,
    runsLoading,
    runsError,
    retryRuns,
    gates,
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

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

  return (
    <ViewShell title="Generate" subtitle={projectId}>
      <div className="p-4 space-y-4">
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
            <EmptyState
              title="No generation runs yet"
              description="Start the wizard above to create your first generation run."
              actionLabel="Start Generation Wizard"
              onAction={() => {
                const wizard = document.querySelector('[data-generation-wizard]');
                wizard?.scrollIntoView({ behavior: 'smooth' });
              }}
            />
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {runs.map((run) => (
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
          <div className="space-y-2 rounded border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-3 text-sm">
            <div className="text-[var(--text-primary)]">Latest status: {selectedRunStatus || selectedRun.status}</div>
            <div className="text-[var(--text-primary)]">Packet entities: {selectedPacketSize ?? 0}</div>
            <button
              type="button"
              className="rounded bg-[var(--color-primary)] px-3 py-1.5 text-xs text-white disabled:opacity-50"
              disabled={forkIsPending}
              onClick={handleForkSelectedRun}
            >
              {forkIsPending ? 'Forking...' : 'Fork Project from Run'}
            </button>
          </div>
        )}
        <GeneratedStoryReview run={selectedRun} />
      </div>
    </ViewShell>
  );
}
