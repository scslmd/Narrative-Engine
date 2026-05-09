import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
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

  const storyboardCardsQuery = useQuery({
    queryKey: ['planning-storyboard-cards', projectId],
    queryFn: () => getStoryboardCards(projectId || ''),
    enabled: Boolean(projectId) && tab === 'planning',
  });

  const arcCandidatesQuery = useQuery({
    queryKey: ['arc-candidates', projectId],
    queryFn: () => getArcCandidates(projectId || ''),
    enabled: Boolean(projectId) && tab === 'arcs',
  });

  const arcSelectionsQuery = useQuery({
    queryKey: ['arc-selections', projectId],
    queryFn: () => getArcSelections(projectId || ''),
    enabled: Boolean(projectId) && tab === 'arcs',
  });

  const arcStageMapsQuery = useQuery({
    queryKey: ['arc-stage-maps', projectId],
    queryFn: () => getArcStageMaps(projectId || ''),
    enabled: Boolean(projectId) && tab === 'arcs',
  });

  const arcComparisonsQuery = useQuery({
    queryKey: ['arc-comparisons', projectId],
    queryFn: () => getArcComparisons(projectId || ''),
    enabled: Boolean(projectId) && tab === 'arcs',
  });

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

  const storyboardCardCreateMutation = useMutation({
    mutationFn: (data: Parameters<typeof createStoryboardCard>[1]) =>
      createStoryboardCard(projectId || '', data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning-storyboard-cards', projectId] });
    },
  });

  const storyboardCardUpdateMutation = useMutation({
    mutationFn: (data: { cardId: string; payload: Parameters<typeof updateStoryboardCard>[1] }) =>
      updateStoryboardCard(data.cardId, data.payload, projectId || undefined),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning-storyboard-cards', projectId] });
    },
  });

  const storyboardCardDeleteMutation = useMutation({
    mutationFn: (cardId: string) =>
      deleteStoryboardCard(cardId, projectId || undefined),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning-storyboard-cards', projectId] });
    },
  });

  const storyboardCardReindexMutation = useMutation({
    mutationFn: (data: { columnId: string; orderedIds: string[] }) =>
      reindexColumn(data.columnId, data.orderedIds, projectId || undefined),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['planning-storyboard-cards', projectId] });
    },
  });

  const selectArcMutation = useMutation({
    mutationFn: (arcId: string) =>
      createArcSelection({
        project_id: projectId || '',
        selected_arc: arcId,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['arcs', 'selections', projectId] });
      void queryClient.invalidateQueries({ queryKey: ['arcs', 'candidates', projectId] });
    },
  });

  const deselectArcMutation = useMutation({
    mutationFn: () => {
      const selections = arcSelectionsQuery.data;
      const selection = selections?.[0];
      if (!selection) return Promise.resolve();
      return deleteArcSelection(selection.selection_id, projectId || '');
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['arcs', 'selections', projectId] });
      void queryClient.invalidateQueries({ queryKey: ['arcs', 'candidates', projectId] });
    },
  });

  const arcCandidateCreateMutation = useMutation({
    mutationFn: (data: { arc_id: string; project_id: string; name: string; summary: string }) =>
      createArcCandidate({
        arc_id: data.arc_id,
        project_id: data.project_id,
        name: data.name,
        summary: data.summary,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['arcs', 'candidates', projectId] });
      void queryClient.invalidateQueries({ queryKey: ['arcs', 'selections', projectId] });
    },
  });

  const stageMapCreateMutation = useMutation({
    mutationFn: (data: { arc_id: string; project_id: string; stage_kinds: string[]; notes?: string | null }) =>
      createArcStageMap({
        project_id: data.project_id,
        arc_id: data.arc_id,
        stage_kinds: data.stage_kinds,
        notes: data.notes || undefined,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['arc-stage-maps', projectId] });
    },
  });

  const arcSelectionUpdateMutation = useMutation({
    mutationFn: ({ selectionId, data }: { selectionId: string; data: ArcSelectionUpdateRequest }) =>
      updateArcSelection(selectionId, data, projectId || ''),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['arc-selections', projectId] });
    },
  });

  const arcSelectionDeleteMutation = useMutation({
    mutationFn: (selectionId: string) =>
      deleteArcSelection(selectionId, projectId || ''),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['arc-selections', projectId] });
    },
  });

  // Form state
  const [sequenceCreateOpen, setSequenceCreateOpen] = useState(false);
  const [sequenceCreateTitle, setSequenceCreateTitle] = useState('');
  const [sequenceCreateSummary, setSequenceCreateSummary] = useState('');
  const [sequenceEditOpenId, setSequenceEditOpenId] = useState<string | null>(null);
  const [sequenceEditTitle, setSequenceEditTitle] = useState('');
  const [sequenceEditSummary, setSequenceEditSummary] = useState('');

  const [chapterCreateOpen, setChapterCreateOpen] = useState(false);
  const [chapterCreateTitle, setChapterCreateTitle] = useState('');
  const [chapterCreateObjective, setChapterCreateObjective] = useState('');
  const [chapterCreateConflict, setChapterCreateConflict] = useState('');
  const [chapterCreateStakes, setChapterCreateStakes] = useState('');
  const [chapterCreateSequenceId, setChapterCreateSequenceId] = useState('');
  const [chapterEditOpenId, setChapterEditOpenId] = useState<string | null>(null);
  const [chapterEditTitle, setChapterEditTitle] = useState('');
  const [chapterEditObjective, setChapterEditObjective] = useState('');
  const [chapterEditConflict, setChapterEditConflict] = useState('');
  const [chapterEditStakes, setChapterEditStakes] = useState('');

  const [sceneCreateOpen, setSceneCreateOpen] = useState(false);
  const [sceneCreateTitle, setSceneCreateTitle] = useState('');
  const [sceneCreateObjective, setSceneCreateObjective] = useState('');
  const [sceneCreateConflict, setSceneCreateConflict] = useState('');
  const [sceneCreateStakes, setSceneCreateStakes] = useState('');
  const [sceneCreateChapterId, setSceneCreateChapterId] = useState('');
  const [sceneEditOpenId, setSceneEditOpenId] = useState<string | null>(null);
  const [sceneEditTitle, setSceneEditTitle] = useState('');
  const [sceneEditObjective, setSceneEditObjective] = useState('');
  const [sceneEditConflict, setSceneEditConflict] = useState('');
  const [sceneEditStakes, setSceneEditStakes] = useState('');

  const [beatCreateOpen, setBeatCreateOpen] = useState(false);
  const [beatCreateObjective, setBeatCreateObjective] = useState('');
  const [beatCreateConflict, setBeatCreateConflict] = useState('');
  const [beatCreateStakes, setBeatCreateStakes] = useState('');
  const [beatEditOpenId, setBeatEditOpenId] = useState<string | null>(null);
  const [beatEditObjective, setBeatEditObjective] = useState('');
  const [beatEditConflict, setBeatEditConflict] = useState('');
  const [beatEditStakes, setBeatEditStakes] = useState('');
  const [beatEditArcStage, setBeatEditArcStage] = useState('');

  const [packetCreateOpen, setPacketCreateOpen] = useState(false);
  const [packetCreateChapterId, setPacketCreateChapterId] = useState('');

  const [cardCreateOpen, setCardCreateOpen] = useState(false);
  const [cardCreateTitle, setCardCreateTitle] = useState('');
  const [cardCreateContent, setCardCreateContent] = useState('');
  const [cardCreateType, setCardCreateType] = useState('idea');

  const [cardEditOpenId, setCardEditOpenId] = useState<string | null>(null);
  const [cardEditTitle, setCardEditTitle] = useState('');
  const [cardEditContent, setCardEditContent] = useState('');
  const [cardEditType, setCardEditType] = useState('idea');

  const [arcCandidateCreateOpen, setArcCandidateCreateOpen] = useState(false);
  const [arcCandidateCreateId, setArcCandidateCreateId] = useState('');
  const [arcCandidateCreateName, setArcCandidateCreateName] = useState('');
  const [arcCandidateCreateSummary, setArcCandidateCreateSummary] = useState('');

  const [stageMapCreateOpen, setStageMapCreateOpen] = useState(false);
  const [stageMapCreateArcId, setStageMapCreateArcId] = useState('');
  const [stageMapCreateNotes, setStageMapCreateNotes] = useState('');
  const [stageMapCreateKinds, setStageMapCreateKinds] = useState<string[]>([]);

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
      setStageMapCreateKinds((prev) =>
        prev.includes(stage) ? prev.filter((s) => s !== stage) : [...prev, stage]
      );
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
