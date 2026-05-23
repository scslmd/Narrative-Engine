from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import InspectRunLink, ReviewDecision
from app.schemas.base import StrictModel
from app.services.review_routing import ReviewRoutingNotFoundError, ReviewRoutingService, ReviewRoutingValidationError
from app.services.story_decision_review import (
    StoryDecisionReviewNotFoundError,
    StoryDecisionReviewService,
    StoryDecisionReviewValidationError,
)
from pydantic import Field


class ReviewDecisionCreateRequest(StrictModel):
    decision_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    target_kind: str = Field(..., min_length=1, max_length=100)
    target_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    decision: str = Field(..., min_length=1, max_length=50)
    notes: str | None = Field(None, max_length=5000)
    source_context: list[str] = Field(default_factory=list)


class InspectRunLinkCreateRequest(StrictModel):
    link_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    object_kind: str = Field(..., min_length=1, max_length=100)
    object_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    logical_run_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    run_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    run_kind: str = Field(..., min_length=1, max_length=100)
    attempt_number: int | None = Field(None, ge=1)
    label: str | None = Field(None, max_length=2000)


__all__ = [
    "InspectRunLinkCreateRequest",
    "ReviewDecisionCreateRequest",
    "register_review_routes",
]


def register_review_routes(
    router: APIRouter,
    decision_service: StoryDecisionReviewService,
    review_service: ReviewRoutingService,
) -> None:
    @router.get("/decisions", response_model=None)
    def list_story_decisions(
        project_id: str,
        subject_type: str | None = None,
        subject_id: str | None = None,
    ):
        from app.api.story_development.common_models import StoryDecisionNodeListResponse
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

    @router.get("/decisions/{node_id}", response_model=None)
    def get_story_decision(node_id: str, project_id: str):
        from app.schemas import StoryDecisionNode
        try:
            return decision_service.get_story_decision(project_id, node_id=node_id)
        except StoryDecisionReviewNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story decision node not found.") from exc

    @router.get("/decisions/{node_id}/path", response_model=None)
    def get_story_decision_path(node_id: str, project_id: str):
        from app.api.story_development.common_models import StoryDecisionPathResponse
        try:
            review = decision_service.inspect_story_decision(project_id, node_id=node_id)
        except StoryDecisionReviewNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story decision node not found.") from exc
        return StoryDecisionPathResponse(
            project_id=project_id,
            node=review.node,
            parent_path=list(review.parent_path),
        )

    @router.get("/review/findings", response_model=None)
    def list_checker_findings(
        project_id: str,
        source_object_kind: str | None = None,
        source_object_id: str | None = None,
    ):
        from app.api.story_development.common_models import CheckerFindingListResponse
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

    @router.get("/review/findings/{finding_id}", response_model=None)
    def get_checker_finding(finding_id: str, project_id: str):
        try:
            return review_service.get_checker_finding(project_id, finding_id=finding_id)
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Checker finding not found.") from exc

    @router.get("/review/decisions", response_model=None)
    def list_review_decisions(
        project_id: str,
        target_kind: str | None = None,
        target_id: str | None = None,
    ):
        from app.api.story_development.common_models import ReviewDecisionListResponse
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

    @router.get("/review/decisions/{decision_id}", response_model=None)
    def get_review_decision(decision_id: str, project_id: str):
        try:
            return review_service.get_review_decision(project_id, decision_id=decision_id)
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Review decision not found.") from exc

    @router.get("/review/inspect-links", response_model=None)
    def list_inspect_links(
        project_id: str,
        object_kind: str | None = None,
        object_id: str | None = None,
        run_id: str | None = None,
        logical_run_id: str | None = None,
    ):
        from app.api.story_development.common_models import InspectRunLinkListResponse
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

    @router.get("/review/inspect-links/{link_id}", response_model=None)
    def get_inspect_link(link_id: str, project_id: str):
        try:
            return review_service.get_inspect_run_link(project_id, link_id=link_id)
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Inspect link not found.") from exc

    @router.post("/review/inspect-links", response_model=InspectRunLink, status_code=201)
    def create_inspect_link(payload: InspectRunLinkCreateRequest) -> InspectRunLink:
        """Create an inspect run link pointing to a review or execution run.

        Creates a bidirectional link between a story object and a run inspection
        target, enabling "Jump to Source" navigation from review findings.

        Args:
            payload: Inspect link creation request with target object and run identifiers.

        Returns:
            The created InspectRunLink object.

        Raises:
            HTTPException 404: If the target object does not exist.
        """
        try:
            return review_service.create_inspect_link(
                payload.project_id,
                link_id=payload.link_id,
                object_kind=payload.object_kind,
                object_id=payload.object_id,
                logical_run_id=payload.logical_run_id,
                run_id=payload.run_id,
                run_kind=payload.run_kind,
                attempt_number=payload.attempt_number,
                label=payload.label,
            )
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Target object not found.") from exc

    @router.post("/review/decisions", response_model=ReviewDecision, status_code=201)
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
