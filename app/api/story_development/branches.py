from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import Field

from app.schemas import BranchComparisonRecord, BranchMergeDecision, BranchStateRef, StoryBranch, StoryBranchState
from app.schemas.base import StrictModel
from app.services.story_branching import (
    StoryBranchingNotFoundError,
    StoryBranchingService,
    StoryBranchingValidationError,
)


# Branch request/response models
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


__all__ = [
    "BranchComparisonCreateRequest",
    "BranchComparisonListResponse",
    "BranchMergeDecisionCreateRequest",
    "BranchMergeDecisionListResponse",
    "BranchStateRefListResponse",
    "StoryBranchActiveRequest",
    "StoryBranchCreateRequest",
    "StoryBranchListResponse",
    "register_branch_routes",
]


def register_branch_routes(
    router: APIRouter,
    branching_service: StoryBranchingService,
) -> None:
    @router.get("/branches", response_model=StoryBranchListResponse)
    def list_story_branches(project_id: str) -> StoryBranchListResponse:
        try:
            items = list(branching_service.list_story_branches(project_id))
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StoryBranchListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.post("/branches", response_model=StoryBranch, status_code=201)
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

    @router.post("/branches/comparisons", response_model=BranchComparisonRecord, status_code=201)
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

    @router.post("/branches/merge-decisions", response_model=BranchMergeDecision, status_code=201)
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