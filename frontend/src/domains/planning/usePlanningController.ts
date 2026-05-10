import { useMemo, useState } from 'react';
import { useQueries, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { ApiError } from '../../lib/api';
import {
  getSequencePlan,
  getChapterPlan,
  getScenePlan,
  getBeatPlan,
  getChapterPacket,
} from '../../services/planning';
import {
  getStoryboardCards,
  createStoryboardCard,
  updateStoryboardCard,
  deleteStoryboardCard,
  reindexColumn,
} from '../../services/storyboard';
import {
  getArcCandidates,
  getArcSelections,
  getArcStageMaps,
  getArcComparisons,
  createArcCandidate,
  createArcSelection,
  deleteArcSelection,
  updateArcSelection,
  createArcStageMap,
} from '../../services/arcs';
import type {
  BeatPlan,
  ChapterPacket,
  ChapterPlan,
  PlanningDependency,
  ScenePlan,
  SequencePlan,
  StoryboardCard,
} from '../../types/planning';
import type {
  ArcCandidate,
  ArcComparisonRecord,
  ArcSelection,
  ArcSelectionUpdateRequest,
  ArcStageMap,
} from '../../types/arcs';
import { usePlanningMutations } from './mutations';
import { usePlanningQueries } from './queries';

export interface PlanningTabState {
  // Data
  sequencePlans: SequencePlan[];
  chapterPlans: ChapterPlan[];
  scenePlans: ScenePlan[];
  beatPlans: BeatPlan[];
  dependencies: PlanningDependency[];
  chapterPackets: ChapterPacket[];
  storyboardCards: StoryboardCard[];
  arcCandidates: ArcCandidate[];
  arcSelections: ArcSelection[];
  arcStageMaps: ArcStageMap[];
  arcComparisons: ArcComparisonRecord[];
  selectedArcId: string | null;

  // Loading states
  sequencesLoading: boolean;
  chaptersLoading: boolean;
  scenesLoading: boolean;
  beatsLoading: boolean;
  dependenciesLoading: boolean;
  packetsLoading: boolean;
  cardsLoading: boolean;

  // Error states
  sequencesError: ApiError | null;
  chaptersError: ApiError | null;
  scenesError: ApiError | null;
  beatsError: ApiError | null;
  dependenciesError: ApiError | null;
  packetsError: ApiError | null;
  cardsError: ApiError | null;
  candidatesLoading: boolean;
  selectionsLoading: boolean;
  stageMapsLoading: boolean;
  comparisonsLoading: boolean;

  // Form state
  sequenceCreateOpen: boolean;
  sequenceCreateTitle: string;
  sequenceCreateSummary: string;
  sequenceEditOpenId: string | null;
  sequenceEditTitle: string;
  sequenceEditSummary: string;

  chapterCreateOpen: boolean;
  chapterCreateTitle: string;
  chapterCreateObjective: string;
  chapterCreateConflict: string;
  chapterCreateStakes: string;
  chapterCreateSequenceId: string;
  chapterEditOpenId: string | null;
  chapterEditTitle: string;
  chapterEditObjective: string;
  chapterEditConflict: string;
  chapterEditStakes: string;

  sceneCreateOpen: boolean;
  sceneCreateTitle: string;
  sceneCreateObjective: string;
  sceneCreateConflict: string;
  sceneCreateStakes: string;
  sceneCreateChapterId: string;
  sceneEditOpenId: string | null;
  sceneEditTitle: string;
  sceneEditObjective: string;
  sceneEditConflict: string;
  sceneEditStakes: string;

  beatCreateOpen: boolean;
  beatCreateObjective: string;
  beatCreateConflict: string;
  beatCreateStakes: string;
  beatEditOpenId: string | null;
  beatEditObjective: string;
  beatEditConflict: string;
  beatEditStakes: string;
  beatEditArcStage: string;

  packetCreateOpen: boolean;
  packetCreateChapterId: string;

  cardCreateOpen: boolean;
  cardCreateTitle: string;
  cardCreateContent: string;
  cardCreateType: string;
  cardEditOpenId: string | null;
  cardEditTitle: string;
  cardEditContent: string;
  cardEditType: string;

  arcCandidateCreateOpen: boolean;
  arcCandidateCreateId: string;
  arcCandidateCreateName: string;
  arcCandidateCreateSummary: string;

  stageMapCreateOpen: boolean;
  stageMapCreateArcId: string;
  stageMapCreateNotes: string;
  stageMapCreateKinds: string[];
}

export interface PlanningTabCallbacks {
  // Sequences
  setSequenceCreateOpen: (open: boolean) => void;
  setSequenceCreateTitle: (value: string) => void;
  setSequenceCreateSummary: (value: string) => void;
  sequenceCreateSubmit: () => void;
  setSequenceEditOpenId: (id: string | null) => void;
  setSequenceEditTitle: (value: string) => void;
  setSequenceEditSummary: (value: string) => void;
  sequenceUpdateSubmit: (sequenceId: string) => void;
  sequenceReorder: (direction: 'up' | 'down', index: number) => void;
  openEditSequence: (plan: SequencePlan) => void;

  // Chapters
  setChapterCreateOpen: (open: boolean) => void;
  setChapterCreateTitle: (value: string) => void;
  setChapterCreateObjective: (value: string) => void;
  setChapterCreateConflict: (value: string) => void;
  setChapterCreateStakes: (value: string) => void;
  setChapterCreateSequenceId: (value: string) => void;
  chapterCreateSubmit: () => void;
  setChapterEditOpenId: (id: string | null) => void;
  setChapterEditTitle: (value: string) => void;
  setChapterEditObjective: (value: string) => void;
  setChapterEditConflict: (value: string) => void;
  setChapterEditStakes: (value: string) => void;
  chapterUpdateSubmit: (chapterId: string) => void;
  chapterReorder: (direction: 'up' | 'down', index: number) => void;
  openEditChapter: (plan: ChapterPlan) => void;

  // Scenes
  setSceneCreateOpen: (open: boolean) => void;
  setSceneCreateTitle: (value: string) => void;
  setSceneCreateObjective: (value: string) => void;
  setSceneCreateConflict: (value: string) => void;
  setSceneCreateStakes: (value: string) => void;
  setSceneCreateChapterId: (value: string) => void;
  sceneCreateSubmit: () => void;
  setSceneEditOpenId: (id: string | null) => void;
  setSceneEditTitle: (value: string) => void;
  setSceneEditObjective: (value: string) => void;
  setSceneEditConflict: (value: string) => void;
  setSceneEditStakes: (value: string) => void;
  sceneUpdateSubmit: (sceneId: string) => void;
  sceneReorder: (direction: 'up' | 'down', index: number) => void;
  openEditScene: (plan: ScenePlan) => void;

  // Beats
  setBeatCreateOpen: (open: boolean) => void;
  setBeatCreateObjective: (value: string) => void;
  setBeatCreateConflict: (value: string) => void;
  setBeatCreateStakes: (value: string) => void;
  beatCreateSubmit: () => void;
  setBeatEditOpenId: (id: string | null) => void;
  setBeatEditObjective: (value: string) => void;
  setBeatEditConflict: (value: string) => void;
  setBeatEditStakes: (value: string) => void;
  setBeatEditArcStage: (value: string) => void;
  beatUpdateSubmit: (beatId: string) => void;
  openEditBeat: (plan: BeatPlan) => void;

  // Chapter Packets
  setPacketCreateOpen: (open: boolean) => void;
  setPacketCreateChapterId: (value: string) => void;
  packetCreateSubmit: () => void;

  // Retry callbacks
  retrySequences: () => void;
  retryChapters: () => void;
  retryScenes: () => void;
  retryBeats: () => void;
  retryDependencies: () => void;
  retryPackets: () => void;
  retryCards: () => void;

  // Storyboard Cards
  setCardCreateOpen: (open: boolean) => void;
  setCardCreateTitle: (value: string) => void;
  setCardCreateContent: (value: string) => void;
  setCardCreateType: (value: string) => void;
  cardCreateSubmit: () => void;
  setCardEditOpenId: (id: string | null) => void;
  setCardEditTitle: (value: string) => void;
  setCardEditContent: (value: string) => void;
  setCardEditType: (value: string) => void;
  cardUpdateSubmit: (cardId: string) => void;
  cardDelete: (cardId: string) => void;
  cardReorder: (columnId: string, orderedIds: string[]) => void;
  openEditCard: (card: StoryboardCard) => void;

  // Arc Candidates
  setArcCandidateCreateOpen: (open: boolean) => void;
  setArcCandidateCreateId: (value: string) => void;
  setArcCandidateCreateName: (value: string) => void;
  setArcCandidateCreateSummary: (value: string) => void;
  arcCandidateCreateSubmit: () => void;

  // Stage Map
  setStageMapCreateOpen: (open: boolean) => void;
  setStageMapCreateArcId: (value: string) => void;
  setStageMapCreateNotes: (value: string) => void;
  setStageMapCreateKinds: (kinds: string[]) => void;
  stageMapCreateSubmit: () => void;
  toggleStageKind: (stage: string) => void;

  // Arc Selection
  selectArc: (arcId: string) => void;
  deselectArc: () => void;
  arcUpdateSelection: (selectionId: string, data: ArcSelectionUpdateRequest) => void;
  arcDeleteSelection: (selectionId: string) => void;
}

export function usePlanningController(tab: string): {
  state: PlanningTabState;
  callbacks: PlanningTabCallbacks;
} {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const resolvedProjectId = projectId || '';
  const planningQueries = usePlanningQueries({
    projectId: resolvedProjectId,
    tab,
  });
  const planningMutations = usePlanningMutations({
    projectId: resolvedProjectId,
  });

  const {
    sequencePlansQuery,
    chapterPlansQuery,
    scenePlansQuery,
    beatPlansQuery,
    dependenciesQuery,
    chapterPacketsQuery,
  } = planningQueries;

  const arcQueries = useQueries({
    queries: [
      {
        queryKey: ['planning-storyboard-cards', projectId],
        queryFn: () => getStoryboardCards(projectId || ''),
        enabled: Boolean(projectId) && tab === 'planning',
      },
      {
        queryKey: ['arc-candidates', projectId],
        queryFn: () => getArcCandidates(projectId || ''),
        enabled: Boolean(projectId) && tab === 'arcs',
      },
      {
        queryKey: ['arc-selections', projectId],
        queryFn: () => getArcSelections(projectId || ''),
        enabled: Boolean(projectId) && tab === 'arcs',
      },
      {
        queryKey: ['arc-stage-maps', projectId],
        queryFn: () => getArcStageMaps(projectId || ''),
        enabled: Boolean(projectId) && tab === 'arcs',
      },
      {
        queryKey: ['arc-comparisons', projectId],
        queryFn: () => getArcComparisons(projectId || ''),
        enabled: Boolean(projectId) && tab === 'arcs',
      },
    ],
  });

  const storyboardCardsQuery = arcQueries[0];
  const arcCandidatesQuery = arcQueries[1];
  const arcSelectionsQuery = arcQueries[2];
  const arcStageMapsQuery = arcQueries[3];
  const arcComparisonsQuery = arcQueries[4];

  const {
    sequencePlanCreateMutation,
    sequencePlanUpdateMutation,
    chapterPlanCreateMutation,
    chapterPlanUpdateMutation,
    scenePlanCreateMutation,
    scenePlanUpdateMutation,
    beatPlanCreateMutation,
    beatPlanUpdateMutation,
    chapterPacketCreateMutation,
    sequenceReorderMutation,
    chapterReorderMutation,
    sceneReorderMutation,
  } = planningMutations;

  const mutations = useMemo(() => {
    const invalidate = (key: readonly unknown[]) => void queryClient.invalidateQueries({ queryKey: key });
    const cardsKey = ['planning-storyboard-cards', projectId];
    const arcSelKey = ['arcs', 'selections', projectId ?? ''];
    const arcCandKey = ['arcs', 'candidates', projectId ?? ''];
    const arcStageMapsKey = ['arc-stage-maps', projectId];
    const arcSelectionsKey = ['arc-selections', projectId];

    return {
      storyboardCardCreateMutation: { mutateAsync: (data: Parameters<typeof createStoryboardCard>[1]) => createStoryboardCard(projectId || '', data).then(() => invalidate(cardsKey)) },
      storyboardCardUpdateMutation: { mutateAsync: (data: { cardId: string; payload: Parameters<typeof updateStoryboardCard>[1] }) => updateStoryboardCard(data.cardId, data.payload, projectId || undefined).then(() => invalidate(cardsKey)) },
      storyboardCardDeleteMutation: { mutateAsync: (cardId: string) => deleteStoryboardCard(cardId, projectId || undefined).then(() => invalidate(cardsKey)) },
      storyboardCardReindexMutation: { mutateAsync: (data: { columnId: string; orderedIds: string[] }) => reindexColumn(data.columnId, data.orderedIds, projectId || undefined).then(() => invalidate(cardsKey)) },
      selectArcMutation: {
        mutateAsync: (arcId: string) =>
          createArcSelection({ project_id: projectId || '', selected_arc: arcId }).then(() => { invalidate(arcSelKey); invalidate(arcCandKey); }),
      },
      deselectArcMutation: {
        mutateAsync: () => {
          const selections = arcQueries[2].data;
          const selection = selections?.[0];
          if (!selection) return Promise.resolve();
          return deleteArcSelection(selection.selection_id, projectId || '').then(() => { invalidate(arcSelKey); invalidate(arcCandKey); });
        },
      },
      arcCandidateCreateMutation: {
        mutateAsync: (data: { arc_id: string; project_id: string; name: string; summary: string }) =>
          createArcCandidate({ arc_id: data.arc_id, project_id: data.project_id, name: data.name, summary: data.summary }).then(() => { invalidate(arcCandKey); invalidate(arcSelKey); }),
      },
      stageMapCreateMutation: {
        mutateAsync: (data: { arc_id: string; project_id: string; stage_kinds: string[]; notes?: string | null }) =>
          createArcStageMap({ project_id: data.project_id, arc_id: data.arc_id, stage_kinds: data.stage_kinds, notes: data.notes || undefined }).then(() => invalidate(arcStageMapsKey)),
      },
      arcSelectionUpdateMutation: {
        mutateAsync: ({ selectionId, data }: { selectionId: string; data: ArcSelectionUpdateRequest }) =>
          updateArcSelection(selectionId, data, projectId || '').then(() => invalidate(arcSelectionsKey)),
      },
      arcSelectionDeleteMutation: {
        mutateAsync: (selectionId: string) =>
          deleteArcSelection(selectionId, projectId || '').then(() => invalidate(arcSelectionsKey)),
      },
    };
  }, [projectId, queryClient, arcQueries]);

  const {
    storyboardCardCreateMutation,
    storyboardCardUpdateMutation,
    storyboardCardDeleteMutation,
    storyboardCardReindexMutation,
    selectArcMutation,
    deselectArcMutation,
    arcCandidateCreateMutation,
    stageMapCreateMutation,
    arcSelectionUpdateMutation,
    arcSelectionDeleteMutation,
  } = mutations;

  // Form state — single useState to stay under React's 50-hook limit
  interface FormState {
    sequenceCreateOpen: boolean;
    sequenceCreateTitle: string;
    sequenceCreateSummary: string;
    sequenceEditOpenId: string | null;
    sequenceEditTitle: string;
    sequenceEditSummary: string;
    chapterCreateOpen: boolean;
    chapterCreateTitle: string;
    chapterCreateObjective: string;
    chapterCreateConflict: string;
    chapterCreateStakes: string;
    chapterCreateSequenceId: string;
    chapterEditOpenId: string | null;
    chapterEditTitle: string;
    chapterEditObjective: string;
    chapterEditConflict: string;
    chapterEditStakes: string;
    sceneCreateOpen: boolean;
    sceneCreateTitle: string;
    sceneCreateObjective: string;
    sceneCreateConflict: string;
    sceneCreateStakes: string;
    sceneCreateChapterId: string;
    sceneEditOpenId: string | null;
    sceneEditTitle: string;
    sceneEditObjective: string;
    sceneEditConflict: string;
    sceneEditStakes: string;
    beatCreateOpen: boolean;
    beatCreateObjective: string;
    beatCreateConflict: string;
    beatCreateStakes: string;
    beatEditOpenId: string | null;
    beatEditObjective: string;
    beatEditConflict: string;
    beatEditStakes: string;
    beatEditArcStage: string;
    packetCreateOpen: boolean;
    packetCreateChapterId: string;
    cardCreateOpen: boolean;
    cardCreateTitle: string;
    cardCreateContent: string;
    cardCreateType: string;
    cardEditOpenId: string | null;
    cardEditTitle: string;
    cardEditContent: string;
    cardEditType: string;
    arcCandidateCreateOpen: boolean;
    arcCandidateCreateId: string;
    arcCandidateCreateName: string;
    arcCandidateCreateSummary: string;
    stageMapCreateOpen: boolean;
    stageMapCreateArcId: string;
    stageMapCreateNotes: string;
    stageMapCreateKinds: string[];
  }

  const initialState: FormState = {
    sequenceCreateOpen: false,
    sequenceCreateTitle: '',
    sequenceCreateSummary: '',
    sequenceEditOpenId: null,
    sequenceEditTitle: '',
    sequenceEditSummary: '',
    chapterCreateOpen: false,
    chapterCreateTitle: '',
    chapterCreateObjective: '',
    chapterCreateConflict: '',
    chapterCreateStakes: '',
    chapterCreateSequenceId: '',
    chapterEditOpenId: null,
    chapterEditTitle: '',
    chapterEditObjective: '',
    chapterEditConflict: '',
    chapterEditStakes: '',
    sceneCreateOpen: false,
    sceneCreateTitle: '',
    sceneCreateObjective: '',
    sceneCreateConflict: '',
    sceneCreateStakes: '',
    sceneCreateChapterId: '',
    sceneEditOpenId: null,
    sceneEditTitle: '',
    sceneEditObjective: '',
    sceneEditConflict: '',
    sceneEditStakes: '',
    beatCreateOpen: false,
    beatCreateObjective: '',
    beatCreateConflict: '',
    beatCreateStakes: '',
    beatEditOpenId: null,
    beatEditObjective: '',
    beatEditConflict: '',
    beatEditStakes: '',
    beatEditArcStage: '',
    packetCreateOpen: false,
    packetCreateChapterId: '',
    cardCreateOpen: false,
    cardCreateTitle: '',
    cardCreateContent: '',
    cardCreateType: 'idea',
    cardEditOpenId: null,
    cardEditTitle: '',
    cardEditContent: '',
    cardEditType: 'idea',
    arcCandidateCreateOpen: false,
    arcCandidateCreateId: '',
    arcCandidateCreateName: '',
    arcCandidateCreateSummary: '',
    stageMapCreateOpen: false,
    stageMapCreateArcId: '',
    stageMapCreateNotes: '',
    stageMapCreateKinds: [],
  };

  const [form, setForm] = useState(initialState);

  // Destructure for clarity
  const {
    sequenceCreateOpen, sequenceCreateTitle, sequenceCreateSummary,
    sequenceEditOpenId, sequenceEditTitle, sequenceEditSummary,
    chapterCreateOpen, chapterCreateTitle, chapterCreateObjective,
    chapterCreateConflict, chapterCreateStakes, chapterCreateSequenceId,
    chapterEditOpenId, chapterEditTitle, chapterEditObjective,
    chapterEditConflict, chapterEditStakes,
    sceneCreateOpen, sceneCreateTitle, sceneCreateObjective,
    sceneCreateConflict, sceneCreateStakes, sceneCreateChapterId,
    sceneEditOpenId, sceneEditTitle, sceneEditObjective,
    sceneEditConflict, sceneEditStakes,
    beatCreateOpen, beatCreateObjective, beatCreateConflict,
    beatCreateStakes, beatEditOpenId, beatEditObjective,
    beatEditConflict, beatEditStakes, beatEditArcStage,
    packetCreateOpen, packetCreateChapterId,
    cardCreateOpen, cardCreateTitle, cardCreateContent, cardCreateType,
    cardEditOpenId, cardEditTitle, cardEditContent, cardEditType,
    arcCandidateCreateOpen, arcCandidateCreateId, arcCandidateCreateName,
    arcCandidateCreateSummary,
    stageMapCreateOpen, stageMapCreateArcId, stageMapCreateNotes,
    stageMapCreateKinds,
  } = form;

  const setSequenceCreateOpen = (v: boolean) => setForm(f => ({ ...f, sequenceCreateOpen: v }));
  const setSequenceCreateTitle = (v: string) => setForm(f => ({ ...f, sequenceCreateTitle: v }));
  const setSequenceCreateSummary = (v: string) => setForm(f => ({ ...f, sequenceCreateSummary: v }));
  const setSequenceEditOpenId = (v: string | null) => setForm(f => ({ ...f, sequenceEditOpenId: v }));
  const setSequenceEditTitle = (v: string) => setForm(f => ({ ...f, sequenceEditTitle: v }));
  const setSequenceEditSummary = (v: string) => setForm(f => ({ ...f, sequenceEditSummary: v }));
  const setChapterCreateOpen = (v: boolean) => setForm(f => ({ ...f, chapterCreateOpen: v }));
  const setChapterCreateTitle = (v: string) => setForm(f => ({ ...f, chapterCreateTitle: v }));
  const setChapterCreateObjective = (v: string) => setForm(f => ({ ...f, chapterCreateObjective: v }));
  const setChapterCreateConflict = (v: string) => setForm(f => ({ ...f, chapterCreateConflict: v }));
  const setChapterCreateStakes = (v: string) => setForm(f => ({ ...f, chapterCreateStakes: v }));
  const setChapterCreateSequenceId = (v: string) => setForm(f => ({ ...f, chapterCreateSequenceId: v }));
  const setChapterEditOpenId = (v: string | null) => setForm(f => ({ ...f, chapterEditOpenId: v }));
  const setChapterEditTitle = (v: string) => setForm(f => ({ ...f, chapterEditTitle: v }));
  const setChapterEditObjective = (v: string) => setForm(f => ({ ...f, chapterEditObjective: v }));
  const setChapterEditConflict = (v: string) => setForm(f => ({ ...f, chapterEditConflict: v }));
  const setChapterEditStakes = (v: string) => setForm(f => ({ ...f, chapterEditStakes: v }));
  const setSceneCreateOpen = (v: boolean) => setForm(f => ({ ...f, sceneCreateOpen: v }));
  const setSceneCreateTitle = (v: string) => setForm(f => ({ ...f, sceneCreateTitle: v }));
  const setSceneCreateObjective = (v: string) => setForm(f => ({ ...f, sceneCreateObjective: v }));
  const setSceneCreateConflict = (v: string) => setForm(f => ({ ...f, sceneCreateConflict: v }));
  const setSceneCreateStakes = (v: string) => setForm(f => ({ ...f, sceneCreateStakes: v }));
  const setSceneCreateChapterId = (v: string) => setForm(f => ({ ...f, sceneCreateChapterId: v }));
  const setSceneEditOpenId = (v: string | null) => setForm(f => ({ ...f, sceneEditOpenId: v }));
  const setSceneEditTitle = (v: string) => setForm(f => ({ ...f, sceneEditTitle: v }));
  const setSceneEditObjective = (v: string) => setForm(f => ({ ...f, sceneEditObjective: v }));
  const setSceneEditConflict = (v: string) => setForm(f => ({ ...f, sceneEditConflict: v }));
  const setSceneEditStakes = (v: string) => setForm(f => ({ ...f, sceneEditStakes: v }));
  const setBeatCreateOpen = (v: boolean) => setForm(f => ({ ...f, beatCreateOpen: v }));
  const setBeatCreateObjective = (v: string) => setForm(f => ({ ...f, beatCreateObjective: v }));
  const setBeatCreateConflict = (v: string) => setForm(f => ({ ...f, beatCreateConflict: v }));
  const setBeatCreateStakes = (v: string) => setForm(f => ({ ...f, beatCreateStakes: v }));
  const setBeatEditOpenId = (v: string | null) => setForm(f => ({ ...f, beatEditOpenId: v }));
  const setBeatEditObjective = (v: string) => setForm(f => ({ ...f, beatEditObjective: v }));
  const setBeatEditConflict = (v: string) => setForm(f => ({ ...f, beatEditConflict: v }));
  const setBeatEditStakes = (v: string) => setForm(f => ({ ...f, beatEditStakes: v }));
  const setBeatEditArcStage = (v: string) => setForm(f => ({ ...f, beatEditArcStage: v }));
  const setPacketCreateOpen = (v: boolean) => setForm(f => ({ ...f, packetCreateOpen: v }));
  const setPacketCreateChapterId = (v: string) => setForm(f => ({ ...f, packetCreateChapterId: v }));
  const setCardCreateOpen = (v: boolean) => setForm(f => ({ ...f, cardCreateOpen: v }));
  const setCardCreateTitle = (v: string) => setForm(f => ({ ...f, cardCreateTitle: v }));
  const setCardCreateContent = (v: string) => setForm(f => ({ ...f, cardCreateContent: v }));
  const setCardCreateType = (v: string) => setForm(f => ({ ...f, cardCreateType: v }));
  const setCardEditOpenId = (v: string | null) => setForm(f => ({ ...f, cardEditOpenId: v }));
  const setCardEditTitle = (v: string) => setForm(f => ({ ...f, cardEditTitle: v }));
  const setCardEditContent = (v: string) => setForm(f => ({ ...f, cardEditContent: v }));
  const setCardEditType = (v: string) => setForm(f => ({ ...f, cardEditType: v }));
  const setArcCandidateCreateOpen = (v: boolean) => setForm(f => ({ ...f, arcCandidateCreateOpen: v }));
  const setArcCandidateCreateId = (v: string) => setForm(f => ({ ...f, arcCandidateCreateId: v }));
  const setArcCandidateCreateName = (v: string) => setForm(f => ({ ...f, arcCandidateCreateName: v }));
  const setArcCandidateCreateSummary = (v: string) => setForm(f => ({ ...f, arcCandidateCreateSummary: v }));
  const setStageMapCreateOpen = (v: boolean) => setForm(f => ({ ...f, stageMapCreateOpen: v }));
  const setStageMapCreateArcId = (v: string) => setForm(f => ({ ...f, stageMapCreateArcId: v }));
  const setStageMapCreateNotes = (v: string) => setForm(f => ({ ...f, stageMapCreateNotes: v }));
  const setStageMapCreateKinds = (v: string[]) => setForm(f => ({ ...f, stageMapCreateKinds: v }));

  const sequencePlans = sequencePlansQuery.data ?? [];
  const chapterPlans = chapterPlansQuery.data ?? [];
  const scenePlans = scenePlansQuery.data ?? [];
  const beatPlans = beatPlansQuery.data ?? [];
  const dependencies = dependenciesQuery.data ?? [];
  const chapterPackets = chapterPacketsQuery.data ?? [];
  const storyboardCards = storyboardCardsQuery.data ?? [];

  const arcCandidates = arcCandidatesQuery.data ?? [];
  const arcSelections = arcSelectionsQuery.data ?? [];
  const selectedArc = arcSelections.length > 0
    ? (arcSelections.find((s) => s.project_id === projectId)?.selected_arc || null)
    : null;

  const arcComparisons = arcComparisonsQuery.data ?? [];
  const arcStageMaps = arcStageMapsQuery.data ?? [];

  // Callbacks
  const callbacks: PlanningTabCallbacks = {
    // Sequences
    setSequenceCreateOpen,
    setSequenceCreateTitle,
    setSequenceCreateSummary,
    sequenceCreateSubmit: () => {
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
    },
    setSequenceEditOpenId,
    setSequenceEditTitle,
    setSequenceEditSummary,
    sequenceUpdateSubmit: (sequenceId) => {
      void sequencePlanUpdateMutation.mutateAsync({
        sequenceId,
        projectId: projectId || '',
        title: sequenceEditTitle,
        summary: sequenceEditSummary || undefined,
      }).then(() => {
        setSequenceEditOpenId(null);
        setSequenceEditTitle('');
        setSequenceEditSummary('');
      });
    },
    sequenceReorder: (direction, index) => {
      const newOrder = [...sequencePlans];
      const [removed] = newOrder.splice(index, 1);
      if (direction === 'up') {
        newOrder.splice(index - 1, 0, removed);
      } else {
        newOrder.splice(index + 1, 0, removed);
      }
      void sequenceReorderMutation.mutateAsync(newOrder.map((s) => s.sequence_id));
    },
    openEditSequence: (plan) => {
      void getSequencePlan(plan.sequence_id, projectId || '').then((fullPlan) => {
        setSequenceEditOpenId(fullPlan.sequence_id);
        setSequenceEditTitle(fullPlan.title);
        setSequenceEditSummary(fullPlan.summary || '');
      });
    },

    // Chapters
    setChapterCreateOpen,
    setChapterCreateTitle,
    setChapterCreateObjective,
    setChapterCreateConflict,
    setChapterCreateStakes,
    setChapterCreateSequenceId,
    chapterCreateSubmit: () => {
      const id = `chapter-${Date.now()}`;
      void chapterPlanCreateMutation.mutateAsync({
        project_id: projectId || '',
        chapter_id: id,
        title: chapterCreateTitle,
        objective: chapterCreateObjective,
        conflict: chapterCreateConflict,
        stakes: chapterCreateStakes,
        sequence_id: chapterCreateSequenceId || undefined,
      }).then(() => {
        setChapterCreateOpen(false);
      });
    },
    setChapterEditOpenId,
    setChapterEditTitle,
    setChapterEditObjective,
    setChapterEditConflict,
    setChapterEditStakes,
    chapterUpdateSubmit: (chapterId) => {
      void chapterPlanUpdateMutation.mutateAsync({
        chapterId,
        projectId: projectId || '',
        title: chapterEditTitle,
        objective: chapterEditObjective,
        conflict: chapterEditConflict || undefined,
        stakes: chapterEditStakes || undefined,
      }).then(() => {
        setChapterEditOpenId(null);
        setChapterEditTitle('');
        setChapterEditObjective('');
        setChapterEditConflict('');
        setChapterEditStakes('');
      });
    },
    chapterReorder: (direction, index) => {
      const newOrder = [...chapterPlans];
      const [removed] = newOrder.splice(index, 1);
      if (direction === 'up') {
        newOrder.splice(index - 1, 0, removed);
      } else {
        newOrder.splice(index + 1, 0, removed);
      }
      void chapterReorderMutation.mutateAsync(newOrder.map((c) => c.chapter_id));
    },
    openEditChapter: (plan) => {
      void getChapterPlan(plan.chapter_id, projectId || '').then((fullPlan) => {
        setChapterEditOpenId(fullPlan.chapter_id);
        setChapterEditTitle(fullPlan.title);
        setChapterEditObjective(fullPlan.objective);
        setChapterEditConflict(fullPlan.conflict || '');
        setChapterEditStakes(fullPlan.stakes || '');
      });
    },

    // Scenes
    setSceneCreateOpen,
    setSceneCreateTitle,
    setSceneCreateObjective,
    setSceneCreateConflict,
    setSceneCreateStakes,
    setSceneCreateChapterId,
    sceneCreateSubmit: () => {
      const id = `scene-${Date.now()}`;
      void scenePlanCreateMutation.mutateAsync({
        project_id: projectId || '',
        scene_id: id,
        title: sceneCreateTitle,
        objective: sceneCreateObjective,
        conflict: sceneCreateConflict,
        stakes: sceneCreateStakes,
        chapter_id: sceneCreateChapterId || undefined,
      }).then(() => {
        setSceneCreateOpen(false);
      });
    },
    setSceneEditOpenId,
    setSceneEditTitle,
    setSceneEditObjective,
    setSceneEditConflict,
    setSceneEditStakes,
    sceneUpdateSubmit: (sceneId) => {
      void scenePlanUpdateMutation.mutateAsync({
        sceneId,
        projectId: projectId || '',
        title: sceneEditTitle,
        objective: sceneEditObjective,
        conflict: sceneEditConflict || undefined,
        stakes: sceneEditStakes || undefined,
      }).then(() => {
        setSceneEditOpenId(null);
        setSceneEditTitle('');
        setSceneEditObjective('');
        setSceneEditConflict('');
        setSceneEditStakes('');
      });
    },
    sceneReorder: (direction, index) => {
      const newOrder = [...scenePlans];
      const [removed] = newOrder.splice(index, 1);
      if (direction === 'up') {
        newOrder.splice(index - 1, 0, removed);
      } else {
        newOrder.splice(index + 1, 0, removed);
      }
      void sceneReorderMutation.mutateAsync(newOrder.map((s) => s.scene_id));
    },
    openEditScene: (plan) => {
      void getScenePlan(plan.scene_id, projectId || '').then((fullPlan) => {
        setSceneEditOpenId(fullPlan.scene_id);
        setSceneEditTitle(fullPlan.title);
        setSceneEditObjective(fullPlan.objective);
        setSceneEditConflict(fullPlan.conflict || '');
        setSceneEditStakes(fullPlan.stakes || '');
      });
    },

    // Beats
    setBeatCreateOpen,
    setBeatCreateObjective,
    setBeatCreateConflict,
    setBeatCreateStakes,
    beatCreateSubmit: () => {
      const id = `beat-${Date.now()}`;
      void beatPlanCreateMutation.mutateAsync({
        project_id: projectId || '',
        beat_id: id,
        objective: beatCreateObjective,
        conflict: beatCreateConflict,
        stakes: beatCreateStakes,
      }).then(() => {
        setBeatCreateOpen(false);
      });
    },
    setBeatEditOpenId,
    setBeatEditObjective,
    setBeatEditConflict,
    setBeatEditStakes,
    setBeatEditArcStage,
    beatUpdateSubmit: (beatId) => {
      void beatPlanUpdateMutation.mutateAsync({
        beatId,
        projectId: projectId || '',
        objective: beatEditObjective,
        conflict: beatEditConflict || undefined,
        stakes: beatEditStakes || undefined,
        arc_stage: beatEditArcStage || undefined,
      }).then(() => {
        setBeatEditOpenId(null);
        setBeatEditObjective('');
        setBeatEditConflict('');
        setBeatEditStakes('');
        setBeatEditArcStage('');
      });
    },
    openEditBeat: (plan) => {
      void getBeatPlan(plan.beat_id, projectId || '').then((fullPlan) => {
        setBeatEditOpenId(fullPlan.beat_id);
        setBeatEditObjective(fullPlan.objective);
        setBeatEditConflict(fullPlan.conflict || '');
        setBeatEditStakes(fullPlan.stakes || '');
        setBeatEditArcStage(fullPlan.arc_stage || '');
      });
    },

    // Chapter Packets
    setPacketCreateOpen,
    setPacketCreateChapterId,
    packetCreateSubmit: () => {
      if (!packetCreateChapterId.trim()) return;
      const id = `pkt-${Date.now()}`;
      void chapterPacketCreateMutation.mutateAsync({
        project_id: projectId || '',
        packet_id: id,
        chapter_id: packetCreateChapterId.trim(),
      }).then(() => {
        setPacketCreateOpen(false);
        setPacketCreateChapterId('');
        void getChapterPacket(id, projectId || '');
      });
    },

    // Retry callbacks
    retrySequences: () => { void sequencePlansQuery.refetch(); },
    retryChapters: () => { void chapterPlansQuery.refetch(); },
    retryScenes: () => { void scenePlansQuery.refetch(); },
    retryBeats: () => { void beatPlansQuery.refetch(); },
    retryDependencies: () => { void dependenciesQuery.refetch(); },
    retryPackets: () => { void chapterPacketsQuery.refetch(); },
    retryCards: () => { void storyboardCardsQuery.refetch(); },

    // Storyboard Cards
    setCardCreateOpen,
    setCardCreateTitle,
    setCardCreateContent,
    setCardCreateType,
    cardCreateSubmit: () => {
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
    },
    setCardEditOpenId,
    setCardEditTitle,
    setCardEditContent,
    setCardEditType,
    cardUpdateSubmit: (cardId) => {
      void storyboardCardUpdateMutation.mutateAsync({
        cardId,
        payload: {
          title: cardEditTitle.trim() || undefined,
          content: cardEditContent.trim() || undefined,
          card_type: cardEditType || undefined,
        },
      }).then(() => {
        setCardEditOpenId(null);
        setCardEditTitle('');
        setCardEditContent('');
        setCardEditType('idea');
      });
    },
    cardDelete: (cardId) => {
      void storyboardCardDeleteMutation.mutateAsync(cardId).then(() => {
        if (cardEditOpenId === cardId) {
          setCardEditOpenId(null);
          setCardEditTitle('');
          setCardEditContent('');
          setCardEditType('idea');
        }
      });
    },
    cardReorder: (columnId, orderedIds) => {
      void storyboardCardReindexMutation.mutateAsync({ columnId, orderedIds });
    },
    openEditCard: (card) => {
      setCardEditOpenId(card.card_id);
      setCardEditTitle(card.title);
      setCardEditContent(card.content || '');
      setCardEditType(card.card_type || 'idea');
    },

    // Arc Candidates
    setArcCandidateCreateOpen,
    setArcCandidateCreateId,
    setArcCandidateCreateName,
    setArcCandidateCreateSummary,
    arcCandidateCreateSubmit: () => {
      if (!arcCandidateCreateId.trim() || !arcCandidateCreateName.trim()) return;
      void arcCandidateCreateMutation.mutateAsync({
        arc_id: arcCandidateCreateId.trim(),
        project_id: projectId || '',
        name: arcCandidateCreateName.trim(),
        summary: arcCandidateCreateSummary.trim() || 'No summary provided.',
      }).then(() => {
        setArcCandidateCreateOpen(false);
        setArcCandidateCreateId('');
        setArcCandidateCreateName('');
        setArcCandidateCreateSummary('');
      });
    },

    // Stage Map
    setStageMapCreateOpen,
    setStageMapCreateArcId,
    setStageMapCreateNotes,
    setStageMapCreateKinds,
    stageMapCreateSubmit: () => {
      if (!stageMapCreateArcId || stageMapCreateKinds.length === 0) return;
      void stageMapCreateMutation.mutateAsync({
        arc_id: stageMapCreateArcId,
        project_id: projectId || '',
        stage_kinds: stageMapCreateKinds,
        notes: stageMapCreateNotes.trim() || undefined,
      }).then(() => {
        setStageMapCreateOpen(false);
        setStageMapCreateArcId('');
        setStageMapCreateKinds([]);
        setStageMapCreateNotes('');
      });
    },
    toggleStageKind: (stage) => {
      setForm(f => ({
        ...f,
        stageMapCreateKinds: f.stageMapCreateKinds.includes(stage)
          ? f.stageMapCreateKinds.filter((s) => s !== stage)
          : [...f.stageMapCreateKinds, stage]
      }));
    },

    // Arc Selection
    selectArc: (arcId) => {
      void selectArcMutation.mutateAsync(arcId);
    },
    deselectArc: () => {
      void deselectArcMutation.mutateAsync();
    },
    arcUpdateSelection: (selectionId, data) => {
      void arcSelectionUpdateMutation.mutateAsync({ selectionId, data });
    },
    arcDeleteSelection: (selectionId) => {
      void arcSelectionDeleteMutation.mutateAsync(selectionId);
    },
  };

  const state: PlanningTabState = {
    sequencePlans,
    chapterPlans,
    scenePlans,
    beatPlans,
    dependencies,
    chapterPackets,
    storyboardCards,
    arcCandidates,
    arcSelections,
    arcStageMaps,
    arcComparisons,
    selectedArcId: selectedArc?.arc_id ?? null,
    sequencesLoading: sequencePlansQuery.isLoading,
    chaptersLoading: chapterPlansQuery.isLoading,
    scenesLoading: scenePlansQuery.isLoading,
    beatsLoading: beatPlansQuery.isLoading,
    dependenciesLoading: dependenciesQuery.isLoading,
    packetsLoading: chapterPacketsQuery.isLoading,
    cardsLoading: storyboardCardsQuery.isLoading,
    candidatesLoading: arcCandidatesQuery.isLoading,
    selectionsLoading: arcSelectionsQuery.isLoading,
    stageMapsLoading: arcStageMapsQuery.isLoading,
    comparisonsLoading: arcComparisonsQuery.isLoading,

    // Error states
    sequencesError: sequencePlansQuery.error ? (sequencePlansQuery.error instanceof ApiError ? sequencePlansQuery.error : new ApiError(sequencePlansQuery.error?.message ?? 'Unknown error', 0)) : null,
    chaptersError: chapterPlansQuery.error ? (chapterPlansQuery.error instanceof ApiError ? chapterPlansQuery.error : new ApiError(chapterPlansQuery.error?.message ?? 'Unknown error', 0)) : null,
    scenesError: scenePlansQuery.error ? (scenePlansQuery.error instanceof ApiError ? scenePlansQuery.error : new ApiError(scenePlansQuery.error?.message ?? 'Unknown error', 0)) : null,
    beatsError: beatPlansQuery.error ? (beatPlansQuery.error instanceof ApiError ? beatPlansQuery.error : new ApiError(beatPlansQuery.error?.message ?? 'Unknown error', 0)) : null,
    dependenciesError: dependenciesQuery.error ? (dependenciesQuery.error instanceof ApiError ? dependenciesQuery.error : new ApiError(dependenciesQuery.error?.message ?? 'Unknown error', 0)) : null,
    packetsError: chapterPacketsQuery.error ? (chapterPacketsQuery.error instanceof ApiError ? chapterPacketsQuery.error : new ApiError(chapterPacketsQuery.error?.message ?? 'Unknown error', 0)) : null,
    cardsError: storyboardCardsQuery.error ? (storyboardCardsQuery.error instanceof ApiError ? storyboardCardsQuery.error : new ApiError(storyboardCardsQuery.error?.message ?? 'Unknown error', 0)) : null,
    sequenceCreateOpen,
    sequenceCreateTitle,
    sequenceCreateSummary,
    sequenceEditOpenId,
    sequenceEditTitle,
    sequenceEditSummary,
    chapterCreateOpen,
    chapterCreateTitle,
    chapterCreateObjective,
    chapterCreateConflict,
    chapterCreateStakes,
    chapterCreateSequenceId,
    chapterEditOpenId,
    chapterEditTitle,
    chapterEditObjective,
    chapterEditConflict,
    chapterEditStakes,
    sceneCreateOpen,
    sceneCreateTitle,
    sceneCreateObjective,
    sceneCreateConflict,
    sceneCreateStakes,
    sceneCreateChapterId,
    sceneEditOpenId,
    sceneEditTitle,
    sceneEditObjective,
    sceneEditConflict,
    sceneEditStakes,
    beatCreateOpen,
    beatCreateObjective,
    beatCreateConflict,
    beatCreateStakes,
    beatEditOpenId,
    beatEditObjective,
    beatEditConflict,
    beatEditStakes,
    beatEditArcStage,
    packetCreateOpen,
    packetCreateChapterId,
    cardCreateOpen,
    cardCreateTitle,
    cardCreateContent,
    cardCreateType,
    cardEditOpenId,
    cardEditTitle,
    cardEditContent,
    cardEditType,
    arcCandidateCreateOpen,
    arcCandidateCreateId,
    arcCandidateCreateName,
    arcCandidateCreateSummary,
    stageMapCreateOpen,
    stageMapCreateArcId,
    stageMapCreateNotes,
    stageMapCreateKinds,
  };

  return { state, callbacks };
}
