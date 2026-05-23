from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import FoundationProfile, FoundationRevision
from app.schemas.base import StrictModel
from app.services.foundation import (
    FoundationNotFoundError,
    FoundationService,
    FoundationValidationError,
)
from pydantic import Field


class FoundationCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    premise: str = Field(..., min_length=1, max_length=10000)
    logline: str = Field(..., min_length=1, max_length=500)
    thematic_spine: str = Field(default="", max_length=2000)
    emotional_promise: str = Field(default="", max_length=2000)
    tone_and_voice_direction: str = Field(default="", max_length=2000)
    target_audience: str = Field(default="", max_length=500)
    narrative_constraints: list[str] = Field(default_factory=list)
    complexity_level: str = Field(default="", max_length=50)
    success_definition: str = Field(default="", max_length=2000)


class FoundationUpdateRequest(StrictModel):
    premise: str | None = Field(None, min_length=1, max_length=10000)
    logline: str | None = Field(None, min_length=1, max_length=500)
    thematic_spine: str | None = Field(None, min_length=1, max_length=2000)
    emotional_promise: str | None = Field(None, min_length=1, max_length=2000)
    tone_and_voice_direction: str | None = Field(None, min_length=1, max_length=2000)
    target_audience: str | None = Field(None, min_length=1, max_length=500)
    narrative_constraints: list[str] | None = None
    complexity_level: str | None = Field(None, min_length=1, max_length=50)
    success_definition: str | None = Field(None, min_length=1, max_length=2000)


class FoundationRevisionListResponse(StrictModel):
    project_id: str
    items: list[FoundationRevision] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class FoundationReviewCue(StrictModel):
    impacted_area: str
    reason: str
    triggering_revision_id: str
    triggering_fields: list[str] = Field(default_factory=list)


class FoundationReviewCueListResponse(StrictModel):
    project_id: str
    items: list[FoundationReviewCue] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class FoundationReadResponse(StrictModel):
    project_id: str
    foundation_id: str
    active_profile: FoundationProfile | None = None
    current_revision_id: str | None = None
    revision_history: list[FoundationRevision] = Field(default_factory=list)
    downstream_review_cues: list[FoundationReviewCue] = Field(default_factory=list)


class FoundationWriteResponse(FoundationReadResponse):
    created_revision: FoundationRevision


__all__ = [
    "FoundationCreateRequest",
    "FoundationReadResponse",
    "FoundationRevisionListResponse",
    "FoundationReviewCue",
    "FoundationReviewCueListResponse",
    "FoundationUpdateRequest",
    "FoundationWriteResponse",
    "register_foundation_routes",
]


def _build_cues(result) -> list[FoundationReviewCue]:
    return [
        FoundationReviewCue(
            impacted_area=cue.impacted_area,
            reason=cue.reason,
            triggering_revision_id=cue.triggering_revision_id,
            triggering_fields=list(cue.triggering_fields),
        )
        for cue in result.downstream_review_cues
    ]


def register_foundation_routes(
    router: APIRouter,
    foundation_service: FoundationService,
) -> None:
    @router.get("/foundation", response_model=FoundationReadResponse)
    def get_foundation(project_id: str) -> FoundationReadResponse:
        """Get the active foundation profile for a project."""
        try:
            result = foundation_service.read_active_foundation(project_id)
            return FoundationReadResponse(
                project_id=result.project_id,
                foundation_id=result.foundation_id,
                active_profile=result.active_profile,
                current_revision_id=result.current_revision_id,
                revision_history=list(result.revision_history),
                downstream_review_cues=_build_cues(result),
            )
        except FoundationNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Foundation not found.") from exc

    @router.post("/foundation", response_model=FoundationWriteResponse, status_code=201)
    def create_foundation(payload: FoundationCreateRequest) -> FoundationWriteResponse:
        """Create a new foundation profile for a project."""
        try:
            foundation_data = {
                "premise": payload.premise,
                "logline": payload.logline,
                "thematic_spine": payload.thematic_spine,
                "emotional_promise": payload.emotional_promise,
                "tone_and_voice_direction": payload.tone_and_voice_direction,
                "target_audience": payload.target_audience,
                "narrative_constraints": payload.narrative_constraints,
                "complexity_level": payload.complexity_level,
                "success_definition": payload.success_definition,
            }
            result = foundation_service.create_foundation_revision(payload.project_id, foundation_data)
            return FoundationWriteResponse(
                project_id=result.project_id,
                foundation_id=result.foundation_id,
                active_profile=result.active_profile,
                current_revision_id=result.current_revision_id,
                revision_history=list(result.revision_history),
                downstream_review_cues=_build_cues(result),
                created_revision=result.created_revision,
            )
        except (FoundationValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/foundation", response_model=FoundationWriteResponse)
    def update_foundation(project_id: str, payload: FoundationUpdateRequest) -> FoundationWriteResponse:
        """Update the active foundation profile for a project."""
        try:
            foundation_data = {
                key: value for key, value in (
                    ("premise", payload.premise),
                    ("logline", payload.logline),
                    ("thematic_spine", payload.thematic_spine),
                    ("emotional_promise", payload.emotional_promise),
                    ("tone_and_voice_direction", payload.tone_and_voice_direction),
                    ("target_audience", payload.target_audience),
                    ("narrative_constraints", payload.narrative_constraints),
                    ("complexity_level", payload.complexity_level),
                    ("success_definition", payload.success_definition),
                ) if value is not None
            }
            if not foundation_data:
                raise HTTPException(status_code=400, detail="At least one field must be provided for update.")
            result = foundation_service.update_foundation_revision(project_id, foundation_data)
            return FoundationWriteResponse(
                project_id=result.project_id,
                foundation_id=result.foundation_id,
                active_profile=result.active_profile,
                current_revision_id=result.current_revision_id,
                revision_history=list(result.revision_history),
                downstream_review_cues=_build_cues(result),
                created_revision=result.created_revision,
            )
        except FoundationNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Foundation not found.") from exc
        except (FoundationValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/foundation/revisions", response_model=FoundationRevisionListResponse)
    def list_foundation_revisions(project_id: str) -> FoundationRevisionListResponse:
        """List all foundation revisions for a project."""
        revisions = foundation_service.list_foundation_revisions(project_id)
        return FoundationRevisionListResponse(
            project_id=project_id,
            items=list(revisions),
            meta={"ordered_by": "created_at_asc"},
        )

    @router.get("/foundation/review-cues", response_model=FoundationReviewCueListResponse)
    def list_foundation_review_cues(project_id: str) -> FoundationReviewCueListResponse:
        """List downstream review cues triggered by foundation changes."""
        cues = foundation_service.list_downstream_review_cues(project_id)
        return FoundationReviewCueListResponse(
            project_id=project_id,
            items=[
                FoundationReviewCue(
                    impacted_area=cue.impacted_area,
                    reason=cue.reason,
                    triggering_revision_id=cue.triggering_revision_id,
                    triggering_fields=list(cue.triggering_fields),
                )
                for cue in cues
            ],
            meta={"ordered_by": "created_at_asc"},
        )
