from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.pattern_library import PatternEntry, PatternEntryCreateRequest, PatternEntryUpdateRequest
from app.services.pattern_library import PatternLibraryService


def build_pattern_library_router(
    repository: StoryDevelopmentRepository,
    prefix: str = "/v1/patterns",
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["pattern-library"])
    service = PatternLibraryService(repository)

    @router.get("/entries", response_model=list[PatternEntry])
    def list_entries(
        project_id: str = Query(..., min_length=1),
        pattern_type: str | None = Query(default=None),
    ) -> list[PatternEntry]:
        return service.list_entries(project_id, pattern_type)

    @router.post("/entries", response_model=PatternEntry, status_code=201)
    def create_entry(payload: PatternEntryCreateRequest) -> PatternEntry:
        return service.create_entry(payload)

    @router.patch("/entries/{pattern_id}", response_model=PatternEntry)
    def update_entry(
        pattern_id: str,
        payload: PatternEntryUpdateRequest,
        project_id: str = Query(..., min_length=1),
    ) -> PatternEntry:
        try:
            return service.update_entry(pattern_id, project_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="pattern entry not found") from exc

    @router.delete("/entries/{pattern_id}", status_code=200)
    def delete_entry(pattern_id: str, project_id: str = Query(..., min_length=1)) -> dict[str, str]:
        try:
            service.delete_entry(project_id, pattern_id)
            return {"status": "deleted", "pattern_id": pattern_id}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="pattern entry not found") from exc

    @router.post("/materialize-extraction", response_model=list[PatternEntry])
    def materialize_extraction(project_id: str, extraction_id: str) -> list[PatternEntry]:
        return service.materialize_extraction(project_id, extraction_id)

    return router
