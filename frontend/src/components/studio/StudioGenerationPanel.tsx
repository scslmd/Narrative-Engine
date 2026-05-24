import { GenerationGatePanel } from '../generation/GenerationGatePanel';
import { GenerationRunCard } from '../generation/GenerationRunCard';
import { StoryGenerationWizard } from '../generation/StoryGenerationWizard';
import { ErrorBanner } from '../ui/ErrorBanner';
import { LoadingState } from '../ui/LoadingState';
import { useGenerationController } from '../../domains/generation/useGenerationController';
import { useStudioStore } from '../../stores/studioStore';
import { ExternalLink, BookOpen, Layers } from 'lucide-react';
import { useThemeStore } from '../../stores/themeStore';
import { resolveEffectiveMode } from '../../theme/theme';

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
    selectedPacketSize,
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

  const openPanel = useStudioStore((s) => s.openPanel);
  const setPanelVisible = useStudioStore((s) => s.setPanelVisible);
  const { mode: themeMode } = useThemeStore();
  const isDark = resolveEffectiveMode(themeMode) === 'dark';

  const handleOpenInEditor = () => {
    if (!selectedRun) return;
    setPanelVisible(true);
    openPanel('manuscripts');
  };

  const handleOpenTargetProject = () => {
    if (!selectedRun) return;
    const targetId = selectedRun.target_project_id;
    if (targetId && targetId !== projectId) {
      window.location.href = `/workspace/${targetId}/studio?tab=manuscripts`;
    }
  };

  const completedRuns = runs.filter(
    (r) => r.status === 'completed' || r.status === 'blocked',
  );

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
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
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-secondary)]">Latest status: {selectedRunStatus || selectedRun.status}</span>
              {selectedPacketSize !== null && (
                <span className={`text-[8px] px-1 py-0.5 rounded ${isDark ? 'bg-slate-700 text-slate-400' : 'bg-slate-200 text-slate-500'}`}>
                  Packet: {selectedPacketSize} items
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-1">
              <button
                type="button"
                className="flex items-center gap-1 rounded bg-emerald-600 px-1.5 py-0.5 text-[9px] text-white hover:bg-emerald-500 disabled:opacity-50"
                onClick={handleOpenInEditor}
              >
                <BookOpen className="w-3 h-3" />
                Open in Editor
              </button>
              {selectedRun.target_project_id !== selectedRun.source_project_id && (
                <button
                  type="button"
                  className="flex items-center gap-1 rounded bg-blue-600 px-1.5 py-0.5 text-[9px] text-white hover:bg-blue-500 disabled:opacity-50"
                  onClick={handleOpenTargetProject}
                >
                  <ExternalLink className="w-3 h-3" />
                  Open Target Project
                </button>
              )}
              <button
                type="button"
                className="rounded bg-[var(--accent-primary)] px-1.5 py-0.5 text-[9px] text-white disabled:opacity-50"
                disabled={forkIsPending}
                onClick={handleForkSelectedRun}
              >
                {forkIsPending ? 'Forking...' : 'Fork'}
              </button>
            </div>
          </div>
        )}

        {completedRuns.length > 0 && (
          <div className="space-y-1">
            <div className={`flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
              <Layers className="w-3 h-3" />
              Completed Runs
            </div>
            <div className="flex flex-wrap gap-1">
              {completedRuns.slice(0, 3).map((run) => (
                <button
                  key={run.generation_id}
                  type="button"
                  className="flex items-center gap-1 rounded border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-2 py-1 text-[9px] text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]"
                  onClick={() => handleRunSelected(run)}
                >
                  <ExternalLink className="w-3 h-3" />
                  {run.target_project_id !== run.source_project_id
                    ? `→ ${run.target_project_id}`
                    : `${run.generation_id.slice(0, 8)}`}
                </button>
              ))}
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
