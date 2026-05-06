import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import {
  LayoutList, Map, GitBranch, Network, FileCheck,
  Lightbulb, Anchor, User, Book, Sparkles, ChevronRight, Network as NetworkIcon
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
import { WorldBibleWorkspace } from '../components/bible/WorldBibleWorkspace';
import FlowEditor from '../components/flow/FlowEditor';
import { PlanningTab } from '../components/planning/PlanningTab';
import { usePlanningTab } from '../hooks/usePlanningTab';
import { useFoundation } from '../hooks/useFoundation';
import { useBrainstorm } from '../hooks/useBrainstorm';
import { createFoundation } from '../services/foundation';
import { getCharacters, createCharacter, updateCharacter } from '../services/characters';
import { getRelationships, deleteRelationship } from '../services/relationships';
import { getWorldBibleEntries, createWorldBibleEntry, updateWorldBibleEntry } from '../services/worldBible';
import { createCanonAnnotation, getCanonAnnotations } from '../services/canonCustomization';

import type { CharacterProfile, CharacterProfileCreateRequest, CharacterProfileUpdateRequest } from '../types/characters';
import type { FoundationCreateRequest, FoundationProfile, FoundationUpdateRequest } from '../types/foundation';
import type { WorldBibleEntry, WorldBibleEntryCreateRequest, WorldBibleEntryUpdateRequest } from '../types/bible';

import { useThemeStore } from '../stores/themeStore';
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
  const { mode } = useThemeStore();
  const isDark = mode === 'dark';

  const { items: brainstormItems, isLoading: brainstormLoading, addItem: addBrainstormItem, clusterItems: clusterBrainstormItems, promoteItem: promoteBrainstormItem } = useBrainstorm(projectId || '');

  const { profile: foundation, revisions, reviewCues, isLoading: foundationLoading, updateProfile: foundationUpdate } = useFoundation(projectId || '');

  const charactersQuery = useQuery({
    queryKey: ['planning', 'characters', projectId],
    queryFn: () => getCharacters(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'characters',
  });

  const worldBibleQuery = useQuery({
    queryKey: ['planning', 'world-bible', projectId],
    queryFn: () => getWorldBibleEntries(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'world-bible',
  });

  const planning = usePlanningTab(activeTab);
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

  const relationshipDeleteMutation = useMutation({
    mutationFn: (edgeId: string) => deleteRelationship(edgeId, projectId || ''),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'relationships', projectId] });
    },
  });

  const foundationSaveMutation = useMutation({
    mutationFn: (foundation: Partial<FoundationProfile>) => {
      const payload = omitKeys(foundation, ['project_id', 'foundation_id', 'version']);

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

  const relationships = relationshipsQuery.data ?? [];

  if (!projectId) {
    return <div className={`text-sm ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>No project selected</div>;
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
      <div className={`border-b ${isDark ? 'border-slate-800 bg-slate-900/40' : 'border-slate-200 bg-white/60'} px-4 py-2`}>
        <div className="flex items-center gap-1 flex-wrap justify-between">
          <button
            type="button"
            onClick={() => projectId && navigate(`/workspace/${projectId}/generate`)}
            className="px-3 py-1.5 text-xs font-medium rounded-md bg-indigo-600 text-white"
          >
            Generate Story
          </button>
          <div className="flex items-center gap-1 flex-wrap">
          <div className="flex items-center gap-1">
            {coreTabs.map((tab) => renderTabButton(tab, true))}
          </div>
          <ChevronRight className={`w-3.5 h-3.5 mx-1 ${isDark ? 'text-slate-600' : 'text-slate-400'}`} />
          <div className="flex items-center gap-1">
            {contentTabs.map((tab) => renderTabButton(tab, false))}
          </div>
          </div>
        </div>
      </div>

      <main className="flex-1 overflow-y-auto">
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
          <div className="p-5">
            <StoryBranchesList projectId={projectId} />
          </div>
        )}
        {activeTab === 'decisions' && (
          <div className="p-5">
            <DecisionTree projectId={projectId} />
          </div>
        )}
        {activeTab === 'checker' && (
          <div className="p-5">
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
              <div className="p-5">
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
                      <p className={`text-sm mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{character.role_in_story}</p>
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
                character={selectedCharacter}
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
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="h-full flex flex-col">
            {relationshipsQuery.isLoading ? (
              <WorkspaceStatus title="Loading relationships" detail="Fetching character relationships for this project." />
            ) : relationshipsQuery.error ? (
              <WorkspaceStatus title="Could not load relationships" detail={getErrorMessage(relationshipsQuery.error)} tone="error" />
            ) : (
              <div className="flex flex-col h-full">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between shrink-0">
                  <h2 className={`text-base font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    Relationship Map
                  </h2>
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                    {relationships.length} relationships
                  </span>
                </div>

                <div className="flex-1 overflow-y-auto p-4">
                  <RelationshipMapGraph
                    characters={characters}
                    relationships={relationships}
                    onDeleteRelationship={(edgeId) => {
                      void relationshipDeleteMutation.mutate(edgeId);
                    }}
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
                    className="h-[250px]"
                  />
                </div>
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
            )}
          </div>
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
