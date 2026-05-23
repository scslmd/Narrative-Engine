from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import ArcCandidate, ArcComparisonRecord, ArcSelection, ArcStageMap
from app.schemas.base import StrictModel
from app.services.story_knowledge import (
    StoryKnowledgeNotFoundError,
    StoryKnowledgeService,
    StoryKnowledgeValidationError,
)
from pydantic import Field


class ArcCandidateListResponse(StrictModel):
    project_id: str
    items: list[ArcCandidate] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ArcSelectionListResponse(StrictModel):
    project_id: str
    items: list[ArcSelection] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ArcStageMapListResponse(StrictModel):
    project_id: str
    items: list[ArcStageMap] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ArcComparisonListResponse(StrictModel):
    project_id: str
    items: list[ArcComparisonRecord] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ArcCandidateCreateRequest(StrictModel):
    arc_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    name: str = Field(..., min_length=1, max_length=500)
    summary: str = Field(..., min_length=1, max_length=5000)
    stage_map_notes: list[str] = Field(default_factory=list)
    fit_notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ArcSelectionCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    selected_arc: ArcCandidateCreateRequest | str = Field(...)
    rejected_arc_ids: list[str] = Field(default_factory=list)
    comparison_notes: list[str] = Field(default_factory=list)
    stage_map: ArcStageMapCreateRequest | None = None


class ArcSelectionUpdateRequest(StrictModel):
    comparison_notes: list[str] | None = None
    stage_map: ArcStageMapCreateRequest | None = None


class ArcStageMapCreateRequest(StrictModel):
    arc_id: str = Field(..., min_length=1, max_length=255)
    stage_kinds: list[str] = Field(..., min_length=1)
    notes: str | None = None


class ArcComparisonRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    candidates: list[str | ArcCandidateCreateRequest] = Field(..., min_length=2)


__all__ = [
    "ArcCandidateCreateRequest",
    "ArcCandidateListResponse",
    "ArcComparisonListResponse",
    "ArcComparisonRequest",
    "ArcSelectionCreateRequest",
    "ArcSelectionListResponse",
    "ArcSelectionUpdateRequest",
    "ArcStageMapCreateRequest",
    "ArcStageMapListResponse",
    "register_arc_routes",
]


def register_arc_routes(
    router: APIRouter,
    story_knowledge_service: StoryKnowledgeService,
) -> None:
    @router.get("/arcs/candidates", response_model=ArcCandidateListResponse)
    def list_arc_candidates(project_id: str) -> ArcCandidateListResponse:
        """List all arc candidates for a project."""
        try:
            candidates = list(story_knowledge_service.list_arc_candidates(project_id))
            return ArcCandidateListResponse(
                project_id=project_id,
                items=candidates,
                meta={"ordered_by": "candidate_id_asc"},
            )
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/arcs/selections", response_model=ArcSelectionListResponse)
    def list_arc_selections(project_id: str) -> ArcSelectionListResponse:
        """List all arc selections for a project."""
        selections = list(story_knowledge_service.list_arc_selections(project_id))
        return ArcSelectionListResponse(
            project_id=project_id,
            items=selections,
            meta={"ordered_by": "created_at_asc"},
        )

    @router.get("/arcs/stage-maps", response_model=ArcStageMapListResponse)
    def list_arc_stage_maps(project_id: str) -> ArcStageMapListResponse:
        """List all arc stage maps for a project."""
        try:
            stage_maps = list(story_knowledge_service.list_arc_stage_maps(project_id))
            return ArcStageMapListResponse(
                project_id=project_id,
                items=stage_maps,
                meta={"ordered_by": "stage_id_asc"},
            )
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/arcs/comparisons", response_model=ArcComparisonListResponse)
    def list_arc_comparisons(project_id: str) -> ArcComparisonListResponse:
        """List all arc comparisons for a project."""
        try:
            comparisons = list(story_knowledge_service.list_arc_comparisons(project_id))
            flat: list[ArcComparisonRecord] = []
            for comparison_tuple in comparisons:
                for record in comparison_tuple:
                    if isinstance(record, ArcComparisonRecord):
                        flat.append(record)
            return ArcComparisonListResponse(
                project_id=project_id,
                items=flat,
                meta={"ordered_by": "created_at_desc"},
            )
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/arcs/candidates", response_model=ArcCandidate, status_code=201)
    def create_arc_candidate(payload: ArcCandidateCreateRequest) -> ArcCandidate:
        """Create a new arc candidate for a project."""
        try:
            candidate = story_knowledge_service.upsert_arc_candidate(
                project_id=payload.project_id,
                arc_id=payload.arc_id,
                name=payload.name,
                summary=payload.summary,
                stage_map_notes=payload.stage_map_notes,
                fit_notes=payload.fit_notes,
                tags=payload.tags,
            )
            return candidate
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/arcs/comparisons", response_model=ArcCandidateListResponse)
    def compare_arc_candidates_endpoint(payload: ArcComparisonRequest) -> ArcCandidateListResponse:
        """Score and rank arc candidates for a project."""
        try:
            normalized_candidates: list = []
            for candidate in payload.candidates:
                if isinstance(candidate, ArcCandidateCreateRequest):
                    normalized_candidates.append({
                        "arc_id": candidate.arc_id,
                        "project_id": candidate.project_id,
                        "name": candidate.name,
                        "summary": candidate.summary,
                        "stage_map_notes": candidate.stage_map_notes,
                        "fit_notes": candidate.fit_notes,
                        "tags": candidate.tags,
                    })
                else:
                    normalized_candidates.append(candidate)
            comparisons = story_knowledge_service.compare_arc_candidates(
                project_id=payload.project_id,
                candidates=normalized_candidates,
            )
            ranked_candidates = sorted(comparisons, key=lambda c: c.rank)
            return ArcCandidateListResponse(
                project_id=payload.project_id,
                items=[c.candidate for c in ranked_candidates],
                meta={"comparison_count": str(len(comparisons))},
            )
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/arcs/selections", response_model=ArcSelection, status_code=201)
    def select_arc_candidate_endpoint(payload: ArcSelectionCreateRequest) -> ArcSelection:
        """Select an arc candidate, rejecting the others."""
        try:
            selected_arc: ArcCandidate | str = payload.selected_arc
            if isinstance(selected_arc, ArcCandidateCreateRequest):
                selected_arc = ArcCandidate(
                    arc_id=selected_arc.arc_id,
                    project_id=selected_arc.project_id,
                    name=selected_arc.name,
                    summary=selected_arc.summary,
                    stage_map_notes=selected_arc.stage_map_notes,
                    fit_notes=selected_arc.fit_notes,
                    tags=selected_arc.tags,
                )
            rejected_ids = list(payload.rejected_arc_ids) if payload.rejected_arc_ids else None
            comparison_notes = list(payload.comparison_notes) if payload.comparison_notes else None
            stage_map = None
            if payload.stage_map:
                stage_map = ArcStageMap(
                    arc_id=payload.stage_map.arc_id,
                    stage_kinds=payload.stage_map.stage_kinds,
                    notes=payload.stage_map.notes,
                )
            selection = story_knowledge_service.select_arc_candidate(
                project_id=payload.project_id,
                selected_arc=selected_arc,
                rejected_arc_ids=rejected_ids,
                comparison_notes=comparison_notes,
                stage_map=stage_map,
            )
            return selection
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/arcs/selections/{selection_id}", response_model=ArcSelection)
    def update_arc_selection(
        selection_id: str,
        project_id: str,
        payload: ArcSelectionUpdateRequest,
    ) -> ArcSelection:
        """Update an arc selection's notes or stage map."""
        try:
            selection = story_knowledge_service.get_arc_selection(project_id, selection_id)
            if selection is None:
                raise StoryKnowledgeNotFoundError(selection_id)
            if payload.stage_map is not None:
                story_knowledge_service.update_arc_stage_map(
                    project_id=project_id,
                    arc_id=payload.stage_map.arc_id,
                    stage_kinds=payload.stage_map.stage_kinds,
                    notes=payload.stage_map.notes,
                )
            comparison_notes = payload.comparison_notes if payload.comparison_notes is not None else list(selection.comparison_notes)
            updated = story_knowledge_service._update_selection_notes(
                project_id,
                selection_id,
                comparison_notes,
            )
            return updated
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Arc selection not found.") from exc
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/arcs/selections/{selection_id}", status_code=200)
    def delete_arc_selection(selection_id: str, project_id: str) -> dict[str, str]:
        """Remove an arc selection."""
        try:
            story_knowledge_service.delete_arc_selection(project_id, selection_id)
            return {"status": "deleted", "selection_id": selection_id}
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Arc selection not found.") from exc

    @router.post("/arcs/stage-maps", response_model=ArcStageMap, status_code=201)
    def create_arc_stage_map(project_id: str, payload: ArcStageMapCreateRequest) -> ArcStageMap:
        """Create or update a stage map for an arc candidate."""
        try:
            stage_map = story_knowledge_service.update_arc_stage_map(
                project_id=project_id,
                arc_id=payload.arc_id,
                stage_kinds=payload.stage_kinds,
                notes=payload.notes,
            )
            return stage_map
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Arc candidate not found for stage map.") from exc
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
