from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import Field

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import (
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
    StoryDecisionNode,
)
from app.schemas.base import StrictModel
from app.services.drafting import DraftingNotFoundError, DraftingService
from app.services.planning import PlanningNotFoundError, PlanningService
from app.services.review_routing import ReviewRoutingNotFoundError, ReviewRoutingService, ReviewRoutingValidationError
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


def build_story_development_router(repository: StoryDevelopmentRepository) -> APIRouter:
    router = APIRouter(prefix="/story-development", tags=["story-development"])
    decision_service = StoryDecisionReviewService(repository)
    drafting_service = DraftingService(repository)
    planning_service = PlanningService(repository)
    review_service = ReviewRoutingService(repository, drafting_service=drafting_service, planning_service=planning_service)

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

    return router
