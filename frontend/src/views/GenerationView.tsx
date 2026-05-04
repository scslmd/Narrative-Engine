import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { ApiError } from '../lib/api';
import { getCharacters } from '../services/characters';
import { getWorldBibleEntries } from '../services/worldBible';
import {
  createGenerationRun,
  getGenerationGates,
  listGenerationRuns,
  previewFork,
  retryGenerationRun,
} from '../services/storyGeneration';
import type { GenerationRunResponse } from '../types/storyGeneration';
import { GenerationGatePanel } from '../components/generation/GenerationGatePanel';
import { GeneratedStoryReview } from '../components/generation/GeneratedStoryReview';
import { GenerationRunCard } from '../components/generation/GenerationRunCard';
import { StoryGenerationWizard } from '../components/generation/StoryGenerationWizard';
import { useToast } from '../hooks/useToast';
import { useApiQuery } from '../hooks/useApiQuery';
import { LoadingState } from '../components/ui/LoadingState';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorBanner } from '../components/ui/ErrorBanner';

export function GenerationView() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const [selectedRun, setSelectedRun] = useState<GenerationRunResponse | null>(null);
  const [gateRunId, setGateRunId] = useState<string | null>(null);

  const charactersQuery = useQuery({
    queryKey: ['generation', 'characters', projectId],
    queryFn: () => getCharacters(projectId || ''),
    enabled: Boolean(projectId),
  });
  const worldQuery = useQuery({
    queryKey: ['generation', 'world', projectId],
    queryFn: () => getWorldBibleEntries(projectId || ''),
    enabled: Boolean(projectId),
  });
  const runsQuery = useApiQuery({
    queryKey: ['generation', 'runs', projectId || ''],
    serviceFn: () => listGenerationRuns(projectId || ''),
    onErrorToast: false,
  });
  const gatesQuery = useQuery({
    queryKey: ['generation', 'gates', gateRunId],
    queryFn: () => getGenerationGates(gateRunId || ''),
    enabled: Boolean(gateRunId),
  });

  const retryMutation = useMutation({
    mutationFn: (generationId: string) => retryGenerationRun(generationId),
    retry: false,
    onSuccess: async () => {
      addToast('Retry submitted successfully', 'success');
      await queryClient.invalidateQueries({ queryKey: ['generation', 'runs', projectId] });
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        if (error.status === 409) {
          addToast('Cannot retry this run — it is not in a failed state.', 'error');
        } else if (error.status === 404) {
          addToast('Generation packet expired. Re-submit from wizard.', 'error');
        } else {
          addToast(error.message, 'error');
        }
      } else {
        addToast(error instanceof Error ? error.message : 'Retry failed', 'error');
      }
    },
  });

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

  return (
    <div className="space-y-4">
      <StoryGenerationWizard
        projectId={projectId}
        characters={charactersQuery.data || []}
        worldEntries={worldQuery.data || []}
        onPreview={previewFork}
        onSubmit={createGenerationRun}
        onSubmitted={(run) => {
          setSelectedRun(run);
          setGateRunId(run.generation_id);
          void queryClient.invalidateQueries({ queryKey: ['generation', 'runs', projectId] });
        }}
      />

      <ErrorBanner error={runsQuery.error} onRetry={runsQuery.retry} />

      <LoadingState isLoading={runsQuery.isLoading}>
        {runsQuery.data && runsQuery.data.length === 0 ? (
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(runsQuery.data || []).map((run) => (
              <div
                key={run.generation_id || `run-${run.source_project_id}-${run.target_project_id}`}
                onClick={() => {
                  setSelectedRun(run);
                  setGateRunId(run.generation_id);
                }}
                className="cursor-pointer text-left"
              >
                <GenerationRunCard
                  run={run}
                  onRetry={() => retryMutation.mutate(run.generation_id)}
                  isRetrying={retryMutation.isPending && retryMutation.variables === run.generation_id}
                />
              </div>
            ))}
          </div>
        )}
      </LoadingState>

      <GenerationGatePanel gates={gatesQuery.data || []} />
      <GeneratedStoryReview run={selectedRun} />
    </div>
  );
}
