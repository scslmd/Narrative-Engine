import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useMythosLibrary } from '../../hooks/useMythosLibrary';
import { usePatternLibrary } from '../../hooks/usePatternLibrary';
import {
  createCanonProfile,
  deleteCanonAnnotation,
  deleteCanonProfile,
  getCanonAnnotations,
  getCanonProfiles,
  previewCanonProfilePacket,
  updateCanonProfile,
} from '../../services/canonCustomization';
import { getCharacters } from '../../services/characters';
import { materializeMythosExtraction } from '../../services/mythosLibrary';
import { materializePatternExtraction } from '../../services/patternLibrary';
import { createGenerationRun } from '../../services/storyGeneration';
import { getWorldBibleEntries } from '../../services/worldBible';
import type {
  CanonAnnotation,
  CanonCustomizationProfileCreateRequest,
} from '../../types/canonCustomization';
import type {
  CanonGenerationPacket,
  CanonGenerationRequest,
  GenerationRunResponse,
  WorldBibleRef,
} from '../../types/storyGeneration';
import { invalidateMany } from '../shared/invalidation';
import { queryKeys } from '../shared/queryKeys';

export interface CanonSelectionState {
  profileName: string;
  generationBrief: string;
  selectedCharacterIds: string[];
  selectedWorldRefs: WorldBibleRef[];
  selectedMythosIds: string[];
  selectedPatternIds: string[];
}

interface UseCanonControllerResult {
  isLoading: boolean;
  isAuthError: boolean;
  isError: boolean;
  packetPreview: CanonGenerationPacket | null;
  characters: Awaited<ReturnType<typeof getCharacters>>;
  worldEntries: Awaited<ReturnType<typeof getWorldBibleEntries>>;
  mythosEntries: ReturnType<typeof useMythosLibrary>['entries'];
  patternEntries: ReturnType<typeof usePatternLibrary>['entries'];
  annotations: CanonAnnotation[];
  profiles: Awaited<ReturnType<typeof getCanonProfiles>>;
  saveProfileFromSelection: (selection: CanonSelectionState) => Promise<void>;
  submitGenerationFromSelection: (selection: CanonSelectionState) => Promise<GenerationRunResponse>;
  previewPacket: (profileId: string) => Promise<void>;
  deleteMythosEntry: (mythosId: string) => Promise<void>;
  deletePatternEntry: (patternId: string) => Promise<void>;
  renameProfile: (profileId: string, name: string) => Promise<void>;
  deleteProfile: (profileId: string) => Promise<void>;
  deleteAnnotation: (annotationId: string) => Promise<void>;
  materializeMythos: (extractionId: string) => Promise<void>;
  materializePatterns: (extractionId: string) => Promise<void>;
}

function toProfileRequest(
  projectId: string,
  selection: CanonSelectionState,
  annotations: CanonAnnotation[],
): CanonCustomizationProfileCreateRequest {
  return {
    project_id: projectId,
    name: selection.profileName,
    description: '',
    default_generation_mode: 'same_project_side_story',
    canon_scope: {
      source_project_id: projectId,
      scope_mode: 'selected',
      character_ids: selection.selectedCharacterIds,
      world_bible_refs: selection.selectedWorldRefs,
      continuity_thread_ids: [],
      arc_ids: [],
      mythos_ids: selection.selectedMythosIds,
      pattern_ids: selection.selectedPatternIds,
      include_relationships: true,
      include_unresolved_questions: true,
      include_contradictions_as_forbidden: true,
    },
    canon_policy: {
      locked_character_fields: ['character.display_name', 'character.voice_notes'],
      locked_world_fields: ['world_bible.title', 'world_bible.canonical_facts'],
      allowed_character_changes: [],
      allowed_world_changes: [],
      forbidden_contradictions: annotations
        .filter((item) => item.annotation_kind === 'forbidden_contradiction')
        .map((item) => item.note || `${item.target_kind}.${item.field_path}`),
      continuity_strictness: 'repair_once',
    },
    generation_brief_template: selection.generationBrief,
    selected_annotation_ids: annotations.map((item) => item.annotation_id),
    status: 'draft',
  };
}

function toGenerationRequest(projectId: string, selection: CanonSelectionState): CanonGenerationRequest {
  return {
    source_project_id: projectId,
    mode: 'same_project_side_story',
    destination: {
      destination_kind: 'same_project',
      target_project_id: projectId,
    },
    canon_scope: {
      source_project_id: projectId,
      scope_mode: 'selected',
      character_ids: selection.selectedCharacterIds,
      world_bible_refs: selection.selectedWorldRefs,
      continuity_thread_ids: [],
      arc_ids: [],
      mythos_ids: selection.selectedMythosIds,
      pattern_ids: selection.selectedPatternIds,
      include_relationships: true,
      include_unresolved_questions: true,
      include_contradictions_as_forbidden: true,
    },
    generation_brief: selection.generationBrief,
    target_chapter_count: 8,
  };
}

export function useCanonController(projectId: string): UseCanonControllerResult {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [packetPreview, setPacketPreview] = useState<CanonGenerationPacket | null>(null);

  const charactersQuery = useQuery({
    queryKey: queryKeys.canon.planningCharacters(projectId),
    queryFn: () => getCharacters(projectId),
    enabled: Boolean(projectId),
    retry: false,
  });

  const worldQuery = useQuery({
    queryKey: queryKeys.canon.planningWorldBible(projectId),
    queryFn: () => getWorldBibleEntries(projectId),
    enabled: Boolean(projectId),
    retry: false,
  });

  const { entries: mythosEntries, deleteEntry: deleteMythosEntry } = useMythosLibrary(projectId);
  const { entries: patternEntries, deleteEntry: deletePatternEntry } = usePatternLibrary(projectId);

  const annotationsQuery = useQuery({
    queryKey: queryKeys.canon.annotations(projectId),
    queryFn: () => getCanonAnnotations(projectId),
    enabled: Boolean(projectId),
    retry: false,
  });

  const profilesQuery = useQuery({
    queryKey: queryKeys.canon.profiles(projectId),
    queryFn: () => getCanonProfiles(projectId),
    enabled: Boolean(projectId),
    retry: false,
  });

  const createProfileMutation = useMutation({
    mutationFn: createCanonProfile,
    onSuccess: async () => {
      await invalidateMany(queryClient, [queryKeys.canon.profiles(projectId)]);
    },
  });

  const updateProfileMutation = useMutation({
    mutationFn: ({ profileId, name }: { profileId: string; name: string }) =>
      updateCanonProfile(profileId, projectId, { name }),
    onSuccess: async () => {
      await invalidateMany(queryClient, [queryKeys.canon.profiles(projectId)]);
    },
  });

  const deleteProfileMutation = useMutation({
    mutationFn: (profileId: string) => deleteCanonProfile(projectId, profileId),
    onSuccess: async () => {
      await invalidateMany(queryClient, [queryKeys.canon.profiles(projectId)]);
    },
  });

  const deleteAnnotationMutation = useMutation({
    mutationFn: (annotationId: string) => deleteCanonAnnotation(projectId, annotationId),
    onSuccess: async () => {
      await invalidateMany(queryClient, [queryKeys.canon.annotations(projectId)]);
    },
  });

  const materializeMythosMutation = useMutation({
    mutationFn: (extractionId: string) => materializeMythosExtraction(projectId, extractionId),
    onSuccess: async () => {
      await invalidateMany(queryClient, [queryKeys.canon.mythos(projectId)]);
    },
  });

  const materializePatternsMutation = useMutation({
    mutationFn: (extractionId: string) => materializePatternExtraction(projectId, extractionId),
    onSuccess: async () => {
      await invalidateMany(queryClient, [queryKeys.canon.patterns(projectId)]);
    },
  });

  const createGenerationMutation = useMutation({
    mutationFn: createGenerationRun,
    onSuccess: (run) => {
      navigate(`/workspace/${projectId}/generate?generation_id=${run.generation_id}`);
    },
  });

  const queries = [charactersQuery, worldQuery, annotationsQuery, profilesQuery];
  const isLoading = queries.some((query) => query.isLoading);
  const isError = queries.some((query) => query.isError);
  const isAuthError = queries.some(
    (query) => query.error && typeof query.error === 'object' && 'status' in query.error && query.error.status === 401,
  );

  return {
    isLoading,
    isError,
    isAuthError,
    packetPreview,
    characters: charactersQuery.data ?? [],
    worldEntries: worldQuery.data ?? [],
    mythosEntries,
    patternEntries,
    annotations: annotationsQuery.data ?? [],
    profiles: profilesQuery.data ?? [],
    saveProfileFromSelection: async (selection) => {
      const request = toProfileRequest(projectId, selection, annotationsQuery.data ?? []);
      await createProfileMutation.mutateAsync(request);
    },
    submitGenerationFromSelection: async (selection) => {
      const request = toGenerationRequest(projectId, selection);
      return createGenerationMutation.mutateAsync(request);
    },
    previewPacket: async (profileId) => {
      const packet = await previewCanonProfilePacket(projectId, profileId);
      setPacketPreview(packet);
    },
    deleteMythosEntry,
    deletePatternEntry,
    renameProfile: async (profileId, name) => {
      await updateProfileMutation.mutateAsync({ profileId, name });
    },
    deleteProfile: async (profileId) => {
      await deleteProfileMutation.mutateAsync(profileId);
    },
    deleteAnnotation: async (annotationId) => {
      await deleteAnnotationMutation.mutateAsync(annotationId);
    },
    materializeMythos: async (extractionId) => {
      await materializeMythosMutation.mutateAsync(extractionId);
    },
    materializePatterns: async (extractionId) => {
      await materializePatternsMutation.mutateAsync(extractionId);
    },
  };
}
