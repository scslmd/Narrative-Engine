import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { getCharacters } from '../services/characters';
import { getWorldBibleEntries } from '../services/worldBible';
import {
  createGenerationRun,
  getGenerationGates,
  listGenerationRuns,
  previewFork,
} from '../services/storyGeneration';
import type { GenerationRunResponse } from '../types/storyGeneration';
import { GenerationGatePanel } from '../components/generation/GenerationGatePanel';
import { GeneratedStoryReview } from '../components/generation/GeneratedStoryReview';
import { GenerationRunCard } from '../components/generation/GenerationRunCard';
import { StoryGenerationWizard } from '../components/generation/StoryGenerationWizard';

export function GenerationView() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
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
  const runsQuery = useQuery({
    queryKey: ['generation', 'runs', projectId],
    queryFn: () => listGenerationRuns(projectId || ''),
    enabled: Boolean(projectId),
  });
  const gatesQuery = useQuery({
    queryKey: ['generation', 'gates', gateRunId],
    queryFn: () => getGenerationGates(gateRunId || ''),
    enabled: Boolean(gateRunId),
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {(runsQuery.data || []).map((run) => (
          <button
            key={run.generation_id || `run-${run.source_project_id}-${run.target_project_id}`}
            type="button"
            onClick={() => {
              setSelectedRun(run);
              setGateRunId(run.generation_id);
            }}
            className="text-left"
          >
            <GenerationRunCard run={run} />
          </button>
        ))}
      </div>

      <GenerationGatePanel gates={gatesQuery.data || []} />
      <GeneratedStoryReview run={selectedRun} />
    </div>
  );
}
