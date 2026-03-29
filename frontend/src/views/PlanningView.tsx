import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { ManifestViewer } from '../components/ManifestViewer';
import { SequenceViewer } from '../components/SequenceViewer';
import { InspectMode } from '../components/inspect';
import { FindingsList } from '../components/review';
import { RoleModelChecker } from '../components/checker';
import { StoryBranchesList } from '../components/branches';
import { DecisionTree } from '../components/decisions';
import { InspectRunLinksList } from '../components/inspectLinks';
import { BrainstormWorkspace } from '../components/brainstorm/BrainstormWorkspace';
import { FoundationEditor } from '../components/foundation/FoundationEditor';
import { CharacterBuilder } from '../components/characters/CharacterBuilder';
import { WorldBibleWorkspace } from '../components/bible/WorldBibleWorkspace';
import { getBrainstormItems, createBrainstormItem, clusterBrainstormItems } from '../services/brainstorm';
import { getFoundation, createFoundation, updateFoundation } from '../services/foundation';
import { getCharacters, createCharacter, updateCharacter } from '../services/characters';
import { getWorldBibleEntries, createWorldBibleEntry, updateWorldBibleEntry } from '../services/worldBible';
import type { BrainstormItemCreateRequest } from '../types/brainstorm';
import type { CharacterProfile, CharacterProfileCreateRequest, CharacterProfileUpdateRequest } from '../types/characters';
import type { FoundationCreateRequest, FoundationProfile, FoundationUpdateRequest } from '../types/foundation';
import type { WorldBibleEntry, WorldBibleEntryCreateRequest, WorldBibleEntryUpdateRequest } from '../types/bible';

type PlanningTab =
  | 'manifest'
  | 'sequences'
  | 'checker'
  | 'branches'
  | 'decisions'
  | 'brainstorm'
  | 'foundation'
  | 'characters'
  | 'world-bible';

type CharacterEditorMode = 'list' | 'create' | 'edit';

export function PlanningView() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<PlanningTab>('manifest');
  const [characterEditorMode, setCharacterEditorMode] = useState<CharacterEditorMode>('list');
  const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(null);

  const brainstormQuery = useQuery({
    queryKey: ['planning', 'brainstorm-items', projectId],
    queryFn: () => getBrainstormItems(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'brainstorm',
  });

  const foundationQuery = useQuery({
    queryKey: ['planning', 'foundation', projectId],
    queryFn: () => getFoundation(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'foundation',
  });

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

  const brainstormCreateMutation = useMutation({
    mutationFn: (request: BrainstormItemCreateRequest) => createBrainstormItem(request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'brainstorm-items', projectId] });
    },
  });

  const brainstormClusterMutation = useMutation({
    mutationFn: (itemIds: string[]) =>
      clusterBrainstormItems({
        project_id: projectId || '',
        item_ids: itemIds,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'brainstorm-items', projectId] });
    },
  });

  const foundationSaveMutation = useMutation({
    mutationFn: (foundation: Partial<FoundationProfile>) => {
      const payload = omitKeys(foundation, ['project_id', 'foundation_id', 'version']);
      const activeFoundation = foundationQuery.data?.active_profile;

      if (activeFoundation) {
        return updateFoundation(projectId || '', payload as FoundationUpdateRequest);
      }

      return createFoundation({
        project_id: projectId || '',
        ...(payload as Omit<FoundationCreateRequest, 'project_id'>),
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'foundation', projectId] });
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

  if (!projectId) {
    return <div className="text-gray-500">No project selected</div>;
  }

  const brainstormItems = brainstormQuery.data ?? [];
  const foundation = foundationQuery.data?.active_profile ?? undefined;
  const characters = charactersQuery.data ?? [];
  const selectedCharacter = selectedCharacterId
    ? characters.find((character) => character.character_id === selectedCharacterId)
    : null;
  const worldBibleEntries = worldBibleQuery.data ?? [];

  return (
    <div className="h-full flex flex-col">
      <header className="border-b px-4 py-2 bg-white">
        <nav className="flex gap-4 flex-wrap">
          <button
            onClick={() => setActiveTab('manifest')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'manifest' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Manifest
          </button>
          <button
            onClick={() => setActiveTab('sequences')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'sequences' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Sequences
          </button>
          <button
            onClick={() => setActiveTab('branches')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'branches' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Branches
          </button>
          <button
            onClick={() => setActiveTab('decisions')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'decisions' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Decisions
          </button>
          <button
            onClick={() => setActiveTab('checker')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'checker' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Checker
          </button>

          <div className="w-px h-6 bg-gray-300 mx-2"></div>

          <button
            onClick={() => setActiveTab('brainstorm')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'brainstorm' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Brainstorm
          </button>
          <button
            onClick={() => setActiveTab('foundation')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'foundation' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Foundation
          </button>
          <button
            onClick={() => setActiveTab('characters')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'characters' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Characters
          </button>
          <button
            onClick={() => setActiveTab('world-bible')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'world-bible' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            World Bible
          </button>
        </nav>
      </header>

      <main className="flex-1 overflow-y-auto pr-2">
        {activeTab === 'manifest' && <ManifestViewer projectId={projectId} />}
        {activeTab === 'sequences' && <SequenceViewer projectId={projectId} />}
        {activeTab === 'branches' && (
          <div className="p-4">
            <StoryBranchesList projectId={projectId} />
          </div>
        )}
        {activeTab === 'decisions' && (
          <div className="p-4">
            <DecisionTree projectId={projectId} />
          </div>
        )}
        {activeTab === 'checker' && (
          <div className="p-4">
            <RoleModelChecker projectId={projectId} />
          </div>
        )}

        {activeTab === 'brainstorm' && (
          <div className="h-full">
            {brainstormQuery.isLoading ? (
              <WorkspaceStatus title="Loading brainstorm items" detail="Fetching project brainstorm data." />
            ) : brainstormQuery.error ? (
              <WorkspaceStatus title="Could not load brainstorm" detail={getErrorMessage(brainstormQuery.error)} tone="error" />
            ) : (
              <BrainstormWorkspace
                projectId={projectId}
                items={brainstormItems}
                onItemAdd={(request) => brainstormCreateMutation.mutate(request)}
                onClusterCreate={(itemIds) => brainstormClusterMutation.mutate(itemIds)}
              />
            )}
          </div>
        )}

        {activeTab === 'foundation' && (
          <div className="h-full">
            {foundationQuery.isLoading ? (
              <WorkspaceStatus title="Loading foundation" detail="Fetching the active foundation profile." />
            ) : foundationQuery.error ? (
              <WorkspaceStatus title="Could not load foundation" detail={getErrorMessage(foundationQuery.error)} tone="error" />
            ) : (
              <FoundationEditor
                projectId={projectId}
                foundation={foundation}
                onSave={(updates) => foundationSaveMutation.mutate(updates)}
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
              <div className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Characters</h2>
                    <p className="text-sm text-gray-500 mt-1">
                      {characters.length} profiles in this project
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedCharacterId(null);
                      setCharacterEditorMode('create');
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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
                      className="text-left bg-white border border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-400 hover:shadow-md transition-all"
                    >
                      <h3 className="font-medium text-gray-900">{character.display_name}</h3>
                      <p className="text-sm text-gray-600">{character.role_in_story}</p>
                    </button>
                  ))}
                </div>

                {characters.length === 0 && (
                  <div className="text-center py-12 text-gray-500">
                    <p>No characters yet</p>
                    <p className="text-sm mt-2">Create a character to start building the cast.</p>
                  </div>
                )}
              </div>
            ) : characterEditorMode === 'create' ? (
              <CharacterBuilder
                projectId={projectId}
                onSave={(character) => characterSaveMutation.mutate(character)}
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

export function WritingView() {
  const { projectId } = useParams<{ projectId: string }>();

  if (!projectId) {
    return <div className="text-gray-500">No project selected</div>;
  }

  return (
    <div className="h-full overflow-y-auto pr-2">
      <SequenceViewer projectId={projectId} />
    </div>
  );
}

export function ReviewView() {
  const { projectId } = useParams<{ projectId: string }>();
  const [activeTab, setActiveTab] = useState<'findings' | 'links'>('findings');

  if (!projectId) {
    return <div className="text-gray-500">No project selected</div>;
  }

  return (
    <div className="h-full flex flex-col">
      <header className="border-b px-4 py-2 bg-white">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('findings')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'findings' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Findings
          </button>
          <button
            onClick={() => setActiveTab('links')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'links' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Inspect Run Links
          </button>
        </nav>
      </header>

      <main className="flex-1 overflow-y-auto pr-2">
        {activeTab === 'findings' && (
          <div className="p-4">
            <FindingsList projectId={projectId} />
          </div>
        )}
        {activeTab === 'links' && (
          <div className="p-4">
            <InspectRunLinksList projectId={projectId} />
          </div>
        )}
      </main>
    </div>
  );
}

export function InspectView() {
  const { projectId } = useParams<{ projectId: string; jobId?: string }>();

  if (!projectId) {
    return <div className="text-gray-500">No project selected</div>;
  }

  return (
    <div className="h-full">
      <InspectMode />
    </div>
  );
}

function WorkspaceStatus({
  title,
  detail,
  tone = 'neutral',
}: {
  title: string;
  detail: string;
  tone?: 'neutral' | 'error';
}) {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className={`max-w-md rounded-lg border p-6 text-center ${tone === 'error' ? 'border-red-200 bg-red-50 text-red-900' : 'border-gray-200 bg-white text-gray-900'}`}>
        <p className="text-lg font-semibold">{title}</p>
        <p className="mt-2 text-sm text-gray-600">{detail}</p>
      </div>
    </div>
  );
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return 'An unexpected error occurred.';
}

function omitKeys<T extends object>(value: T, keys: string[]): Partial<T> {
  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>).filter(([key]) => !keys.includes(key)),
  ) as Partial<T>;
}
