import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { CanonWorkshop } from '../components/canon/CanonWorkshop';
import {
  createCanonProfile,
  getCanonAnnotations,
  getCanonProfiles,
  previewCanonProfilePacket,
} from '../services/canonCustomization';
import { getCharacters } from '../services/characters';
import { getMythosEntries } from '../services/mythosLibrary';
import { getPatternEntries } from '../services/patternLibrary';
import { createGenerationRun } from '../services/storyGeneration';
import { getWorldBibleEntries } from '../services/worldBible';
import type { CanonGenerationPacket } from '../types/storyGeneration';

export function CanonView() {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [packetPreview, setPacketPreview] = useState<CanonGenerationPacket | null>(null);
  const tabParam = searchParams.get('tab');
  const initialTab =
    tabParam === 'mythos' || tabParam === 'patterns' || tabParam === 'packet'
      ? tabParam
      : 'overview';

  const charactersQuery = useQuery({
    queryKey: ['planning', 'characters', projectId],
    queryFn: () => getCharacters(projectId || ''),
    enabled: Boolean(projectId),
  });
  const worldQuery = useQuery({
    queryKey: ['planning', 'world-bible', projectId],
    queryFn: () => getWorldBibleEntries(projectId || ''),
    enabled: Boolean(projectId),
  });
  const mythosQuery = useQuery({
    queryKey: ['canon', 'mythos', projectId],
    queryFn: () => getMythosEntries(projectId || ''),
    enabled: Boolean(projectId),
  });
  const patternsQuery = useQuery({
    queryKey: ['canon', 'patterns', projectId],
    queryFn: () => getPatternEntries(projectId || ''),
    enabled: Boolean(projectId),
  });
  const annotationsQuery = useQuery({
    queryKey: ['canon', 'annotations', projectId],
    queryFn: () => getCanonAnnotations(projectId || ''),
    enabled: Boolean(projectId),
  });
  const profilesQuery = useQuery({
    queryKey: ['canon', 'profiles', projectId],
    queryFn: () => getCanonProfiles(projectId || ''),
    enabled: Boolean(projectId),
  });

  const createProfileMutation = useMutation({
    mutationFn: createCanonProfile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['canon', 'profiles', projectId] });
    },
  });
  const createGenerationMutation = useMutation({
    mutationFn: createGenerationRun,
    onSuccess: (run) => {
      navigate(`/workspace/${projectId}/generate?generation_id=${run.generation_id}`);
    },
  });

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

  const isLoading = [
    charactersQuery,
    worldQuery,
    mythosQuery,
    patternsQuery,
    annotationsQuery,
    profilesQuery,
  ].some((query) => query.isLoading);

  if (isLoading) {
    return <div className="text-sm text-slate-500">Loading canon workspace...</div>;
  }

  if (
    charactersQuery.isError ||
    worldQuery.isError ||
    mythosQuery.isError ||
    patternsQuery.isError ||
    annotationsQuery.isError ||
    profilesQuery.isError
  ) {
    return <div className="text-sm text-red-600">Failed to load canon workspace data.</div>;
  }

  return (
    <CanonWorkshop
      projectId={projectId}
      characters={charactersQuery.data || []}
      worldEntries={worldQuery.data || []}
      mythosEntries={mythosQuery.data || []}
      patternEntries={patternsQuery.data || []}
      annotations={annotationsQuery.data || []}
      profiles={profilesQuery.data || []}
      packetPreview={packetPreview}
      initialTab={initialTab}
      onSaveProfile={async (request) => {
        await createProfileMutation.mutateAsync(request);
      }}
      onPreviewPacket={async (profileId) => {
        const packet = await previewCanonProfilePacket(projectId, profileId);
        setPacketPreview(packet);
      }}
      onSubmitGeneration={async (request) => createGenerationMutation.mutateAsync(request)}
    />
  );
}
