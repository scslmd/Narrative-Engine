import type { ApiError } from '../../lib/api';
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

export interface PlanningTabState {
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
  sequencesLoading: boolean;
  chaptersLoading: boolean;
  scenesLoading: boolean;
  beatsLoading: boolean;
  dependenciesLoading: boolean;
  packetsLoading: boolean;
  cardsLoading: boolean;
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
  setPacketCreateOpen: (open: boolean) => void;
  setPacketCreateChapterId: (value: string) => void;
  packetCreateSubmit: () => void;
  retrySequences: () => void;
  retryChapters: () => void;
  retryScenes: () => void;
  retryBeats: () => void;
  retryDependencies: () => void;
  retryPackets: () => void;
  retryCards: () => void;
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
  setArcCandidateCreateOpen: (open: boolean) => void;
  setArcCandidateCreateId: (value: string) => void;
  setArcCandidateCreateName: (value: string) => void;
  setArcCandidateCreateSummary: (value: string) => void;
  arcCandidateCreateSubmit: () => void;
  setStageMapCreateOpen: (open: boolean) => void;
  setStageMapCreateArcId: (value: string) => void;
  setStageMapCreateNotes: (value: string) => void;
  setStageMapCreateKinds: (kinds: string[]) => void;
  stageMapCreateSubmit: () => void;
  toggleStageKind: (stage: string) => void;
  selectArc: (arcId: string) => void;
  deselectArc: () => void;
  arcUpdateSelection: (selectionId: string, data: ArcSelectionUpdateRequest) => void;
  arcDeleteSelection: (selectionId: string) => void;
}
