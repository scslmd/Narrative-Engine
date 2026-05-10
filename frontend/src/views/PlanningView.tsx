import { useEffect, useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import {
  LayoutList, Map, GitBranch, Network, FileCheck, Plus,
  Lightbulb, Anchor, User, Book, Sparkles, ChevronRight, Network as NetworkIcon, Wand2
} from 'lucide-react';
import { ManifestViewer } from '../components/ManifestViewer';
import { RoleModelChecker } from '../components/checker';
import { StoryBranchesList } from '../components/branches';
import { DecisionTree } from '../components/decisions';
import { BrainstormWorkspace } from '../components/brainstorm/BrainstormWorkspace';
import { FoundationEditor } from '../components/foundation/FoundationEditor';
import { CharacterBuilder } from '../components/characters/CharacterBuilder';
import { RelationshipMapGraph } from '../components/characters/RelationshipMapGraph';
import { RelationshipList } from '../components/characters/RelationshipList';
import { RelationshipForm } from '../components/characters/RelationshipForm';
import { RelationshipEditModal } from '../components/characters/RelationshipEditModal';
import { WorldBibleWorkspace } from '../components/bible/WorldBibleWorkspace';
import FlowEditor from '../components/flow/FlowEditor';
import { PlanningTab } from '../components/planning/PlanningTab';
import { usePlanningController } from '../domains/planning/usePlanningController';
import { useFoundation } from '../hooks/useFoundation';
import { useBrainstorm } from '../hooks/useBrainstorm';
import { createFoundation } from '../services/foundation';
import { getCharacters, createCharacter, getCharacter, getCharacterRelationships, updateCharacter } from '../services/characters';
import { getRelationships, deleteRelationship } from '../services/relationships';
import { useRelationships } from '../hooks/useRelationships';
import api from '../lib/api';
import { getWorldBibleEntries, createWorldBibleEntry, getWorldBibleEntry, updateWorldBibleEntry } from '../services/worldBible';
import { createCanonAnnotation, getCanonAnnotations } from '../services/canonCustomization';
import { useCascadeDiscovery } from '../hooks/useCascadeDiscovery';
import { ScanDialog } from '../components/discovery/ScanDialog';
import { ReviewDialog } from '../components/discovery/ReviewDialog';
import type { CascadeScanRequest } from '../types/discovery';
import { getJobStatus } from '../services/discovery';

import type { CharacterProfile, RelationshipEdge, CharacterProfileCreateRequest, CharacterProfileUpdateRequest } from '../types/characters';
import type { FoundationCreateRequest, FoundationProfile, FoundationUpdateRequest } from '../types/foundation';
import type { WorldBibleEntry, WorldBibleEntryCreateRequest, WorldBibleEntryUpdateRequest } from '../types/bible';

import { useThemeStore } from '../stores/themeStore';
import { resolveEffectiveMode } from '../theme/theme';
import { EmptyState, WorkspaceStatus } from '../components/planning/ui';
import { getErrorMessage } from '../components/planning/utils';

type PlanningTab =
  | 'manifest'
  | 'planning'
  | 'flow'
  | 'arcs'
  | 'branches'
  | 'decisions'
  | 'checker'
  | 'brainstorm'
  | 'foundation'
  | 'characters'
  | 'world-bible'
  | 'relationships';

type CharacterEditorMode = 'list' | 'create' | 'edit';

const coreTabs: { key: PlanningTab; label: string; icon: typeof LayoutList }[] = [
  { key: 'manifest', label: 'Manifest', icon: LayoutList },
  { key: 'planning', label: 'Planning', icon: Map },
  { key: 'flow', label: 'Flow', icon: GitBranch },
  { key: 'arcs', label: 'Arcs', icon: Network },
  { key: 'branches', label: 'Branches', icon: GitBranch },
  { key: 'decisions', label: 'Decisions', icon: Sparkles },
  { key: 'checker', label: 'Checker', icon: FileCheck },
];

const contentTabs: { key: PlanningTab; label: string; icon: typeof Lightbulb }[] = [
  { key: 'brainstorm', label: 'Brainstorm', icon: Lightbulb },
  { key: 'foundation', label: 'Foundation', icon: Anchor },
  { key: 'characters', label: 'Characters', icon: User },
  { key: 'world-bible', label: 'World Bible', icon: Book },
  { key: 'relationships', label: 'Relationships', icon: NetworkIcon },
];

const tabActiveBgMap: Record<PlanningTab, string> = {
  manifest: 'bg-indigo-600',
  planning: 'bg-blue-600',
  flow: 'bg-blue-600',
  arcs: 'bg-purple-600',
  branches: 'bg-teal-600',
  decisions: 'bg-violet-600',
  checker: 'bg-rose-600',
  brainstorm: 'bg-amber-600',
  foundation: 'bg-emerald-600',
  characters: 'bg-pink-600',
  'world-bible': 'bg-indigo-600',
  relationships: 'bg-cyan-600',
};

const tabActiveBgDarkMap: Record<PlanningTab, string> = {
  manifest: 'bg-indigo-500',
  planning: 'bg-blue-500',
  flow: 'bg-blue-500',
  arcs: 'bg-purple-500',
  branches: 'bg-teal-500',
  decisions: 'bg-violet-500',
  checker: 'bg-rose-500',
  brainstorm: 'bg-amber-500',
  foundation: 'bg-emerald-500',
  characters: 'bg-pink-500',
  'world-bible': 'bg-indigo-500',
  relationships: 'bg-cyan-500',
};

export function PlanningView() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<PlanningTab>('manifest');
  const [characterEditorMode, setCharacterEditorMode] = useState<CharacterEditorMode>('list');
  const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(null);
  const [showCreateRelationship, setShowCreateRelationship] = useState(false);
  const [editingRelationship, setEditingRelationship] = useState<RelationshipEdge | null>(null);
  const [extractError, setExtractError] = useState<string | null>(null);
  const [showScanDialog, setShowScanDialog] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const { mode, _systemTick } = useThemeStore();
  void _systemTick;
  const isDark = resolveEffectiveMode(mode) === 'dark';

  const { items: brainstormItems, isLoading: brainstormLoading, addItem: addBrainstormItem, clusterItems: clusterBrainstormItems, promoteItem: promoteBrainstormItem } = useBrainstorm(projectId || '');

  const { profile: foundation, revisions, reviewCues, isLoading: foundationLoading, updateProfile: foundationUpdate } = useFoundation(projectId || '');

  const charactersQuery = useQuery({
    queryKey: ['planning', 'characters', projectId],
    queryFn: () => getCharacters(projectId || ''),
    enabled: Boolean(projectId) && (activeTab === 'characters' || activeTab === 'relationships'),
  });

  const worldBibleQuery = useQuery({
    queryKey: ['planning', 'world-bible', projectId],
    queryFn: () => getWorldBibleEntries(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'world-bible',
  });

  const planning = usePlanningController(activeTab);
  const canonAnnotationsQuery = useQuery({
    queryKey: ['canon', 'annotations', projectId],
    queryFn: () => getCanonAnnotations(projectId || ''),
    enabled: Boolean(projectId) && (activeTab === 'characters' || activeTab === 'world-bible'),
  });

  const relationshipsQuery = useQuery({
    queryKey: ['planning', 'relationships', projectId],
    queryFn: () => getRelationships(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'relationships',
  });
  const selectedCharacterQuery = useQuery({
    queryKey: ['planning', 'character', projectId, selectedCharacterId],
    queryFn: () => getCharacter(selectedCharacterId || '', projectId || ''),
    enabled: Boolean(projectId) && Boolean(selectedCharacterId) && activeTab === 'characters',
  });
  const selectedCharacterRelationshipsQuery = useQuery({
    queryKey: ['planning', 'character-relationships', projectId, selectedCharacterId],
    queryFn: () => getCharacterRelationships(selectedCharacterId || '', projectId || ''),
    enabled: Boolean(projectId) && Boolean(selectedCharacterId) && activeTab === 'characters',
  });
  const firstWorldEntryQuery = useQuery({
    queryKey: ['planning', 'world-bible-first', projectId],
    queryFn: async () => {
      const firstEntry = (worldBibleQuery.data ?? [])[0];
      if (!firstEntry) return null;
      return getWorldBibleEntry(firstEntry.entry_type, firstEntry.title, projectId || '');
    },
    enabled: Boolean(projectId) && activeTab === 'world-bible' && (worldBibleQuery.data ?? []).length > 0,
  });

  const relationshipDeleteMutation = useMutation({
    mutationFn: (edgeId: string) => deleteRelationship(edgeId, projectId || ''),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'relationships', projectId] });
    },
  });

  const relationshipHook = useRelationships(projectId || '');

  const { scanMutation, stagingQuery, approvalMutation, applyMutation, currentStageId, setCurrentStageId } = useCascadeDiscovery();

  async function handleExtractRelationships() {
    setExtractError(null);
    try {
      // Fetch chapter content from the project
      const response = await api.get(`/v1/projects/${projectId}/chapter-1`);
      const chapterText = response.data?.content || '';

      if (!chapterText.trim()) {
        setExtractError('No manuscript content found. Generate or import a chapter first.');
        return;
      }

      await relationshipHook.extractRelationships({
        manuscript_text: chapterText,
        character_ids: characters.map((c) => c.character_id),
      });
    } catch (err) {
      setExtractError(err instanceof Error ? err.message : 'Failed to extract relationships');
    }
  }

  const foundationSaveMutation = useMutation({
    mutationFn: (data: Partial<FoundationProfile>) => {
      const payload = omitKeys(data, ['project_id', 'foundation_id', 'version']);

      if (foundation) {
        return foundationUpdate(payload as FoundationUpdateRequest);
      }

      return createFoundation({
        project_id: projectId || '',
        ...(payload as Omit<FoundationCreateRequest, 'project_id'>),
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['foundation', projectId] });
      void queryClient.invalidateQueries({ queryKey: ['foundation-revisions', projectId] });
      void queryClient.invalidateQueries({ queryKey: ['foundation-review-cues', projectId] });
    },
  });

  const characterSaveMutation = useMutation({
    mutationFn: (character: Partial<CharacterProfile>) => {
      const payload = omitKeys(character, ['project_id', 'character_id', 'relationship_edges']);
      const characterId = character.character_id;

      if (characterEditorMode === 'edit' && selectedCharacterId) {
        return updateCharacter(
          selectedCharacterId,
          projectId || '',
          payload as CharacterProfileUpdateRequest,
        );
      }

      if (!characterId?.trim()) {
        throw new Error('Character ID is required.');
      }

      return createCharacter({
        project_id: projectId || '',
        character_id: characterId.trim(),
        ...(payload as Omit<CharacterProfileCreateRequest, 'project_id' | 'character_id'>),
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'characters', projectId] });
      setCharacterEditorMode('list');
      setSelectedCharacterId(null);
    },
  });

  const worldBibleAddMutation = useMutation({
    mutationFn: (request: WorldBibleEntryCreateRequest) => createWorldBibleEntry(request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'world-bible', projectId] });
    },
  });

  const worldBibleUpdateMutation = useMutation({
    mutationFn: ({
      entry,
      originalTitle,
    }: {
      entry: WorldBibleEntry;
      originalTitle: string;
    }) => {
      const updates = omitKeys(entry, ['entry_id', 'project_id', 'entry_type']);
      return updateWorldBibleEntry(
        entry.entry_type,
        originalTitle,
        projectId || '',
        updates as WorldBibleEntryUpdateRequest,
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'world-bible', projectId] });
    },
  });
  const canonAnnotationMutation = useMutation({
    mutationFn: createCanonAnnotation,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['canon', 'annotations', projectId] });
      void queryClient.invalidateQueries({ queryKey: ['canon', 'profiles', projectId] });
    },
  });

   const characters = useMemo(() => charactersQuery.data ?? [], [charactersQuery.data]);

  const characterNameMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const char of characters) {
      map[char.character_id] = char.display_name;
    }
    return map;
  }, [characters]);

  const relationships = useMemo(() => relationshipsQuery.data ?? [], [relationshipsQuery.data]);

  const handleOpenCharacter = useCallback((characterId: string) => {
    setSelectedCharacterId(characterId);
    setCharacterEditorMode('edit');
    setActiveTab('characters');
  }, []);

  const handleEditRelationship = useCallback((edgeId: string) => {
    const edge = relationships.find((r) => r.edge_id === edgeId);
    if (edge) {
      setEditingRelationship(edge);
    }
  }, [relationships]);

  const handleScanSubmit = useCallback(
    (request: CascadeScanRequest) => {
      scanMutation.mutate(request, {
        onSuccess: (data) => {
          setShowScanDialog(false);
          setActiveJobId(data.job_id);
        },
      });
    },
    [scanMutation],
  );

  const handleToggleApproval = useCallback(
    (entityId: string, approved: boolean) => {
      if (!currentStageId) return;
      approvalMutation.mutate({ stageId: currentStageId, updates: [{ entity_id: entityId, approved }] });
    },
    [currentStageId, approvalMutation],
  );

  const handleApply = useCallback(async () => {
    if (!currentStageId) return { characters_added: 0, relationships_added: 0, world_bible_added: 0, characters_enriched: 0 };
    return applyMutation.mutateAsync(currentStageId);
  }, [currentStageId, applyMutation]);

  const handleReviewClose = useCallback(() => {
    setCurrentStageId(null);
    setActiveJobId(null);
  }, [setCurrentStageId]);

  useEffect(() => {
    if (!activeJobId) return;
    const interval = setInterval(async () => {
      try {
        const status = await getJobStatus(activeJobId);
        if (status.status === 'completed' && status.stage_id) {
          setCurrentStageId(status.stage_id);
          clearInterval(interval);
        } else if (status.status === 'failed') {
          setActiveJobId(null);
          clearInterval(interval);
        }
      } catch {
        // Ignore polling errors
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [activeJobId, setCurrentStageId]);

  if (!projectId) {
    return <div className="text-sm text-subtle">No project selected</div>;
  }

  const selectedCharacter = selectedCharacterId
    ? characters.find((character) => character.character_id === selectedCharacterId)
    : null;
  const worldBibleEntries = worldBibleQuery.data ?? [];
  const canonAnnotations = canonAnnotationsQuery.data ?? [];

  const renderTabButton = (tab: { key: PlanningTab; label: string }, isCore: boolean) => {
    const isActive = activeTab === tab.key;
    const Icon = (isCore ? coreTabs : contentTabs).find(t => t.key === tab.key)?.icon;
    const activeBg = isDark ? tabActiveBgDarkMap[tab.key] : tabActiveBgMap[tab.key];

    return (
      <button
        key={tab.key}
        onClick={() => setActiveTab(tab.key)}
        aria-current={isActive ? 'page' : undefined}
        aria-pressed={isActive}
        aria-label={`Open ${tab.label} tab`}
        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-150 ${
          isActive
            ? `${activeBg} text-white shadow-sm`
            : isDark
              ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100/80'
        }`}
      >
        {Icon && <Icon className="w-3.5 h-3.5" />}
        <span>{tab.label}</span>
      </button>
    );
  };

  return (
    <div className="h-full flex flex-col">
      <div className={`border-b ${isDark ? 'border-slate-800 bg-slate-900/40' : 'border-slate-200 bg-white/60'} px-4 py-3`}>
        <div className="flex items-start gap-3 flex-wrap justify-between">
          <div>
            <h2 className={`text-sm font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>Planning Workspace</h2>
            <p className="text-xs text-muted">Choose a planning surface and keep decisions synchronized.</p>
          </div>
          <button
            type="button"
            onClick={() => projectId && navigate(`/workspace/${projectId}/generate`)}
            className="px-3 py-1.5 text-xs font-medium rounded-md bg-indigo-600 text-white shadow-sm"
          >
            Generate Story
          </button>
        </div>
        <div className="mt-3 flex items-center gap-1 flex-wrap" role="toolbar" aria-label="Planning sections">
          <div className="flex items-center gap-1 flex-wrap">
          <div className="flex items-center gap-1" role="group" aria-label="Core planning tabs">
            {coreTabs.map((tab) => renderTabButton(tab, true))}
          </div>
          <ChevronRight className="w-3.5 h-3.5 mx-1 text-muted" />
          <div className="flex items-center gap-1" role="group" aria-label="Content planning tabs">
            {contentTabs.map((tab) => renderTabButton(tab, false))}
          </div>
          </div>
        </div>
      </div>

      <main className="flex-1 overflow-y-auto p-4">
        {activeTab === 'manifest' && <ManifestViewer projectId={projectId} />}
        
        {activeTab === 'planning' && (
          <PlanningTab isDark={isDark} activeTab={activeTab} state={planning.state} callbacks={planning.callbacks} />
        )}

        {activeTab === 'flow' && (
          <div className="h-full">
            <FlowEditor projectId={projectId} />
          </div>
        )}

        {activeTab === 'arcs' && (
          <PlanningTab isDark={isDark} activeTab={activeTab} state={planning.state} callbacks={planning.callbacks} />
        )}

        {activeTab === 'branches' && (
          <div className="rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] p-5">
            <StoryBranchesList projectId={projectId} />
          </div>
        )}
        {activeTab === 'decisions' && (
          <div className="rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] p-5">
            <DecisionTree projectId={projectId} />
          </div>
        )}
        {activeTab === 'checker' && (
          <div className="rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] p-5">
            <RoleModelChecker projectId={projectId} />
          </div>
        )}

        {activeTab === 'brainstorm' && (
          <div className="h-full">
            {brainstormLoading ? (
              <WorkspaceStatus title="Loading brainstorm items" detail="Fetching project brainstorm data." />
            ) : (
              <BrainstormWorkspace
                projectId={projectId}
                items={brainstormItems}
                onItemAdd={(request) => void addBrainstormItem(request)}
                onClusterCreate={(itemIds) => void clusterBrainstormItems(itemIds)}
                onPromote={async ({ item_id, target_object_kind, target_object_id }) => {
                await promoteBrainstormItem(item_id, target_object_kind, target_object_id);
              }}
              />
            )}
          </div>
        )}

        {activeTab === 'foundation' && (
          <div className="h-full">
            {foundationLoading ? (
              <WorkspaceStatus title="Loading foundation" detail="Fetching the active foundation profile." />
            ) : (
              <FoundationEditor
                projectId={projectId}
                foundation={foundation ?? undefined}
                onSave={(updates) => foundationSaveMutation.mutate(updates)}
                revisions={revisions}
                reviewCues={reviewCues}
              />
            )}
          </div>
        )}

        {activeTab === 'characters' && (
          <div className="h-full">
            {charactersQuery.isLoading ? (
              <WorkspaceStatus title="Loading characters" detail="Fetching character profiles for this project." />
            ) : charactersQuery.error ? (
              <WorkspaceStatus title="Could not load characters" detail={getErrorMessage(charactersQuery.error)} tone="error" />
            ) : characterEditorMode === 'list' ? (
              <div className="rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] p-5">
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <h2 className={`text-lg font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>Characters</h2>
                    <p className={`text-sm mt-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                      {characters.length} profiles in this project
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedCharacterId(null);
                      setCharacterEditorMode('create');
                    }}
                    className="px-3 py-1.5 bg-gradient-to-r from-pink-500 to-pink-600 text-white text-xs font-medium rounded-lg hover:from-pink-600 hover:to-pink-700 shadow-sm transition-all"
                  >
                    + New Character
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {characters.map((character) => (
                    <button
                      key={character.character_id}
                      onClick={() => {
                        setSelectedCharacterId(character.character_id);
                        setCharacterEditorMode('edit');
                      }}
                      className={`text-left rounded-lg border p-4 cursor-pointer transition-all duration-150 ${
                        isDark
                          ? 'bg-slate-900 border-slate-800 hover:border-slate-700 hover:shadow-card'
                          : 'bg-white border-slate-200 hover:border-pink-300 hover:shadow-card'
                      }`}
                    >
                      <h3 className={`font-medium ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>{character.display_name}</h3>
                      <p className="text-sm mt-1 text-body">{character.role_in_story}</p>
                    </button>
                  ))}
                </div>

                {characters.length === 0 && (
                  <EmptyState text="No character profiles configured. Create a character to start building the cast." />
                )}
              </div>
            ) : characterEditorMode === 'create' ? (
              <CharacterBuilder
                projectId={projectId}
                onSave={(character) => characterSaveMutation.mutate(character)}
                canonAnnotations={canonAnnotations}
                onAnnotateField={async (targetId, fieldPath, annotationKind, note) => {
                  await canonAnnotationMutation.mutateAsync({
                    project_id: projectId,
                    target_kind: 'character',
                    target_id: targetId,
                    field_path: fieldPath,
                    annotation_kind: annotationKind,
                    note,
                  });
                }}
                onCancel={() => {
                  setCharacterEditorMode('list');
                  setSelectedCharacterId(null);
                }}
              />
            ) : selectedCharacter ? (
              <CharacterBuilder
                projectId={projectId}
                character={selectedCharacterQuery.data ?? selectedCharacter}
                onSave={(character) => characterSaveMutation.mutate(character)}
                canonAnnotations={canonAnnotations}
                onAnnotateField={async (targetId, fieldPath, annotationKind, note) => {
                  await canonAnnotationMutation.mutateAsync({
                    project_id: projectId,
                    target_kind: 'character',
                    target_id: targetId,
                    field_path: fieldPath,
                    annotation_kind: annotationKind,
                    note,
                  });
                }}
                onCancel={() => {
                  setCharacterEditorMode('list');
                  setSelectedCharacterId(null);
                }}
              />
            ) : (
              <WorkspaceStatus
                title="Character not found"
                detail="The selected character is no longer available. Return to the list and pick another profile."
                tone="error"
              />
            )}
            {selectedCharacterRelationshipsQuery.data && selectedCharacterRelationshipsQuery.data.length > 0 && (
              <p className="px-4 pb-2 text-xs text-subtle">
                Selected character relationships: {selectedCharacterRelationshipsQuery.data.length}
              </p>
            )}
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="h-full flex flex-col">
            {relationshipsQuery.isLoading ? (
              <WorkspaceStatus title="Loading relationships" detail="Fetching character relationships for this project." />
            ) : relationshipsQuery.error ? (
              <WorkspaceStatus title="Could not load relationships" detail={getErrorMessage(relationshipsQuery.error)} tone="error" />
            ) : showCreateRelationship ? (
              <div className="flex flex-col h-full">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between shrink-0">
                  <h2 className={`text-base font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    New Relationship
                  </h2>
                </div>

                <div className="flex-1 overflow-y-auto p-4">
                  <RelationshipForm
                    characters={characters}
                    isSubmitting={relationshipHook.isCreating}
                    isDark={isDark}
                    onSubmit={async (data) => {
                      await relationshipHook.createRelationship(data);
                      setShowCreateRelationship(false);
                    }}
                    onCancel={() => setShowCreateRelationship(false)}
                  />
                </div>
              </div>
            ) : (
              <div className="flex flex-col h-full">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between shrink-0">
                  <h2 className={`text-base font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    Relationship Map
                  </h2>
                 <div className="flex items-center gap-2">
                      <span className="text-xs text-subtle">
                        {relationships.length} relationships
                      </span>
                      <button
                        onClick={handleExtractRelationships}
                        disabled={relationshipHook.isExtracting || characters.length < 2}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg bg-violet-600 text-white hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Wand2 className="w-3.5 h-3.5" />
                        {relationshipHook.isExtracting ? 'Analyzing...' : 'AI Extract'}
                      </button>
                      <button
                        onClick={() => setShowCreateRelationship(true)}
                        disabled={characters.length < 2}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg bg-cyan-600 text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        Add Relationship
                      </button>
                      <button
                        onClick={() => setShowScanDialog(true)}
                        className="px-2.5 py-1 text-xs font-medium rounded-lg bg-purple-600 text-white hover:bg-purple-700"
                      >
                        Scan Manuscript
                      </button>
                    </div>
                </div>

                {extractError && (
                  <div className="px-4 py-2 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
                    <p className="text-xs text-red-700 dark:text-red-400">{extractError}</p>
                  </div>
                )}

                <div className="flex-1 overflow-y-auto p-4">
                  <RelationshipMapGraph
                    characters={characters}
                    relationships={relationships}
                    onDeleteRelationship={(edgeId) => {
                      void relationshipDeleteMutation.mutate(edgeId);
                    }}
                    onOpenCharacter={handleOpenCharacter}
                    onEditRelationship={handleEditRelationship}
                    className="h-[350px]"
                  />
                </div>

                <div className="shrink-0 px-4 pb-4">
                  <RelationshipList
                    relationships={relationships}
                    characterNames={characterNameMap}
                    onDeleteRelationship={(edgeId) => {
                      void relationshipDeleteMutation.mutate(edgeId);
                    }}
                    onUpdateRelationship={handleEditRelationship}
                    className="h-[250px]"
                  />
                </div>

                {editingRelationship && (
                  <RelationshipEditModal
                    relationship={editingRelationship}
                    characters={characters}
                    isSaving={relationshipHook.isUpdating}
                    isDeleting={relationshipHook.isDeleting}
                    isOpen={!!editingRelationship}
                    onClose={() => setEditingRelationship(null)}
                    onSave={async (edgeId, data) => {
                      await relationshipHook.updateRelationship(edgeId, data);
                    }}
                    onDelete={async (edgeId) => {
                      await relationshipHook.deleteRelationship(edgeId);
                    }}
                    isDark={isDark}
                  />
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'world-bible' && (
          <div className="h-full">
            {worldBibleQuery.isLoading ? (
              <WorkspaceStatus title="Loading world bible" detail="Fetching world bible entries for this project." />
            ) : worldBibleQuery.error ? (
              <WorkspaceStatus title="Could not load world bible" detail={getErrorMessage(worldBibleQuery.error)} tone="error" />
            ) : (
              <>
                <WorldBibleWorkspace
                  projectId={projectId}
                  entries={worldBibleEntries}
                  canonAnnotations={canonAnnotations}
                  onAnnotateField={async (targetId, fieldPath, annotationKind, note) => {
                    await canonAnnotationMutation.mutateAsync({
                      project_id: projectId,
                      target_kind: 'world_bible',
                      target_id: targetId,
                      field_path: fieldPath,
                      annotation_kind: annotationKind,
                      note,
                    });
                  }}
                  onEntryAdd={(request) => worldBibleAddMutation.mutate(request)}
                  onEntryUpdate={(entry, originalTitle) =>
                    worldBibleUpdateMutation.mutate({ entry, originalTitle })
                  }
                />
                {firstWorldEntryQuery.data && (
                  <p className="px-4 pb-2 text-xs text-subtle">
                    Loaded world entry detail: {firstWorldEntryQuery.data.title}
                  </p>
                )}
              </>
            )}
          </div>
        )}

        {showScanDialog && (
          <ScanDialog projectId={projectId} onSubmit={handleScanSubmit} onClose={() => setShowScanDialog(false)} isLoading={scanMutation.isPending} />
        )}

        {activeJobId && !currentStageId && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
              <p className="text-lg font-medium text-gray-900 dark:text-white">Scanning manuscript...</p>
              <p className="text-sm text-gray-500 mt-2">This may take a moment depending on text length.</p>
            </div>
          </div>
        )}

        {currentStageId && stagingQuery.data && (
          <ReviewDialog
            stageId={currentStageId}
            characters={stagingQuery.data.characters}
            relationships={stagingQuery.data.relationships}
            worldBible={stagingQuery.data.world_bible}
            onToggleApproval={handleToggleApproval}
            onApply={handleApply}
            onClose={handleReviewClose}
            applyLoading={applyMutation.isPending}
          />
        )}
      </main>
    </div>
  );
}

function omitKeys<T extends object>(value: T, keys: string[]): Partial<T> {
  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>).filter(([key]) => !keys.includes(key)),
  ) as Partial<T>;
}
