import { SequencePlanSection } from './SequencePlanSection';
import { ChapterPlanSection } from './ChapterPlanSection';
import { ScenePlanSection } from './ScenePlanSection';
import { BeatPlanSection } from './BeatPlanSection';
import { DependenciesSection } from './DependenciesSection';
import { ChapterPacketsSection } from './ChapterPacketsSection';
import { StoryboardCardsSection } from './StoryboardCardsSection';
import { ArcsTab } from './ArcsTab';
import type { PlanningTabState, PlanningTabCallbacks } from '../../hooks/usePlanningTab';

export interface PlanningTabProps {
  isDark: boolean;
  activeTab: 'planning' | 'arcs';
  state: PlanningTabState;
  callbacks: PlanningTabCallbacks;
}

export function PlanningTab({ isDark, state, callbacks }: PlanningTabProps) {
  return (
    <div className={`p-5 space-y-5 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
      <SequencePlanSection
        plans={state.sequencePlans} isLoading={state.sequencesLoading}
        error={state.sequencesError} onRetry={callbacks.retrySequences}
        createOpen={state.sequenceCreateOpen} createTitle={state.sequenceCreateTitle} createSummary={state.sequenceCreateSummary}
        editOpenId={state.sequenceEditOpenId} editTitle={state.sequenceEditTitle} editSummary={state.sequenceEditSummary}
        onCreateOpen={() => { callbacks.setSequenceCreateOpen(true); callbacks.setSequenceCreateTitle(''); callbacks.setSequenceCreateSummary(''); }}
        onCreateClose={() => callbacks.setSequenceCreateOpen(false)}
        onCreateTitleChange={callbacks.setSequenceCreateTitle} onCreateSummaryChange={callbacks.setSequenceCreateSummary}
        onCreate={callbacks.sequenceCreateSubmit}
        onEditOpen={callbacks.openEditSequence}
        onEditClose={() => { callbacks.setSequenceEditOpenId(null); callbacks.setSequenceEditTitle(''); callbacks.setSequenceEditSummary(''); }}
        onEditTitleChange={callbacks.setSequenceEditTitle} onEditSummaryChange={callbacks.setSequenceEditSummary}
        onUpdate={callbacks.sequenceUpdateSubmit}
        onReorderUp={(index) => callbacks.sequenceReorder('up', index)}
        onReorderDown={(index) => callbacks.sequenceReorder('down', index)}
        onCreateButtonDisabled={!state.sequenceCreateTitle.trim()}
        onUpdateButtonDisabled={false}
      />

      <ChapterPlanSection
        plans={state.chapterPlans} isLoading={state.chaptersLoading}
        error={state.chaptersError} onRetry={callbacks.retryChapters}
        createOpen={state.chapterCreateOpen} createTitle={state.chapterCreateTitle}
        createObjective={state.chapterCreateObjective} createConflict={state.chapterCreateConflict} createStakes={state.chapterCreateStakes}
        createSequenceId={state.chapterCreateSequenceId}
        editOpenId={state.chapterEditOpenId} editTitle={state.chapterEditTitle}
        editObjective={state.chapterEditObjective} editConflict={state.chapterEditConflict} editStakes={state.chapterEditStakes}
        onCreateOpen={() => { callbacks.setChapterCreateOpen(true); callbacks.setChapterCreateTitle(''); callbacks.setChapterCreateObjective(''); callbacks.setChapterCreateConflict(''); callbacks.setChapterCreateStakes(''); callbacks.setChapterCreateSequenceId(''); }}
        onCreateClose={() => callbacks.setChapterCreateOpen(false)}
        onCreateTitleChange={callbacks.setChapterCreateTitle} onCreateObjectiveChange={callbacks.setChapterCreateObjective}
        onCreateConflictChange={callbacks.setChapterCreateConflict} onCreateStakesChange={callbacks.setChapterCreateStakes}
        onCreateSequenceIdChange={callbacks.setChapterCreateSequenceId}
        onCreate={callbacks.chapterCreateSubmit}
        onEditOpen={callbacks.openEditChapter}
        onEditClose={() => { callbacks.setChapterEditOpenId(null); callbacks.setChapterEditTitle(''); callbacks.setChapterEditObjective(''); callbacks.setChapterEditConflict(''); callbacks.setChapterEditStakes(''); }}
        onEditTitleChange={callbacks.setChapterEditTitle} onEditObjectiveChange={callbacks.setChapterEditObjective}
        onEditConflictChange={callbacks.setChapterEditConflict} onEditStakesChange={callbacks.setChapterEditStakes}
        onUpdate={callbacks.chapterUpdateSubmit}
        onReorderUp={(index) => callbacks.chapterReorder('up', index)}
        onReorderDown={(index) => callbacks.chapterReorder('down', index)}
        onCreateButtonDisabled={!state.chapterCreateTitle.trim() || !state.chapterCreateObjective.trim()}
        onUpdateButtonDisabled={false}
      />

      <ScenePlanSection
        plans={state.scenePlans} isLoading={state.scenesLoading}
        error={state.scenesError} onRetry={callbacks.retryScenes}
        createOpen={state.sceneCreateOpen} createTitle={state.sceneCreateTitle}
        createObjective={state.sceneCreateObjective} createConflict={state.sceneCreateConflict} createStakes={state.sceneCreateStakes}
        createChapterId={state.sceneCreateChapterId}
        editOpenId={state.sceneEditOpenId} editTitle={state.sceneEditTitle}
        editObjective={state.sceneEditObjective} editConflict={state.sceneEditConflict} editStakes={state.sceneEditStakes}
        onCreateOpen={() => { callbacks.setSceneCreateOpen(true); callbacks.setSceneCreateTitle(''); callbacks.setSceneCreateObjective(''); callbacks.setSceneCreateConflict(''); callbacks.setSceneCreateStakes(''); callbacks.setSceneCreateChapterId(''); }}
        onCreateClose={() => callbacks.setSceneCreateOpen(false)}
        onCreateTitleChange={callbacks.setSceneCreateTitle} onCreateObjectiveChange={callbacks.setSceneCreateObjective}
        onCreateConflictChange={callbacks.setSceneCreateConflict} onCreateStakesChange={callbacks.setSceneCreateStakes}
        onCreateChapterIdChange={callbacks.setSceneCreateChapterId}
        onCreate={callbacks.sceneCreateSubmit}
        onEditOpen={callbacks.openEditScene}
        onEditClose={() => { callbacks.setSceneEditOpenId(null); callbacks.setSceneEditTitle(''); callbacks.setSceneEditObjective(''); callbacks.setSceneEditConflict(''); callbacks.setSceneEditStakes(''); }}
        onEditTitleChange={callbacks.setSceneEditTitle} onEditObjectiveChange={callbacks.setSceneEditObjective}
        onEditConflictChange={callbacks.setSceneEditConflict} onEditStakesChange={callbacks.setSceneEditStakes}
        onUpdate={callbacks.sceneUpdateSubmit}
        onReorderUp={(index) => callbacks.sceneReorder('up', index)}
        onReorderDown={(index) => callbacks.sceneReorder('down', index)}
        onCreateButtonDisabled={!state.sceneCreateTitle.trim() || !state.sceneCreateObjective.trim()}
        onUpdateButtonDisabled={false}
      />

      <BeatPlanSection
        plans={state.beatPlans} isLoading={state.beatsLoading}
        error={state.beatsError} onRetry={callbacks.retryBeats}
        createOpen={state.beatCreateOpen} createObjective={state.beatCreateObjective}
        createConflict={state.beatCreateConflict} createStakes={state.beatCreateStakes}
        editOpenId={state.beatEditOpenId} editObjective={state.beatEditObjective}
        editConflict={state.beatEditConflict} editStakes={state.beatEditStakes} editArcStage={state.beatEditArcStage}
        onCreateOpen={() => { callbacks.setBeatCreateOpen(true); callbacks.setBeatCreateObjective(''); callbacks.setBeatCreateConflict(''); callbacks.setBeatCreateStakes(''); }}
        onCreateClose={() => callbacks.setBeatCreateOpen(false)}
        onCreateObjectiveChange={callbacks.setBeatCreateObjective} onCreateConflictChange={callbacks.setBeatCreateConflict}
        onCreateStakesChange={callbacks.setBeatCreateStakes}
        onCreate={callbacks.beatCreateSubmit}
        onEditOpen={callbacks.openEditBeat}
        onEditClose={() => { callbacks.setBeatEditOpenId(null); callbacks.setBeatEditObjective(''); callbacks.setBeatEditConflict(''); callbacks.setBeatEditStakes(''); callbacks.setBeatEditArcStage(''); }}
        onEditObjectiveChange={callbacks.setBeatEditObjective} onEditConflictChange={callbacks.setBeatEditConflict}
        onEditStakesChange={callbacks.setBeatEditStakes} onEditArcStageChange={callbacks.setBeatEditArcStage}
        onUpdate={callbacks.beatUpdateSubmit}
        onCreateButtonDisabled={!state.beatCreateObjective.trim() || !state.beatCreateConflict.trim()}
        onUpdateButtonDisabled={false}
      />

      <DependenciesSection
        dependencies={state.dependencies}
        isLoading={state.dependenciesLoading}
        error={state.dependenciesError} onRetry={callbacks.retryDependencies}
      />

      <ChapterPacketsSection
        packets={state.chapterPackets}
        isLoading={state.packetsLoading}
        error={state.packetsError} onRetry={callbacks.retryPackets}
        createOpen={state.packetCreateOpen}
        createChapterId={state.packetCreateChapterId}
        onCreateOpen={() => callbacks.setPacketCreateOpen(true)}
        onCreateClose={() => callbacks.setPacketCreateOpen(false)}
        onCreateChapterIdChange={callbacks.setPacketCreateChapterId}
        onCreate={callbacks.packetCreateSubmit}
        onCreateButtonDisabled={!state.packetCreateChapterId.trim()}
      />

      <StoryboardCardsSection
        cards={state.storyboardCards}
        isLoading={state.cardsLoading}
        error={state.cardsError} onRetry={callbacks.retryCards}
        createOpen={state.cardCreateOpen}
        createTitle={state.cardCreateTitle}
        createContent={state.cardCreateContent}
        createType={state.cardCreateType}
        onCreateOpen={() => {
          callbacks.setCardCreateOpen(true);
          callbacks.setCardCreateTitle('');
          callbacks.setCardCreateContent('');
          callbacks.setCardCreateType('idea');
        }}
        onCreateClose={() => callbacks.setCardCreateOpen(false)}
        onCreateTitleChange={callbacks.setCardCreateTitle}
        onCreateContentChange={callbacks.setCardCreateContent}
        onCreateTypeChange={callbacks.setCardCreateType}
        onCreate={callbacks.cardCreateSubmit}
        onCreateButtonDisabled={!state.cardCreateTitle.trim()}
        editOpenId={state.cardEditOpenId}
        editTitle={state.cardEditTitle}
        editContent={state.cardEditContent}
        editType={state.cardEditType}
        onEditOpen={callbacks.openEditCard}
        onEditClose={() => { callbacks.setCardEditOpenId(null); callbacks.setCardEditTitle(''); callbacks.setCardEditContent(''); callbacks.setCardEditType('idea'); }}
        onEditTitleChange={callbacks.setCardEditTitle}
        onEditContentChange={callbacks.setCardEditContent}
        onEditTypeChange={callbacks.setCardEditType}
        onUpdate={callbacks.cardUpdateSubmit}
        onDelete={callbacks.cardDelete}
        onReorder={callbacks.cardReorder}
        onUpdateButtonDisabled={false}
      />

      <ArcsTab
        data={{
          arcCandidates: state.arcCandidates,
          arcSelections: state.arcSelections,
          arcStageMaps: state.arcStageMaps,
          arcComparisons: state.arcComparisons,
          selectedArcId: state.selectedArcId,
          candidatesLoading: state.candidatesLoading,
          selectionsLoading: state.selectionsLoading,
          stageMapsLoading: state.stageMapsLoading,
          comparisonsLoading: state.comparisonsLoading,
        }}
        actions={{
          onUpdateSelection: callbacks.arcUpdateSelection,
          onDeleteSelection: callbacks.arcDeleteSelection,
        }}
        tab={{
          arcCandidateCreateOpen: state.arcCandidateCreateOpen,
          arcCandidateCreateId: state.arcCandidateCreateId,
          arcCandidateCreateName: state.arcCandidateCreateName,
          arcCandidateCreateSummary: state.arcCandidateCreateSummary,
          stageMapCreateOpen: state.stageMapCreateOpen,
          stageMapCreateArcId: state.stageMapCreateArcId,
          stageMapCreateNotes: state.stageMapCreateNotes,
          stageMapCreateKinds: state.stageMapCreateKinds,
          onCreateArcCandidate: callbacks.arcCandidateCreateSubmit,
          onSetArcCandidateCreateOpen: callbacks.setArcCandidateCreateOpen,
          onSetArcCandidateCreateId: callbacks.setArcCandidateCreateId,
          onSetArcCandidateCreateName: callbacks.setArcCandidateCreateName,
          onSetArcCandidateCreateSummary: callbacks.setArcCandidateCreateSummary,
          onStageMapCreate: callbacks.stageMapCreateSubmit,
          onSetStageMapCreateOpen: callbacks.setStageMapCreateOpen,
          onSetStageMapCreateArcId: callbacks.setStageMapCreateArcId,
          onSetStageMapCreateNotes: callbacks.setStageMapCreateNotes,
          onSetStageMapCreateKinds: callbacks.setStageMapCreateKinds,
          onToggleStageKind: callbacks.toggleStageKind,
          onSelectArc: callbacks.selectArc,
          onDeselectArc: callbacks.deselectArc,
        }}
      />
    </div>
  );
}
