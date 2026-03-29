import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { ManifestViewer } from '../components/ManifestViewer';
import { RoleModelChecker } from '../components/checker';
import { StoryBranchesList } from '../components/branches';
import { DecisionTree } from '../components/decisions';
import { BrainstormWorkspace } from '../components/brainstorm/BrainstormWorkspace';
import { FoundationEditor } from '../components/foundation/FoundationEditor';
import { CharacterBuilder } from '../components/characters/CharacterBuilder';
import { WorldBibleWorkspace } from '../components/bible/WorldBibleWorkspace';
import FlowEditor from '../components/flow/FlowEditor';
import { getBrainstormItems, createBrainstormItem, clusterBrainstormItems } from '../services/brainstorm';
import { getFoundation, createFoundation, updateFoundation } from '../services/foundation';
import { getCharacters, createCharacter, updateCharacter } from '../services/characters';
import { getWorldBibleEntries, createWorldBibleEntry, updateWorldBibleEntry } from '../services/worldBible';
import {
  getSequencePlans,
  getChapterPlans,
  getScenePlans,
  getPlanningDependencies,
  getChapterPackets,
} from '../services/planning';
import {
  getArcCandidates,
  getArcSelections,
  getArcStageMaps,
  getSelectedArc,
  getStageMapForArc,
} from '../services/arcs';
import type { BrainstormItemCreateRequest } from '../types/brainstorm';
import type { CharacterProfile, CharacterProfileCreateRequest, CharacterProfileUpdateRequest } from '../types/characters';
import type { FoundationCreateRequest, FoundationProfile, FoundationUpdateRequest } from '../types/foundation';
import type { WorldBibleEntry, WorldBibleEntryCreateRequest, WorldBibleEntryUpdateRequest } from '../types/bible';

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

  const sequencePlansQuery = useQuery({
    queryKey: ['planning-sequence-plans', projectId],
    queryFn: () => getSequencePlans(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'planning',
  });

  const chapterPlansQuery = useQuery({
    queryKey: ['planning-chapter-plans', projectId],
    queryFn: () => getChapterPlans(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'planning',
  });

  const scenePlansQuery = useQuery({
    queryKey: ['planning-scene-plans', projectId],
    queryFn: () => getScenePlans(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'planning',
  });

  const dependenciesQuery = useQuery({
    queryKey: ['planning-dependencies', projectId],
    queryFn: () => getPlanningDependencies(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'planning',
  });

  const chapterPacketsQuery = useQuery({
    queryKey: ['planning-chapter-packets', projectId],
    queryFn: () => getChapterPackets(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'planning',
  });

  const arcCandidatesQuery = useQuery({
    queryKey: ['arc-candidates', projectId],
    queryFn: () => getArcCandidates(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'arcs',
  });

  const arcSelectionsQuery = useQuery({
    queryKey: ['arc-selections', projectId],
    queryFn: () => getArcSelections(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'arcs',
  });

  const arcStageMapsQuery = useQuery({
    queryKey: ['arc-stage-maps', projectId],
    queryFn: () => getArcStageMaps(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'arcs',
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

  const sequencePlans = sequencePlansQuery.data ?? [];
  const chapterPlans = chapterPlansQuery.data ?? [];
  const scenePlans = scenePlansQuery.data ?? [];
  const dependencies = dependenciesQuery.data ?? [];
  const chapterPackets = chapterPacketsQuery.data ?? [];

  const arcCandidates = arcCandidatesQuery.data ?? [];
  const arcSelections = arcSelectionsQuery.data ?? [];
  const arcStageMaps = arcStageMapsQuery.data ?? [];
  const selectedArc = arcSelections.length > 0 ? getSelectedArc(arcSelections, projectId) : null;
  const selectedArcStageMap = selectedArc ? getStageMapForArc(arcStageMaps, selectedArc.arc_id) : undefined;

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
            onClick={() => setActiveTab('planning')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'planning' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Planning
          </button>
          <button
            onClick={() => setActiveTab('flow')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'flow' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Flow
          </button>
          <button
            onClick={() => setActiveTab('arcs')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'arcs' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Arcs
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
        
        {activeTab === 'planning' && (
          <div className="p-4 space-y-6">
            <section>
              <h3 className="font-semibold text-gray-900 mb-2">Sequences ({sequencePlans.length})</h3>
              {sequencePlansQuery.isLoading ? (
                <WorkspaceStatus title="Loading sequences" detail="Fetching sequence plans..." />
              ) : sequencePlans.length === 0 ? (
                <p className="text-sm text-gray-500">No sequence plans configured. Create a sequence to define the high-level story structure.</p>
              ) : (
                <div className="space-y-2">
                  {sequencePlans.map((seq) => (
                    <div key={seq.sequence_id} className="p-3 bg-white border rounded">
                      <div className="font-medium text-gray-900">{seq.title}</div>
                      {seq.summary && <p className="text-sm text-gray-600 mt-1">{seq.summary}</p>}
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="font-semibold text-gray-900 mb-2">Chapters ({chapterPlans.length})</h3>
              {chapterPlansQuery.isLoading ? (
                <WorkspaceStatus title="Loading chapters" detail="Fetching chapter plans..." />
              ) : chapterPlans.length === 0 ? (
                <p className="text-sm text-gray-500">No chapter plans configured. Chapters will appear once sequence planning is complete.</p>
              ) : (
                <div className="space-y-2">
                  {chapterPlans.map((chap) => (
                    <div key={chap.chapter_id} className="p-3 bg-white border rounded">
                      <div className="font-medium text-gray-900">{chap.title}</div>
                      {chap.sequence_id && <span className="text-xs text-gray-500">Sequence: {chap.sequence_id}</span>}
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="font-semibold text-gray-900 mb-2">Scenes ({scenePlans.length})</h3>
              {scenePlansQuery.isLoading ? (
                <WorkspaceStatus title="Loading scenes" detail="Fetching scene plans..." />
              ) : scenePlans.length === 0 ? (
                <p className="text-sm text-gray-500">No scene plans configured. Scenes will appear once chapter planning is complete.</p>
              ) : (
                <div className="space-y-2">
                  {scenePlans.map((scene) => (
                    <div key={scene.scene_id} className="p-3 bg-white border rounded">
                      <div className="font-medium text-gray-900">{scene.title}</div>
                      {scene.chapter_id && <span className="text-xs text-gray-500">Chapter: {scene.chapter_id}</span>}
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="font-semibold text-gray-900 mb-2">Dependencies ({dependencies.length})</h3>
              {dependenciesQuery.isLoading ? (
                <WorkspaceStatus title="Loading dependencies" detail="Fetching planning dependencies..." />
              ) : dependencies.length === 0 ? (
                <p className="text-sm text-gray-500">No dependencies defined. Dependencies track relationships between planning artifacts.</p>
              ) : (
                <div className="space-y-2">
                  {dependencies.map((dep) => (
                    <div key={dep.dependency_id} className="p-3 bg-white border rounded text-sm">
                      <span className="text-gray-700">{dep.upstream_id}</span>
                      <span className="mx-2">→</span>
                      <span className="text-gray-700">{dep.downstream_id}</span>
                      {dep.reason && (
                        <div className="mt-1 text-xs text-gray-500 italic">{dep.reason}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="font-semibold text-gray-900 mb-2">Chapter Packets ({chapterPackets.length})</h3>
              {chapterPacketsQuery.isLoading ? (
                <WorkspaceStatus title="Loading chapter packets" detail="Fetching chapter packets..." />
              ) : chapterPackets.length === 0 ? (
                <p className="text-sm text-gray-500">No chapter packets configured. Packets will appear once chapters are ready for drafting.</p>
              ) : (
                <div className="space-y-2">
                  {chapterPackets.map((packet) => (
                    <div key={packet.packet_id} className="p-3 bg-white border rounded">
                      <div className="font-medium text-gray-900">{packet.chapter_id}</div>
                      <span className="text-xs text-gray-500">{packet.included_reference_ids.length} references included</span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}

        {activeTab === 'flow' && (
          <div className="h-full">
            <FlowEditor projectId={projectId} />
          </div>
        )}

        {activeTab === 'arcs' && (
          <div className="p-4 space-y-6">
            <section>
              <h3 className="font-semibold text-gray-900 mb-2">Selected Arc</h3>
              {arcSelectionsQuery.isLoading ? (
                <WorkspaceStatus title="Loading arc selections" detail="Fetching selected arcs..." />
              ) : selectedArc ? (
                <div className="p-4 bg-green-50 border border-green-200 rounded">
                  <div className="font-medium text-gray-900">{selectedArc.arc_id}</div>
                  {selectedArc.summary && <p className="text-sm text-gray-600 mt-1">{selectedArc.summary}</p>}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No arc selected. Arc selections define the narrative trajectory for this project.</p>
              )}
            </section>

            {selectedArc && selectedArcStageMap && (
              <section>
                <h3 className="font-semibold text-gray-900 mb-2">Selected Arc Stage Map</h3>
                {arcStageMapsQuery.isLoading ? (
                  <WorkspaceStatus title="Loading stage maps" detail="Fetching arc stage mappings..." />
                ) : (
                  <div className="p-4 bg-white border rounded">
                    <div className="text-sm text-gray-600">
                      <div>Stage Kinds: {selectedArcStageMap.stage_kinds.join(', ')}</div>
                      {selectedArcStageMap.notes && (
                        <div className="mt-2 italic">{selectedArcStageMap.notes}</div>
                      )}
                    </div>
                  </div>
                )}
              </section>
            )}

            <section>
              <h3 className="font-semibold text-gray-900 mb-2">All Arc Candidates ({arcCandidates.length})</h3>
              {arcCandidatesQuery.isLoading ? (
                <WorkspaceStatus title="Loading arc candidates" detail="Fetching all arc candidates..." />
              ) : arcCandidates.length === 0 ? (
                <p className="text-sm text-gray-500">No arc candidates available. Arcs will appear once foundation and character work is complete.</p>
              ) : (
                <div className="space-y-2">
                  {arcCandidates.map((candidate) => {
                    const isSelected = selectedArc?.arc_id === candidate.arc_id;
                    return (
                      <div key={candidate.arc_id} className={`p-3 border rounded ${isSelected ? 'bg-green-50 border-green-300' : 'bg-white'}`}>
                        <div className="font-medium text-gray-900">{candidate.name}</div>
                        {candidate.summary && <p className="text-sm text-gray-600 mt-1">{candidate.summary}</p>}
                        {isSelected && <span className="inline-block mt-2 px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">Selected</span>}
                      </div>
                    );
                  })}
                </div>
              )}
            </section>
          </div>
        )}

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
                    <p>No character profiles configured</p>
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
