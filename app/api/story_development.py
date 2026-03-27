from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import Field

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import (
    BranchComparisonRecord,
    BranchMergeDecision,
    BranchStateRef,
    ChapterPacket,
    ChapterPlan,
    CheckerFinding,
    DraftArtifact,
    InspectRunLink,
    ManuscriptDocument,
    PlanningDependency,
    ReviewDecision,
    RevisionSuggestion,
    ScenePlan,
    SequencePlan,
    StoryBranch,
    StoryBranchState,
    StoryDecisionNode,
    StoryFlowDefinition,
    StoryFlowStage,
    StorySuggestionLifecycleState,
)
from app.schemas.base import StrictModel
from app.services.drafting import DraftingNotFoundError, DraftingService
from app.services.editable_flow import (
    EditableFlowNotFoundError,
    EditableFlowService,
    EditableFlowValidationError,
)
from app.services.planning import PlanningNotFoundError, PlanningService
from app.services.review_routing import ReviewRoutingNotFoundError, ReviewRoutingService, ReviewRoutingValidationError
from app.services.story_branching import (
    StoryBranchingNotFoundError,
    StoryBranchingService,
    StoryBranchingValidationError,
)
from app.services.story_decision_review import (
    StoryDecisionReviewNotFoundError,
    StoryDecisionReviewService,
    StoryDecisionReviewValidationError,
)


class StoryDecisionNodeListResponse(StrictModel):
    project_id: str
    items: list[StoryDecisionNode] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class StoryDecisionPathResponse(StrictModel):
    project_id: str
    node: StoryDecisionNode
    parent_path: list[StoryDecisionNode] = Field(default_factory=list)


class CheckerFindingListResponse(StrictModel):
    project_id: str
    items: list[CheckerFinding] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ReviewDecisionListResponse(StrictModel):
    project_id: str
    items: list[ReviewDecision] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class InspectRunLinkListResponse(StrictModel):
    project_id: str
    items: list[InspectRunLink] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class SequencePlanListResponse(StrictModel):
    project_id: str
    items: list[SequencePlan] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ChapterPlanListResponse(StrictModel):
    project_id: str
    items: list[ChapterPlan] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ScenePlanListResponse(StrictModel):
    project_id: str
    items: list[ScenePlan] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class PlanningDependencyListResponse(StrictModel):
    project_id: str
    items: list[PlanningDependency] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ChapterPacketListResponse(StrictModel):
    project_id: str
    items: list[ChapterPacket] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class DraftArtifactListResponse(StrictModel):
    project_id: str
    items: list[DraftArtifact] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ManuscriptDocumentListResponse(StrictModel):
    project_id: str
    items: list[ManuscriptDocument] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class RevisionSuggestionListResponse(StrictModel):
    project_id: str
    items: list[RevisionSuggestion] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ManuscriptDocumentCreateRequest(StrictModel):
    document_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=1_000_000)
    chapter_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    scene_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    current_draft_artifact_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    version: int | None = Field(None, ge=1)


class PromoteDraftToManuscriptRequest(StrictModel):
    project_id: str
    document_id: str
    draft_artifact_id: str
    title: str | None = None
    chapter_id: str | None = None
    scene_id: str | None = None
    version: int | None = None


class ReviewDecisionCreateRequest(StrictModel):
    decision_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    target_kind: str = Field(..., min_length=1, max_length=100)
    target_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    decision: str = Field(..., min_length=1, max_length=50)
    notes: str | None = Field(None, max_length=5000)
    source_context: list[str] = Field(default_factory=list)


class RevisionSuggestionCreateRequest(StrictModel):
    suggestion_id: str
    project_id: str
    target_document_id: str
    source_text: str
    proposed_text: str
    rationale: str
    source_context: list[str] = Field(default_factory=list)
    status: str = StorySuggestionLifecycleState.REQUESTED.value


class StoryBranchListResponse(StrictModel):
    project_id: str
    items: list[StoryBranch] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class BranchStateRefListResponse(StrictModel):
    project_id: str
    items: list[BranchStateRef] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class BranchComparisonListResponse(StrictModel):
    project_id: str
    items: list[BranchComparisonRecord] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class StoryBranchCreateRequest(StrictModel):
    project_id: str
    branch_id: str
    branch_point_id: str
    branch_name: str
    branch_state: StoryBranchState = StoryBranchState.ACTIVE


class StoryBranchActiveRequest(StrictModel):
    project_id: str
    branch_id: str


class BranchComparisonCreateRequest(StrictModel):
    project_id: str
    comparison_id: str
    source_branch_id: str
    target_branch_id: str
    review_notes: list[str] = Field(default_factory=list)


class BranchMergeDecisionCreateRequest(StrictModel):
    project_id: str
    merge_decision_id: str
    source_branch_id: str
    target_branch_id: str
    merge_rationale: str
    resulting_decision_node_ids: list[str] = Field(default_factory=list)


class BranchMergeDecisionListResponse(StrictModel):
    project_id: str
    items: list[BranchMergeDecision] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class FlowStageListResponse(StrictModel):
    project_id: str
    items: list[StoryFlowStage] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class FlowStageCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    stage_kind: str = Field(..., min_length=1, max_length=100)
    display_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    depends_on: list[str] = Field(default_factory=list)
    insert_after_stage_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')


class FlowStageUpdateRequest(StrictModel):
    display_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    depends_on: list[str] | None = None
    writer_notes: str | None = Field(None, max_length=5000)
    custom_prompt_guidance: str | None = Field(None, max_length=10000)


class FlowStageReorderRequest(StrictModel):
    stage_order: list[str] = Field(..., min_length=1)


def build_story_development_router(
    repository: StoryDevelopmentRepository,
    prefix: str = "/story-development",
) -> APIRouter:
    router = APIRouter(prefix=prefix.rstrip("/") if prefix else "", tags=["story-development"])
    decision_service = StoryDecisionReviewService(repository)
    drafting_service = DraftingService(repository)
    planning_service = PlanningService(repository)
    branching_service = StoryBranchingService(repository)
    review_service = ReviewRoutingService(repository, drafting_service=drafting_service, planning_service=planning_service)
    flow_service = EditableFlowService()

    @router.get("/branches", response_model=StoryBranchListResponse)
    def list_story_branches(project_id: str) -> StoryBranchListResponse:
        try:
            items = list(branching_service.list_story_branches(project_id))
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StoryBranchListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.post("/branches", response_model=StoryBranch)
    def create_story_branch(payload: StoryBranchCreateRequest) -> StoryBranch:
        try:
            return branching_service.create_story_branch(
                payload.project_id,
                branch_id=payload.branch_id,
                branch_point_id=payload.branch_point_id,
                branch_name=payload.branch_name,
                branch_state=payload.branch_state,
            )
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Branch point not found.") from exc
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/branches/active", response_model=StoryBranch)
    def get_active_story_branch(project_id: str) -> StoryBranch:
        try:
            return branching_service.get_active_story_branch(project_id)
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Active story branch not found.") from exc

    @router.post("/branches/active", response_model=StoryBranch)
    def select_active_story_branch(payload: StoryBranchActiveRequest) -> StoryBranch:
        try:
            return branching_service.select_active_branch(payload.project_id, branch_id=payload.branch_id)
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story branch not found.") from exc

    @router.post("/branches/comparisons", response_model=BranchComparisonRecord)
    def create_branch_comparison(payload: BranchComparisonCreateRequest) -> BranchComparisonRecord:
        try:
            return branching_service.compare_story_branches(
                payload.project_id,
                comparison_id=payload.comparison_id,
                source_branch_id=payload.source_branch_id,
                target_branch_id=payload.target_branch_id,
                review_notes=payload.review_notes,
            )
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="One or more story branches were not found.") from exc
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/branches/comparisons", response_model=BranchComparisonListResponse)
    def list_branch_comparisons(project_id: str) -> BranchComparisonListResponse:
        try:
            items = list(branching_service.list_branch_comparisons(project_id))
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return BranchComparisonListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.get("/branches/comparisons/{comparison_id}", response_model=BranchComparisonRecord)
    def get_branch_comparison(comparison_id: str, project_id: str) -> BranchComparisonRecord:
        try:
            return branching_service.get_branch_comparison(project_id, comparison_id=comparison_id)
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Branch comparison not found.") from exc

    @router.post("/branches/merge-decisions", response_model=BranchMergeDecision)
    def record_branch_merge_decision(payload: BranchMergeDecisionCreateRequest) -> BranchMergeDecision:
        try:
            return branching_service.record_branch_merge_decision(
                payload.project_id,
                merge_decision_id=payload.merge_decision_id,
                source_branch_id=payload.source_branch_id,
                target_branch_id=payload.target_branch_id,
                merge_rationale=payload.merge_rationale,
                resulting_decision_node_ids=payload.resulting_decision_node_ids,
            )
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="One or more story branches were not found.") from exc
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/branches/merge-decisions", response_model=BranchMergeDecisionListResponse)
    def list_branch_merge_decisions(project_id: str) -> BranchMergeDecisionListResponse:
        try:
            items = list(branching_service.list_branch_merge_decisions(project_id))
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return BranchMergeDecisionListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.get("/branches/merge-decisions/{merge_decision_id}", response_model=BranchMergeDecision)
    def get_branch_merge_decision(merge_decision_id: str, project_id: str) -> BranchMergeDecision:
        try:
            return branching_service.get_branch_merge_decision(project_id, merge_decision_id=merge_decision_id)
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Branch merge decision not found.") from exc

    @router.get("/branches/{branch_id}/state-refs", response_model=BranchStateRefListResponse)
    def list_branch_state_refs(
        branch_id: str,
        project_id: str,
        decision_node_id: str | None = None,
    ) -> BranchStateRefListResponse:
        try:
            if decision_node_id is None:
                items = list(branching_service.list_branch_state_refs(project_id, branch_id=branch_id))
            else:
                items = list(
                    branching_service.list_branch_state_refs_for_decision_node(
                        project_id,
                        branch_id=branch_id,
                        decision_node_id=decision_node_id,
                    )
                )
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story branch not found.") from exc
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return BranchStateRefListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.get("/branches/{branch_id}", response_model=StoryBranch)
    def get_story_branch(branch_id: str, project_id: str) -> StoryBranch:
        try:
            return branching_service.get_story_branch(project_id, branch_id=branch_id)
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story branch not found.") from exc

    # Flow stage endpoints
    @router.get("/flow/stages", response_model=FlowStageListResponse)
    def list_flow_stages(project_id: str) -> FlowStageListResponse:
        try:
            items = flow_service.list_stages(project_id)
            return FlowStageListResponse(project_id=project_id, items=items, meta={"ordered_by": "position_asc"})
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Flow not found for project.") from exc

    @router.post("/flow/stages", response_model=StoryFlowStage)
    def create_flow_stage(payload: FlowStageCreateRequest) -> StoryFlowStage:
        try:
            return flow_service.add_custom_stage(
                project_id=payload.project_id,
                display_name=payload.display_name or f"{payload.stage_kind.replace('_', ' ').title()} Stage",
                description=payload.description,
                stage_kind=payload.stage_kind,
                depends_on=payload.depends_on,
                insert_after_stage_id=payload.insert_after_stage_id,
            )
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Flow not found for project.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/flow/stages/{stage_id}", response_model=StoryFlowStage)
    def update_flow_stage(stage_id: str, project_id: str, payload: FlowStageUpdateRequest) -> StoryFlowStage:
        try:
            updates: dict[str, Any] = {}
            if payload.display_name is not None:
                updates["display_name"] = payload.display_name
            if payload.description is not None:
                updates["description"] = payload.description
            if payload.depends_on is not None:
                updates["depends_on"] = payload.depends_on
            if payload.writer_notes is not None:
                updates["writer_notes"] = payload.writer_notes
            if payload.custom_prompt_guidance is not None:
                updates["custom_prompt_guidance"] = payload.custom_prompt_guidance
            
            return flow_service.redefine_stage(project_id=project_id, stage_id=stage_id, **updates)
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Stage not found.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/flow/stages/reorder", response_model=StoryFlowDefinition)
    def reorder_flow_stages(project_id: str, payload: FlowStageReorderRequest) -> StoryFlowDefinition:
        try:
            return flow_service.reorder_stages(project_id=project_id, stage_order=payload.stage_order)
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Flow not found for project.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/flow/stages/{stage_id}", response_model=StoryFlowStage)
    def delete_flow_stage(stage_id: str, project_id: str) -> StoryFlowStage:
        try:
            return flow_service.delete_custom_stage(project_id=project_id, stage_id=stage_id)
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Stage not found.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/decisions", response_model=StoryDecisionNodeListResponse)
    def list_story_decisions(
        project_id: str,
        subject_type: str | None = None,
        subject_id: str | None = None,
    ) -> StoryDecisionNodeListResponse:
        try:
            items = list(
                decision_service.list_story_decision_nodes(
                    project_id,
                    subject_type=subject_type,
                    subject_id=subject_id,
                )
            )
        except StoryDecisionReviewValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StoryDecisionNodeListResponse(
            project_id=project_id,
            items=items,
            meta={"ordered_by": "decision_made_at_asc"},
        )

    @router.get("/decisions/{node_id}", response_model=StoryDecisionNode)
    def get_story_decision(node_id: str, project_id: str) -> StoryDecisionNode:
        try:
            return decision_service.get_story_decision(project_id, node_id=node_id)
        except StoryDecisionReviewNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story decision node not found.") from exc

    @router.get("/decisions/{node_id}/path", response_model=StoryDecisionPathResponse)
    def get_story_decision_path(node_id: str, project_id: str) -> StoryDecisionPathResponse:
        try:
            review = decision_service.inspect_story_decision(project_id, node_id=node_id)
        except StoryDecisionReviewNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story decision node not found.") from exc
        return StoryDecisionPathResponse(
            project_id=project_id,
            node=review.node,
            parent_path=list(review.parent_path),
        )

    @router.get("/review/findings", response_model=CheckerFindingListResponse)
    def list_checker_findings(
        project_id: str,
        source_object_kind: str | None = None,
        source_object_id: str | None = None,
    ) -> CheckerFindingListResponse:
        try:
            items = list(
                review_service.list_checker_findings(
                    project_id,
                    source_object_kind=source_object_kind,
                    source_object_id=source_object_id,
                )
            )
        except ReviewRoutingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return CheckerFindingListResponse(
            project_id=project_id,
            items=items,
            meta={"ordered_by": "created_at_asc"},
        )

    @router.get("/review/findings/{finding_id}", response_model=CheckerFinding)
    def get_checker_finding(finding_id: str, project_id: str) -> CheckerFinding:
        try:
            return review_service.get_checker_finding(project_id, finding_id=finding_id)
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Checker finding not found.") from exc

    @router.get("/review/decisions", response_model=ReviewDecisionListResponse)
    def list_review_decisions(
        project_id: str,
        target_kind: str | None = None,
        target_id: str | None = None,
    ) -> ReviewDecisionListResponse:
        try:
            items = list(
                review_service.list_review_decisions(
                    project_id,
                    target_kind=target_kind,
                    target_id=target_id,
                )
            )
        except ReviewRoutingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return ReviewDecisionListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.get("/review/decisions/{decision_id}", response_model=ReviewDecision)
    def get_review_decision(decision_id: str, project_id: str) -> ReviewDecision:
        try:
            return review_service.get_review_decision(project_id, decision_id=decision_id)
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Review decision not found.") from exc

    @router.get("/review/inspect-links", response_model=InspectRunLinkListResponse)
    def list_inspect_links(
        project_id: str,
        object_kind: str | None = None,
        object_id: str | None = None,
        run_id: str | None = None,
        logical_run_id: str | None = None,
    ) -> InspectRunLinkListResponse:
        try:
            items = list(
                review_service.list_inspect_run_links(
                    project_id,
                    object_kind=object_kind,
                    object_id=object_id,
                    run_id=run_id,
                    logical_run_id=logical_run_id,
                )
            )
        except ReviewRoutingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return InspectRunLinkListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.get("/review/inspect-links/{link_id}", response_model=InspectRunLink)
    def get_inspect_link(link_id: str, project_id: str) -> InspectRunLink:
        try:
            return review_service.get_inspect_run_link(project_id, link_id=link_id)
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Inspect link not found.") from exc

    @router.get("/planning/sequence-plans", response_model=SequencePlanListResponse)
    def list_sequence_plans(project_id: str) -> SequencePlanListResponse:
        return SequencePlanListResponse(
            project_id=project_id,
            items=list(planning_service.list_sequence_plans(project_id)),
            meta={"ordered_by": "position_asc"},
        )

    @router.get("/planning/sequence-plans/{sequence_id}", response_model=SequencePlan)
    def get_sequence_plan(sequence_id: str, project_id: str) -> SequencePlan:
        try:
            return planning_service.get_sequence_plan(project_id, sequence_id=sequence_id)
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Sequence plan not found.") from exc

    @router.get("/planning/chapter-plans", response_model=ChapterPlanListResponse)
    def list_chapter_plans(project_id: str) -> ChapterPlanListResponse:
        return ChapterPlanListResponse(
            project_id=project_id,
            items=list(planning_service.list_chapter_plans(project_id)),
            meta={"ordered_by": "position_asc"},
        )

    @router.get("/planning/chapter-plans/{chapter_id}", response_model=ChapterPlan)
    def get_chapter_plan(chapter_id: str, project_id: str) -> ChapterPlan:
        try:
            return planning_service.get_chapter_plan(project_id, chapter_id=chapter_id)
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Chapter plan not found.") from exc

    @router.get("/planning/scene-plans", response_model=ScenePlanListResponse)
    def list_scene_plans(project_id: str) -> ScenePlanListResponse:
        return ScenePlanListResponse(
            project_id=project_id,
            items=list(planning_service.list_scene_plans(project_id)),
            meta={"ordered_by": "position_asc"},
        )

    @router.get("/planning/scene-plans/{scene_id}", response_model=ScenePlan)
    def get_scene_plan(scene_id: str, project_id: str) -> ScenePlan:
        try:
            return planning_service.get_scene_plan(project_id, scene_id=scene_id)
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Scene plan not found.") from exc

    @router.get("/planning/dependencies", response_model=PlanningDependencyListResponse)
    def list_planning_dependencies(project_id: str) -> PlanningDependencyListResponse:
        return PlanningDependencyListResponse(
            project_id=project_id,
            items=list(planning_service.list_planning_dependencies(project_id)),
            meta={"ordered_by": "dependency_id_asc"},
        )

    @router.get("/planning/dependencies/{dependency_id}", response_model=PlanningDependency)
    def get_planning_dependency(dependency_id: str, project_id: str) -> PlanningDependency:
        try:
            return planning_service.get_planning_dependency(project_id, dependency_id=dependency_id)
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Planning dependency not found.") from exc

    @router.get("/planning/chapter-packets", response_model=ChapterPacketListResponse)
    def list_chapter_packets(project_id: str) -> ChapterPacketListResponse:
        return ChapterPacketListResponse(
            project_id=project_id,
            items=list(planning_service.list_chapter_packets(project_id)),
            meta={"ordered_by": "chapter_id_asc"},
        )

    @router.get("/planning/chapter-packets/{packet_id}", response_model=ChapterPacket)
    def get_chapter_packet(packet_id: str, project_id: str) -> ChapterPacket:
        try:
            return planning_service.get_chapter_packet(project_id, packet_id=packet_id)
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Chapter packet not found.") from exc

    @router.get("/drafting/draft-artifacts", response_model=DraftArtifactListResponse)
    def list_draft_artifacts(project_id: str) -> DraftArtifactListResponse:
        return DraftArtifactListResponse(
            project_id=project_id,
            items=list(drafting_service.list_draft_artifacts(project_id)),
            meta={"ordered_by": "title_asc"},
        )

    @router.get("/drafting/draft-artifacts/{artifact_id}", response_model=DraftArtifact)
    def get_draft_artifact(artifact_id: str, project_id: str) -> DraftArtifact:
        try:
            return drafting_service.get_draft_artifact(project_id, artifact_id=artifact_id)
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Draft artifact not found.") from exc

    @router.get("/drafting/manuscript-documents", response_model=ManuscriptDocumentListResponse)
    def list_manuscript_documents(project_id: str) -> ManuscriptDocumentListResponse:
        return ManuscriptDocumentListResponse(
            project_id=project_id,
            items=list(drafting_service.list_manuscript_documents(project_id)),
            meta={"ordered_by": "title_asc"},
        )

    @router.get("/drafting/manuscript-documents/{document_id}", response_model=ManuscriptDocument)
    def get_manuscript_document(document_id: str, project_id: str) -> ManuscriptDocument:
        try:
            return drafting_service.get_manuscript_document(project_id, document_id=document_id)
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Manuscript document not found.") from exc

    @router.get("/drafting/revision-suggestions", response_model=RevisionSuggestionListResponse)
    def list_revision_suggestions(project_id: str, target_document_id: str | None = None) -> RevisionSuggestionListResponse:
        if target_document_id is None:
            items = list(drafting_service.list_revision_suggestions(project_id))
        else:
            items = list(
                drafting_service.list_revision_suggestions_for_document(
                    project_id,
                    target_document_id=target_document_id,
                )
            )
        return RevisionSuggestionListResponse(project_id=project_id, items=items, meta={"ordered_by": "suggestion_id_asc"})

    @router.get("/drafting/revision-suggestions/{suggestion_id}", response_model=RevisionSuggestion)
    def get_revision_suggestion(suggestion_id: str, project_id: str) -> RevisionSuggestion:
        try:
            return drafting_service.get_revision_suggestion(project_id, suggestion_id=suggestion_id)
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Revision suggestion not found.") from exc

    @router.post("/drafting/manuscript-documents", response_model=ManuscriptDocument)
    def create_manuscript_document(payload: ManuscriptDocumentCreateRequest) -> ManuscriptDocument:
        """Create a new manuscript document.

        Creates a manuscript document with the specified content and metadata.
        Optionally links to an existing draft artifact for provenance tracking.

        Args:
            payload: Manuscript document creation request with ID, title, content, and optional chapter/scene references.

        Returns:
            The created ManuscriptDocument object.

        Raises:
            HTTPException 404: If the referenced draft artifact does not exist.
        """
        try:
            return drafting_service.save_manuscript_document(
                payload.project_id,
                document_id=payload.document_id,
                content=payload.content,
                title=payload.title,
                chapter_id=payload.chapter_id,
                scene_id=payload.scene_id,
                current_draft_artifact_id=payload.current_draft_artifact_id,
                version=payload.version,
            )
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Referenced draft artifact not found.") from exc

    @router.post("/drafting/promote-draft", response_model=ManuscriptDocument)
    def promote_draft_to_manuscript(payload: PromoteDraftToManuscriptRequest) -> ManuscriptDocument:
        """Promote a draft artifact to a manuscript document.

        Creates a new manuscript document from an existing draft artifact,
        preserving the draft's content and optionally updating metadata.

        Args:
            payload: Promotion request with project ID, target document ID, and source draft artifact ID.

        Returns:
            The created ManuscriptDocument object.

        Raises:
            HTTPException 404: If the referenced draft artifact does not exist.
        """
        try:
            return drafting_service.promote_draft_to_manuscript(
                payload.project_id,
                document_id=payload.document_id,
                draft_artifact_id=payload.draft_artifact_id,
                title=payload.title,
                chapter_id=payload.chapter_id,
                scene_id=payload.scene_id,
                version=payload.version,
            )
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Draft artifact not found.") from exc

    @router.post("/drafting/revision-suggestions", response_model=RevisionSuggestion)
    def create_revision_suggestion(payload: RevisionSuggestionCreateRequest) -> RevisionSuggestion:
        """Create a revision suggestion for a manuscript document.

        Proposes text changes to an existing manuscript document with rationale
        and source context for review.

        Args:
            payload: Revision suggestion request with target document, source/proposed text, and rationale.

        Returns:
            The created RevisionSuggestion object.

        Raises:
            HTTPException 404: If the target manuscript document does not exist.
        """
        try:
            return drafting_service.create_revision_suggestion(
                payload.project_id,
                suggestion_id=payload.suggestion_id,
                target_document_id=payload.target_document_id,
                source_text=payload.source_text,
                proposed_text=payload.proposed_text,
                rationale=payload.rationale,
                source_context=payload.source_context,
                status=payload.status,
            )
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Target manuscript document not found.") from exc

    @router.post("/review/decisions", response_model=ReviewDecision)
    def record_review_decision(payload: ReviewDecisionCreateRequest) -> ReviewDecision:
        """Record a review decision for a target object.

        Records an accept/reject/defer decision on checker findings, artifacts,
        or other reviewable objects with optional notes and context.

        Args:
            payload: Review decision request with target kind/id, decision action, and optional notes.

        Returns:
            The created ReviewDecision object.

        Raises:
            HTTPException 404: If the target object does not exist.
        """
        try:
            return review_service.record_review_decision(
                payload.project_id,
                decision_id=payload.decision_id,
                target_kind=payload.target_kind,
                target_id=payload.target_id,
                decision=payload.decision,
                notes=payload.notes,
                source_context=payload.source_context,
            )
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Target object not found.") from exc

    return router
