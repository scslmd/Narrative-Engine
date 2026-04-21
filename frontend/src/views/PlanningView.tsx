import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
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
import { ArcComparisonGraph } from '../components/arcs/ArcComparisonGraph';
import { ArcStageMapFlow } from '../components/arcs/ArcStageMapFlow';
import { WorldBibleWorkspace } from '../components/bible/WorldBibleWorkspace';
import FlowEditor from '../components/flow/FlowEditor';
import { getBrainstormItems, createBrainstormItem, clusterBrainstormItems } from '../services/brainstorm';
import { getFoundation, createFoundation, updateFoundation } from '../services/foundation';
import { getCharacters, createCharacter, updateCharacter } from '../services/characters';
import { getRelationships, deleteRelationship } from '../services/relationships';
import { getWorldBibleEntries, createWorldBibleEntry, updateWorldBibleEntry } from '../services/worldBible';
import {
  getSequencePlans,
  getChapterPlans,
  getScenePlans,
  getBeatPlans,
  createSequencePlan,
  createChapterPlan,
  createScenePlan,
  createBeatPlan,
  getPlanningDependencies,
  getChapterPackets,
  createChapterPacket,
} from '../services/planning';
import {
  getStoryboardCards,
  createStoryboardCard,
} from '../services/storyboard';
import {
  getArcCandidates,
  getArcSelections,
  getArcStageMaps,
  getArcComparisons,
  getSelectedArc,
} from '../services/arcs';
import type { BrainstormItemCreateRequest } from '../types/brainstorm';
import type { CharacterProfile, CharacterProfileCreateRequest, CharacterProfileUpdateRequest } from '../types/characters';
import type { FoundationCreateRequest, FoundationProfile, FoundationUpdateRequest } from '../types/foundation';
import type { WorldBibleEntry, WorldBibleEntryCreateRequest, WorldBibleEntryUpdateRequest } from '../types/bible';
import { useThemeStore } from '../stores/themeStore';

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
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<PlanningTab>('manifest');
  const [characterEditorMode, setCharacterEditorMode] = useState<CharacterEditorMode>('list');
  const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(null);
  const { mode } = useThemeStore();
  const isDark = mode === 'dark';

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

  const beatPlansQuery = useQuery({
    queryKey: ['planning-beat-plans', projectId],
    queryFn: () => getBeatPlans(projectId || ''),
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

  const storyboardCardsQuery = useQuery({
    queryKey: ['planning-storyboard-cards', projectId],
    queryFn: () => getStoryboardCards(projectId || ''),
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

  const arcComparisonsQuery = useQuery({
    queryKey: ['arc-comparisons', projectId],
    queryFn: () => getArcComparisons(projectId || ''),
    enabled: Boolean(projectId) && activeTab === 'arcs',
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

  const sequencePlanCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createSequencePlan>[1]) =>
      createSequencePlan(projectId || '', data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'sequence-plans', projectId] });
    },
  });

  const chapterPacketCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createChapterPacket>[1]) =>
      createChapterPacket(projectId || '', data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'chapter-packets', projectId] });
    },
  });

  const storyboardCardCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createStoryboardCard>[1]) =>
      createStoryboardCard(projectId || '', data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'storyboard-cards', projectId] });
    },
  });

  const chapterPlanCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createChapterPlan>[1]) =>
      createChapterPlan(projectId || '', data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'chapter-plans', projectId] });
    },
  });

  const scenePlanCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createScenePlan>[1]) =>
      createScenePlan(projectId || '', data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'scene-plans', projectId] });
    },
  });

  const beatPlanCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createBeatPlan>[1]) =>
      createBeatPlan(projectId || '', data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning', 'beat-plans', projectId] });
    },
  });

  const [sequenceCreateOpen, setSequenceCreateOpen] = useState(false);
  const [sequenceCreateTitle, setSequenceCreateTitle] = useState('');
  const [sequenceCreateSummary, setSequenceCreateSummary] = useState('');
  const [packetCreateOpen, setPacketCreateOpen] = useState(false);
  const [packetCreateChapterId, setPacketCreateChapterId] = useState('');
  const [cardCreateOpen, setCardCreateOpen] = useState(false);
  const [cardCreateTitle, setCardCreateTitle] = useState('');
  const [cardCreateContent, setCardCreateContent] = useState('');
  const [cardCreateType, setCardCreateType] = useState('idea');

  const [chapterCreateOpen, setChapterCreateOpen] = useState(false);
  const [chapterCreateTitle, setChapterCreateTitle] = useState('');
  const [chapterCreateObjective, setChapterCreateObjective] = useState('');
  const [chapterCreateConflict, setChapterCreateConflict] = useState('');
  const [chapterCreateStakes, setChapterCreateStakes] = useState('');
  const [chapterCreateSequenceId, setChapterCreateSequenceId] = useState('');

  const [sceneCreateOpen, setSceneCreateOpen] = useState(false);
  const [sceneCreateTitle, setSceneCreateTitle] = useState('');
  const [sceneCreateObjective, setSceneCreateObjective] = useState('');
  const [sceneCreateConflict, setSceneCreateConflict] = useState('');
  const [sceneCreateStakes, setSceneCreateStakes] = useState('');
  const [sceneCreateChapterId, setSceneCreateChapterId] = useState('');

  const [beatCreateOpen, setBeatCreateOpen] = useState(false);
  const [beatCreateObjective, setBeatCreateObjective] = useState('');
  const [beatCreateConflict, setBeatCreateConflict] = useState('');
  const [beatCreateStakes, setBeatCreateStakes] = useState('');

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

  const brainstormItems = brainstormQuery.data ?? [];
  const foundation = foundationQuery.data?.active_profile ?? undefined;
  const selectedCharacter = selectedCharacterId
    ? characters.find((character) => character.character_id === selectedCharacterId)
    : null;
  const worldBibleEntries = worldBibleQuery.data ?? [];

  const sequencePlans = sequencePlansQuery.data ?? [];
  const chapterPlans = chapterPlansQuery.data ?? [];
  const scenePlans = scenePlansQuery.data ?? [];
  const beatPlans = beatPlansQuery.data ?? [];
  const dependencies = dependenciesQuery.data ?? [];
  const chapterPackets = chapterPacketsQuery.data ?? [];
  const storyboardCards = storyboardCardsQuery.data ?? [];

  const arcCandidates = arcCandidatesQuery.data ?? [];
  const arcSelections = arcSelectionsQuery.data ?? [];
  const arcStageMaps = arcStageMapsQuery.data ?? [];
  const selectedArc = arcSelections.length > 0 ? getSelectedArc(arcSelections, projectId) : null;

  const arcComparisons = arcComparisonsQuery.data ?? [];

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

      <main className="flex-1 overflow-y-auto">
        {activeTab === 'manifest' && <ManifestViewer projectId={projectId} />}
        
        {activeTab === 'planning' && (
          <div className={`p-5 space-y-5 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
            <Section title="Sequences" count={sequencePlans.length}>
              <div className="flex justify-end mb-2">
                {!sequenceCreateOpen ? (
                  <button
                    onClick={() => { setSequenceCreateOpen(true); setSequenceCreateTitle(''); setSequenceCreateSummary(''); }}
                    className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-indigo-950 text-indigo-300 hover:bg-indigo-900' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'}`}
                  >
                    + New Sequence
                  </button>
                ) : (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Sequence title"
                      value={sequenceCreateTitle}
                      onChange={(e) => setSequenceCreateTitle(e.target.value)}
                      className={`text-sm px-2 py-1 rounded border w-40 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                    />
                    <input
                      type="text"
                      placeholder="Summary (optional)"
                      value={sequenceCreateSummary}
                      onChange={(e) => setSequenceCreateSummary(e.target.value)}
                      className={`text-sm px-2 py-1 rounded border w-48 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                    />
                    <button
                      onClick={() => {
                        if (!sequenceCreateTitle.trim()) return;
                        const id = `seq-${Date.now()}`;
                        void sequencePlanCreateMutation.mutateAsync({
                          project_id: projectId || '',
                          sequence_id: id,
                          title: sequenceCreateTitle.trim(),
                          summary: sequenceCreateSummary.trim() || undefined,
                        }).then(() => {
                          setSequenceCreateOpen(false);
                          setSequenceCreateTitle('');
                          setSequenceCreateSummary('');
                        });
                      }}
                      disabled={!sequenceCreateTitle.trim()}
                      className="text-xs px-2.5 py-1 rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-40"
                    >
                      Create
                    </button>
                    <button onClick={() => setSequenceCreateOpen(false)} className={`text-xs px-2 py-1 rounded-md ${isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-700'}`}>
                      Cancel
                    </button>
                  </div>
                )}
              </div>
              {sequencePlansQuery.isLoading ? (
                <WorkspaceStatus title="Loading sequences" detail="Fetching sequence plans..." isDark={isDark} />
              ) : sequencePlans.length === 0 ? (
                <EmptyState text="No sequence plans configured. Create a sequence to define the high-level story structure." />
              ) : (
                <div className="space-y-2">
                  {sequencePlans.map((seq) => (
                    <div key={seq.sequence_id} className={`p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                      <div className="font-medium">{seq.title}</div>
                      {seq.summary && <p className={`text-sm mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{seq.summary}</p>}
                    </div>
                  ))}
                </div>
              )}
            </Section>

            <Section title="Chapters" count={chapterPlans.length}>
              <div className="flex justify-end mb-2">
                {!chapterCreateOpen ? (
                  <button
                    onClick={() => { setChapterCreateOpen(true); setChapterCreateTitle(''); setChapterCreateObjective(''); setChapterCreateConflict(''); setChapterCreateStakes(''); setChapterCreateSequenceId(''); }}
                    className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-indigo-950 text-indigo-300 hover:bg-indigo-900' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'}`}
                  >
                    + New Chapter
                  </button>
                ) : (
                  <div className="flex flex-col gap-2 w-80">
                    <input type="text" placeholder="Chapter title" value={chapterCreateTitle} onChange={(e) => setChapterCreateTitle(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <input type="text" placeholder="Objective" value={chapterCreateObjective} onChange={(e) => setChapterCreateObjective(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <input type="text" placeholder="Conflict" value={chapterCreateConflict} onChange={(e) => setChapterCreateConflict(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <input type="text" placeholder="Stakes" value={chapterCreateStakes} onChange={(e) => setChapterCreateStakes(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <input type="text" placeholder="Sequence ID (optional)" value={chapterCreateSequenceId} onChange={(e) => setChapterCreateSequenceId(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <div className="flex gap-2">
                      <button onClick={() => { const id = `chapter-${Date.now()}`; void chapterPlanCreateMutation.mutateAsync({ project_id: projectId || '', chapter_id: id, title: chapterCreateTitle, objective: chapterCreateObjective, conflict: chapterCreateConflict, stakes: chapterCreateStakes, sequence_id: chapterCreateSequenceId || undefined }); setChapterCreateOpen(false); }} disabled={!chapterCreateTitle.trim() || !chapterCreateObjective.trim() || chapterPlanCreateMutation.isPending} className="text-xs px-3 py-1 rounded bg-green-600 text-white disabled:opacity-50">Create</button>
                      <button onClick={() => setChapterCreateOpen(false)} className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600">Cancel</button>
                    </div>
                  </div>
                )}
              </div>
              {chapterPlansQuery.isLoading ? (
                <WorkspaceStatus title="Loading chapters" detail="Fetching chapter plans..." isDark={isDark} />
              ) : chapterPlans.length === 0 ? (
                <EmptyState text="No chapter plans configured. Create a chapter to define story structure." />
              ) : (
                <div className="space-y-2">
                  {chapterPlans.map((chap) => (
                    <div key={chap.chapter_id} className={`p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                      <div className="font-medium">{chap.title}</div>
                      {chap.sequence_id && <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Sequence: {chap.sequence_id}</span>}
                    </div>
                  ))}
                </div>
              )}
            </Section>

            <Section title="Scenes" count={scenePlans.length}>
              <div className="flex justify-end mb-2">
                {!sceneCreateOpen ? (
                  <button
                    onClick={() => { setSceneCreateOpen(true); setSceneCreateTitle(''); setSceneCreateObjective(''); setSceneCreateConflict(''); setSceneCreateStakes(''); setSceneCreateChapterId(''); }}
                    className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-indigo-950 text-indigo-300 hover:bg-indigo-900' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'}`}
                  >
                    + New Scene
                  </button>
                ) : (
                  <div className="flex flex-col gap-2 w-80">
                    <input type="text" placeholder="Scene title" value={sceneCreateTitle} onChange={(e) => setSceneCreateTitle(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <input type="text" placeholder="Objective" value={sceneCreateObjective} onChange={(e) => setSceneCreateObjective(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <input type="text" placeholder="Conflict" value={sceneCreateConflict} onChange={(e) => setSceneCreateConflict(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <input type="text" placeholder="Stakes" value={sceneCreateStakes} onChange={(e) => setSceneCreateStakes(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <input type="text" placeholder="Chapter ID (optional)" value={sceneCreateChapterId} onChange={(e) => setSceneCreateChapterId(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <div className="flex gap-2">
                      <button onClick={() => { const id = `scene-${Date.now()}`; void scenePlanCreateMutation.mutateAsync({ project_id: projectId || '', scene_id: id, title: sceneCreateTitle, objective: sceneCreateObjective, conflict: sceneCreateConflict, stakes: sceneCreateStakes, chapter_id: sceneCreateChapterId || undefined }); setSceneCreateOpen(false); }} disabled={!sceneCreateTitle.trim() || !sceneCreateObjective.trim() || scenePlanCreateMutation.isPending} className="text-xs px-3 py-1 rounded bg-green-600 text-white disabled:opacity-50">Create</button>
                      <button onClick={() => setSceneCreateOpen(false)} className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600">Cancel</button>
                    </div>
                  </div>
                )}
              </div>
              {scenePlansQuery.isLoading ? (
                <WorkspaceStatus title="Loading scenes" detail="Fetching scene plans..." isDark={isDark} />
              ) : scenePlans.length === 0 ? (
                <EmptyState text="No scene plans configured. Create a scene to define granular story beats." />
              ) : (
                <div className="space-y-2">
                  {scenePlans.map((scene) => (
                    <div key={scene.scene_id} className={`p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                      <div className="font-medium">{scene.title}</div>
                      {scene.chapter_id && <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Chapter: {scene.chapter_id}</span>}
                    </div>
                  ))}
                </div>
              )}
            </Section>

            <Section title="Beats" count={beatPlans.length}>
              <div className="flex justify-end mb-2">
                {!beatCreateOpen ? (
                  <button
                    onClick={() => { setBeatCreateOpen(true); setBeatCreateObjective(''); setBeatCreateConflict(''); setBeatCreateStakes(''); }}
                    className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-indigo-950 text-indigo-300 hover:bg-indigo-900' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'}`}
                  >
                    + New Beat
                  </button>
                ) : (
                  <div className="flex flex-col gap-2 w-80">
                    <input type="text" placeholder="Objective" value={beatCreateObjective} onChange={(e) => setBeatCreateObjective(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <input type="text" placeholder="Conflict" value={beatCreateConflict} onChange={(e) => setBeatCreateConflict(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <input type="text" placeholder="Stakes" value={beatCreateStakes} onChange={(e) => setBeatCreateStakes(e.target.value)} className={`text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`} />
                    <div className="flex gap-2">
                      <button onClick={() => { const id = `beat-${Date.now()}`; void beatPlanCreateMutation.mutateAsync({ project_id: projectId || '', beat_id: id, objective: beatCreateObjective, conflict: beatCreateConflict, stakes: beatCreateStakes }); setBeatCreateOpen(false); }} disabled={!beatCreateObjective.trim() || !beatCreateConflict.trim() || beatPlanCreateMutation.isPending} className="text-xs px-3 py-1 rounded bg-green-600 text-white disabled:opacity-50">Create</button>
                      <button onClick={() => setBeatCreateOpen(false)} className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600">Cancel</button>
                    </div>
                  </div>
                )}
              </div>
              {beatPlansQuery.isLoading ? (
                <WorkspaceStatus title="Loading beats" detail="Fetching beat plans..." isDark={isDark} />
              ) : beatPlans.length === 0 ? (
                <EmptyState text="No beat plans configured. Create beats to define granular story moments." />
              ) : (
                <div className="space-y-2">
                  {beatPlans.map((beat) => (
                    <div key={beat.beat_id} className={`p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                      <div className="font-medium">{beat.objective}</div>
                      <div className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Conflict: {beat.conflict}</div>
                      <div className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Stakes: {beat.stakes}</div>
                      {beat.arc_stage && <span className={`text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400`}>{beat.arc_stage}</span>}
                    </div>
                  ))}
                </div>
              )}
            </Section>

            <Section title="Dependencies" count={dependencies.length}>
              {dependenciesQuery.isLoading ? (
                <WorkspaceStatus title="Loading dependencies" detail="Fetching planning dependencies..." isDark={isDark} />
              ) : dependencies.length === 0 ? (
                <EmptyState text="No dependencies defined. Dependencies track relationships between planning artifacts." />
              ) : (
                <div className="space-y-2">
                  {dependencies.map((dep) => (
                    <div key={dep.dependency_id} className={`p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} text-sm`}>
                      <span className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{dep.upstream_id}</span>
                      <span className={`mx-2 ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>→</span>
                      <span className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{dep.downstream_id}</span>
                      {dep.reason && (
                        <div className={`mt-1 text-xs italic ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>{dep.reason}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Section>

            <Section title="Chapter Packets" count={chapterPackets.length}>
              <div className="flex justify-end mb-2">
                {!packetCreateOpen ? (
                  <button
                    onClick={() => { setPacketCreateOpen(true); setPacketCreateChapterId(''); }}
                    className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-indigo-950 text-indigo-300 hover:bg-indigo-900' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'}`}
                  >
                    + New Packet
                  </button>
                ) : (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Chapter ID"
                      value={packetCreateChapterId}
                      onChange={(e) => setPacketCreateChapterId(e.target.value)}
                      className={`text-sm px-2 py-1 rounded border w-40 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                    />
                    <button
                      onClick={() => {
                        if (!packetCreateChapterId.trim()) return;
                        const id = `pkt-${Date.now()}`;
                        void chapterPacketCreateMutation.mutateAsync({
                          project_id: projectId || '',
                          packet_id: id,
                          chapter_id: packetCreateChapterId.trim(),
                        }).then(() => {
                          setPacketCreateOpen(false);
                          setPacketCreateChapterId('');
                        });
                      }}
                      disabled={!packetCreateChapterId.trim()}
                      className="text-xs px-2.5 py-1 rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-40"
                    >
                      Create
                    </button>
                    <button onClick={() => setPacketCreateOpen(false)} className={`text-xs px-2 py-1 rounded-md ${isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-700'}`}>
                      Cancel
                    </button>
                  </div>
                )}
              </div>
              {chapterPacketsQuery.isLoading ? (
                <WorkspaceStatus title="Loading chapter packets" detail="Fetching chapter packets..." isDark={isDark} />
              ) : chapterPackets.length === 0 ? (
                <EmptyState text="No chapter packets configured. Packets will appear once chapters are ready for drafting." />
              ) : (
                <div className="space-y-2">
                  {chapterPackets.map((packet) => (
                    <div key={packet.packet_id} className={`p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                      <div className="font-medium">{packet.chapter_id}</div>
                      <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>{packet.included_reference_ids.length} references included</span>
                    </div>
                  ))}
                </div>
              )}
            </Section>

            <Section title="Storyboard Cards" count={storyboardCards.length}>
              <div className="flex justify-end mb-2">
                {!cardCreateOpen ? (
                  <button
                    onClick={() => { setCardCreateOpen(true); setCardCreateTitle(''); setCardCreateContent(''); setCardCreateType('idea'); }}
                    className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-purple-950 text-purple-300 hover:bg-purple-900' : 'bg-purple-50 text-purple-700 hover:bg-purple-100'}`}
                  >
                    + New Card
                  </button>
                ) : (
                  <div className="flex flex-col gap-2">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Card title"
                        value={cardCreateTitle}
                        onChange={(e) => setCardCreateTitle(e.target.value)}
                        className={`text-sm px-2 py-1 rounded border w-40 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                      />
                      <select
                        value={cardCreateType}
                        onChange={(e) => setCardCreateType(e.target.value)}
                        className={`text-sm px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                      >
                        <option value="idea">Idea</option>
                        <option value="scene">Scene</option>
                        <option value="character">Character</option>
                        <option value="location">Location</option>
                        <option value="plot">Plot Point</option>
                      </select>
                      <button
                        onClick={() => {
                          if (!cardCreateTitle.trim()) return;
                          const id = `card-${Date.now()}`;
                          void storyboardCardCreateMutation.mutateAsync({
                            project_id: projectId || '',
                            card_id: id,
                            title: cardCreateTitle.trim(),
                            content: cardCreateContent.trim(),
                            card_type: cardCreateType,
                          }).then(() => {
                            setCardCreateOpen(false);
                            setCardCreateTitle('');
                            setCardCreateContent('');
                            setCardCreateType('idea');
                          });
                        }}
                        disabled={!cardCreateTitle.trim()}
                        className="text-xs px-2.5 py-1 rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-40"
                      >
                        Create
                      </button>
                      <button onClick={() => setCardCreateOpen(false)} className={`text-xs px-2 py-1 rounded-md ${isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-700'}`}>
                        Cancel
                      </button>
                    </div>
                    <textarea
                      placeholder="Card content (optional)"
                      value={cardCreateContent}
                      onChange={(e) => setCardCreateContent(e.target.value)}
                      rows={2}
                      className={`text-sm px-2 py-1 rounded border resize-none ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                    />
                  </div>
                )}
              </div>
              {storyboardCardsQuery.isLoading ? (
                <WorkspaceStatus title="Loading storyboard cards" detail="Fetching storyboard cards..." isDark={isDark} />
              ) : storyboardCards.length === 0 ? (
                <EmptyState text="No storyboard cards yet. Create cards to capture ideas, scenes, and plot points." />
              ) : (
                <div className="space-y-2">
                  {storyboardCards.map((card) => (
                    <div key={card.card_id} className={`p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium">{card.title}</div>
                          {card.content && <p className={`text-sm mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{card.content}</p>}
                          {card.tags.length > 0 && (
                            <div className="flex gap-1 mt-1 flex-wrap">
                              {card.tags.map((tag) => (
                                <span key={tag} className={`text-xs px-1.5 py-0.5 rounded ${isDark ? 'bg-slate-800 text-slate-400' : 'bg-slate-100 text-slate-500'}`}>{tag}</span>
                              ))}
                            </div>
                          )}
                        </div>
                        <span className={`text-xs px-2 py-0.5 rounded font-medium ${isDark ? 'bg-purple-950 text-purple-300' : 'bg-purple-100 text-purple-700'}`}>
                          {card.card_type}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Section>
          </div>
        )}

        {activeTab === 'flow' && (
          <div className="h-full">
            <FlowEditor projectId={projectId} />
          </div>
        )}

        {activeTab === 'arcs' && (
          <div className={`p-5 space-y-5 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
            <Section title="Selected Arc">
              {arcSelectionsQuery.isLoading ? (
                <WorkspaceStatus title="Loading arc selections" detail="Fetching selected arcs..." isDark={isDark} />
              ) : selectedArc ? (
                <div className={`p-4 rounded-lg border ${isDark ? 'bg-emerald-950/30 border-emerald-900/50' : 'bg-emerald-50 border-emerald-200'}`}>
                  <div className="font-medium">{selectedArc.arc_id}</div>
                  {selectedArc.summary && <p className={`text-sm mt-1 ${isDark ? 'text-emerald-300/70' : 'text-emerald-700'}`}>{selectedArc.summary}</p>}
                </div>
              ) : (
                <EmptyState text="No arc selected. Arc selections define the narrative trajectory for this project." />
              )}
            </Section>

            {arcStageMapsQuery.isLoading ? (
              <Section title="Stage Map">
                <WorkspaceStatus title="Loading stage maps" detail="Fetching arc stage progression..." isDark={isDark} />
              </Section>
            ) : arcStageMaps.length > 0 ? (
              <ArcStageMapFlow
                stageMaps={arcStageMaps}
                candidates={arcCandidates}
                selectedArcId={selectedArc?.arc_id ?? null}
                className="h-[260px]"
              />
            ) : null}

            {arcComparisonsQuery.isLoading ? (
              <Section title="Arc Comparisons">
                <WorkspaceStatus title="Loading arc comparisons" detail="Fetching comparison history..." isDark={isDark} />
              </Section>
            ) : arcComparisons.length > 0 ? (
              <Section title="Arc Comparisons">
                <ArcComparisonGraph
                  comparisons={arcComparisons}
                  className="h-[420px]"
                />
              </Section>
            ) : null}

            <Section title="Arc Candidates" count={arcCandidates.length}>
              {arcCandidatesQuery.isLoading ? (
                <WorkspaceStatus title="Loading arc candidates" detail="Fetching all arc candidates..." isDark={isDark} />
              ) : arcCandidates.length === 0 ? (
                <EmptyState text="No arc candidates available. Arcs will appear once foundation and character work is complete." />
              ) : (
                <div className="space-y-2">
                  {arcCandidates.map((candidate) => {
                    const isSelected = selectedArc?.arc_id === candidate.arc_id;
                    return (
                      <div key={candidate.arc_id} className={`p-3 rounded-lg border ${isSelected
                        ? isDark ? 'bg-emerald-950/30 border-emerald-900/50' : 'bg-emerald-50 border-emerald-300'
                        : isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
                      }`}>
                        <div className="font-medium">{candidate.name}</div>
                        {candidate.summary && <p className={`text-sm mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{candidate.summary}</p>}
                        {isSelected && (
                          <span className={`inline-block mt-2 px-2 py-0.5 text-xs font-medium rounded-full ${isDark ? 'bg-emerald-900/50 text-emerald-300' : 'bg-emerald-100 text-emerald-700'}`}>
                            Selected
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </Section>
          </div>
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
            {brainstormQuery.isLoading ? (
              <WorkspaceStatus title="Loading brainstorm items" detail="Fetching project brainstorm data." isDark={isDark} />
            ) : brainstormQuery.error ? (
              <WorkspaceStatus title="Could not load brainstorm" detail={getErrorMessage(brainstormQuery.error)} tone="error" isDark={isDark} />
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
              <WorkspaceStatus title="Loading foundation" detail="Fetching the active foundation profile." isDark={isDark} />
            ) : foundationQuery.error ? (
              <WorkspaceStatus title="Could not load foundation" detail={getErrorMessage(foundationQuery.error)} tone="error" isDark={isDark} />
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
              <WorkspaceStatus title="Loading characters" detail="Fetching character profiles for this project." isDark={isDark} />
            ) : charactersQuery.error ? (
              <WorkspaceStatus title="Could not load characters" detail={getErrorMessage(charactersQuery.error)} tone="error" isDark={isDark} />
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
                isDark={isDark}
              />
            )}
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="h-full flex flex-col">
            {relationshipsQuery.isLoading ? (
              <WorkspaceStatus title="Loading relationships" detail="Fetching character relationships for this project." isDark={isDark} />
            ) : relationshipsQuery.error ? (
              <WorkspaceStatus title="Could not load relationships" detail={getErrorMessage(relationshipsQuery.error)} tone="error" isDark={isDark} />
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
              <WorkspaceStatus title="Loading world bible" detail="Fetching world bible entries for this project." isDark={isDark} />
            ) : worldBibleQuery.error ? (
              <WorkspaceStatus title="Could not load world bible" detail={getErrorMessage(worldBibleQuery.error)} tone="error" isDark={isDark} />
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

function Section({ title, count, children }: { title: string; count?: number; children: React.ReactNode }) {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  return (
    <div>
      <h3 className={`font-semibold text-sm uppercase tracking-wider mb-3 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
        {title}
        {count !== undefined && (
          <span className={`ml-2 font-normal ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>({count})</span>
        )}
      </h3>
      {children}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  return (
    <p className={`text-sm ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>{text}</p>
  );
}

function WorkspaceStatus({
  title,
  detail,
  tone = 'neutral',
  isDark,
}: {
  title: string;
  detail: string;
  tone?: 'neutral' | 'error';
  isDark: boolean;
}) {
  return (
    <div className="flex h-48 items-center justify-center">
      <div className={`max-w-sm rounded-lg border p-5 text-center ${
        tone === 'error'
          ? isDark ? 'border-red-900/50 bg-red-950/30 text-red-300' : 'border-red-200 bg-red-50 text-red-800'
          : isDark ? 'border-slate-800 bg-slate-900 text-slate-300' : 'border-slate-200 bg-white text-slate-700'
      }`}>
        <p className="text-sm font-semibold">{title}</p>
        <p className={`mt-1.5 text-xs ${tone === 'error' ? (isDark ? 'text-red-400/80' : 'text-red-600') : (isDark ? 'text-slate-500' : 'text-slate-500')}`}>{detail}</p>
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
