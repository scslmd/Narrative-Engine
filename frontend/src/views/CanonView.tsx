import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { CanonWorkshop } from '../components/canon/CanonWorkshop';
import { useMythosLibrary } from '../hooks/useMythosLibrary';
import { usePatternLibrary } from '../hooks/usePatternLibrary';
import {
  createCanonProfile,
  getCanonAnnotations,
  getCanonProfiles,
  previewCanonProfilePacket,
} from '../services/canonCustomization';
import { getCharacters } from '../services/characters';
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
    retry: false,
  });
  const worldQuery = useQuery({
    queryKey: ['planning', 'world-bible', projectId],
    queryFn: () => getWorldBibleEntries(projectId || ''),
    enabled: Boolean(projectId),
    retry: false,
  });
  const { entries: mythosEntries, deleteEntry: deleteMythosEntry } = useMythosLibrary(projectId || '');
  const { entries: patternEntries, deleteEntry: deletePatternEntry } = usePatternLibrary(projectId || '');
  const annotationsQuery = useQuery({
    queryKey: ['canon', 'annotations', projectId],
    queryFn: () => getCanonAnnotations(projectId || ''),
    enabled: Boolean(projectId),
    retry: false,
  });
  const profilesQuery = useQuery({
    queryKey: ['canon', 'profiles', projectId],
    queryFn: () => getCanonProfiles(projectId || ''),
    enabled: Boolean(projectId),
    retry: false,
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
    annotationsQuery,
    profilesQuery,
  ].some((query) => query.isLoading);

  if (isLoading) {
    return <div className="text-sm text-slate-500">Loading canon workspace...</div>;
  }

  if (
    charactersQuery.isError ||
    worldQuery.isError ||
    annotationsQuery.isError ||
    profilesQuery.isError
  ) {
    const anyAuthError = [charactersQuery, worldQuery, annotationsQuery, profilesQuery].some(
      (q) => q.error && typeof q.error === 'object' && 'status' in q.error && q.error.status === 401,
    );
    if (anyAuthError) {
      return (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-2">
          <p className="text-sm font-medium text-amber-900">API key required</p>
          <p className="text-sm text-amber-800">
            The Canon Workshop requires API authentication. Create an API key in{' '}
            <button className="font-semibold text-amber-900 underline hover:no-underline cursor-pointer">Settings &gt; API Keys</button>, then set the <code className="px-1 py-0.5 bg-amber-100 rounded text-xs">NARRATIVE_API_KEY</code> environment variable on your server to enable these features.
          </p>
          <p className="text-xs text-amber-700">See <strong>User Guide §Authentication</strong> for setup instructions.</p>
        </div>
      );
    }
    return <div className="text-sm text-red-600">Failed to load canon workspace data.</div>;
  }

  return (
    <CanonWorkshop
      projectId={projectId}
      characters={charactersQuery.data || []}
      worldEntries={worldQuery.data || []}
      mythosEntries={mythosEntries}
      patternEntries={patternEntries}
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
      onDeleteMythosEntry={(mythosId) => void deleteMythosEntry(mythosId)}
      onDeletePatternEntry={(patternId) => void deletePatternEntry(patternId)}
    />
  );
}
