import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../../lib/api';
import { useApiQuery } from '../../hooks/useApiQuery';
import { useToast } from '../../hooks/useToast';
import { getCharacters } from '../../services/characters';
import { getWorldBibleEntries } from '../../services/worldBible';
import {
  createForkProject,
  createGenerationRun,
  getGenerationGates,
  getGenerationPacket,
  getGenerationRun,
  listGenerationRuns,
  previewFork,
  retryGenerationRun,
} from '../../services/storyGeneration';
import type { CharacterProfile } from '../../types/characters';
import type { WorldBibleEntry } from '../../types/bible';
import type {
  CanonForkPreviewResponse,
  CanonGenerationRequest,
  GenerationGateResult,
  GenerationRunResponse,
} from '../../types/storyGeneration';
import { invalidateMany } from '../shared/invalidation';
import { queryKeys } from '../shared/queryKeys';

interface UseGenerationControllerResult {
  selectedRun: GenerationRunResponse | null;
  selectedPacketSize: number | null;
  characters: CharacterProfile[];
  worldEntries: WorldBibleEntry[];
  runs: GenerationRunResponse[];
  runsLoading: boolean;
  runsError: ApiError | null;
  retryRuns: () => Promise<void>;
  gates: GenerationGateResult[];
  selectedRunStatus: GenerationRunResponse['status'] | null;
  forkIsPending: boolean;
  retryIsPending: boolean;
  retryVariables: string | undefined;
  handleRunSubmitted: (run: GenerationRunResponse) => void;
  handleRunSelected: (run: GenerationRunResponse) => void;
  handleRetryRun: (generationId: string) => void;
  handleForkSelectedRun: () => void;
  submitGenerationRun: (request: CanonGenerationRequest) => Promise<GenerationRunResponse>;
  previewForkRun: (request: CanonGenerationRequest) => Promise<CanonForkPreviewResponse>;
}

export function useGenerationController(projectId: string | undefined): UseGenerationControllerResult {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const [selectedRun, setSelectedRun] = useState<GenerationRunResponse | null>(null);
  const [gateRunId, setGateRunId] = useState<string | null>(null);
  const [selectedPacketSize, setSelectedPacketSize] = useState<number | null>(null);

  const charactersQuery = useQuery({
    queryKey: queryKeys.generation.characters(projectId || ''),
    queryFn: () => getCharacters(projectId || ''),
    enabled: Boolean(projectId),
  });
  const worldQuery = useQuery({
    queryKey: queryKeys.generation.world(projectId || ''),
    queryFn: () => getWorldBibleEntries(projectId || ''),
    enabled: Boolean(projectId),
  });
  const runsQuery = useApiQuery({
    queryKey: [...queryKeys.generation.runs(projectId || '')],
    serviceFn: () => listGenerationRuns(projectId || ''),
    onErrorToast: false,
  });
  const gatesQuery = useQuery({
    queryKey: queryKeys.generation.gates(gateRunId || ''),
    queryFn: () => getGenerationGates(gateRunId || ''),
    enabled: Boolean(gateRunId),
  });
  const selectedRunQuery = useQuery({
    queryKey: queryKeys.generation.run(selectedRun?.generation_id || ''),
    queryFn: () => getGenerationRun(selectedRun!.generation_id),
    enabled: Boolean(selectedRun?.generation_id),
  });
  const packetQuery = useQuery({
    queryKey: queryKeys.generation.packet(selectedRun?.generation_id || ''),
    queryFn: () => getGenerationPacket(selectedRun!.generation_id),
    enabled: Boolean(selectedRun?.generation_id),
  });

  useEffect(() => {
    if (!packetQuery.data) {
      setSelectedPacketSize(null);
      return;
    }
    const packet = packetQuery.data;
    setSelectedPacketSize(
      packet.characters.length +
        packet.world_bible.length +
        packet.mythos_entries.length +
        packet.pattern_entries.length,
    );
  }, [packetQuery.data]);

  const forkMutation = useMutation({
    mutationFn: (run: GenerationRunResponse) =>
      createForkProject({
        source_project_id: run.source_project_id,
        mode: 'new_project_hybrid_fork',
        destination: {
          destination_kind: 'new_project',
          target_project_name: `${run.target_project_id || run.source_project_id}-fork`,
        },
        canon_scope: {
          source_project_id: run.source_project_id,
          character_ids: [],
          world_bible_refs: [],
          continuity_thread_ids: [],
          arc_ids: [],
          mythos_ids: [],
          pattern_ids: [],
          include_relationships: true,
          include_unresolved_questions: true,
          include_contradictions_as_forbidden: true,
        },
        generation_brief: `Fork project from generation run ${run.generation_id}`,
        target_chapter_count: 8,
      }),
    onSuccess: async () => {
      addToast('Fork project request submitted', 'success');
      await invalidateMany(queryClient, [queryKeys.generation.runs(projectId || '')]);
    },
    onError: (error) => {
      addToast(error instanceof Error ? error.message : 'Fork failed', 'error');
    },
  });

  const retryMutation = useMutation({
    mutationFn: (generationId: string) => retryGenerationRun(generationId),
    retry: false,
    onSuccess: async () => {
      addToast('Retry submitted successfully', 'success');
      await invalidateMany(queryClient, [queryKeys.generation.runs(projectId || '')]);
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        if (error.status === 409) {
          addToast('Cannot retry this run - it is not in a failed state.', 'error');
          return;
        }
        if (error.status === 404) {
          addToast('Generation packet expired. Re-submit from wizard.', 'error');
          return;
        }
      }
      addToast(error instanceof Error ? error.message : 'Retry failed', 'error');
    },
  });

  const handleRunSubmitted = (run: GenerationRunResponse) => {
    setSelectedRun(run);
    setGateRunId(run.generation_id);
    void invalidateMany(queryClient, [queryKeys.generation.runs(projectId || '')]);
  };

  const handleRunSelected = (run: GenerationRunResponse) => {
    setSelectedRun(run);
    setGateRunId(run.generation_id);
  };

  const handleRetryRun = (generationId: string) => {
    retryMutation.mutate(generationId);
  };

  const handleForkSelectedRun = () => {
    if (!selectedRun) {
      return;
    }
    forkMutation.mutate(selectedRun);
  };

  return {
    selectedRun,
    selectedPacketSize,
    characters: charactersQuery.data || [],
    worldEntries: worldQuery.data || [],
    runs: runsQuery.data || [],
    runsLoading: runsQuery.isLoading,
    runsError: runsQuery.error,
    retryRuns: runsQuery.retry,
    gates: gatesQuery.data || [],
    selectedRunStatus: selectedRunQuery.data?.status || null,
    forkIsPending: forkMutation.isPending,
    retryIsPending: retryMutation.isPending,
    retryVariables: retryMutation.variables,
    handleRunSubmitted,
    handleRunSelected,
    handleRetryRun,
    handleForkSelectedRun,
    submitGenerationRun: createGenerationRun,
    previewForkRun: previewFork,
  };
}
