from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.mythos_library import MythosEntry, MythosEntryCreateRequest, MythosEntryUpdateRequest
from app.services.mythos_library import MythosLibraryService


def build_mythos_library_router(
    repository: StoryDevelopmentRepository,
    prefix: str = "/v1/mythos",
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["mythos-library"])
    service = MythosLibraryService(repository)

    @router.get("/entries", response_model=list[MythosEntry])
    def list_entries(project_id: str = Query(..., min_length=1), entry_type: str | None = Query(default=None)) -> list[MythosEntry]:
        return service.list_entries(project_id, entry_type)

    @router.post("/entries", response_model=MythosEntry, status_code=201)
    def create_entry(payload: MythosEntryCreateRequest) -> MythosEntry:
        return service.create_entry(payload)

    @router.patch("/entries/{mythos_id}", response_model=MythosEntry)
    def update_entry(
        mythos_id: str,
        payload: MythosEntryUpdateRequest,
        project_id: str = Query(..., min_length=1),
    ) -> MythosEntry:
        try:
            return service.update_entry(mythos_id, project_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="mythos entry not found") from exc

    @router.delete("/entries/{mythos_id}", status_code=200)
    def delete_entry(mythos_id: str, project_id: str = Query(..., min_length=1)) -> dict[str, str]:
        try:
            service.delete_entry(project_id, mythos_id)
            return {"status": "deleted", "mythos_id": mythos_id}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="mythos entry not found") from exc

    @router.post("/materialize-extraction", response_model=list[MythosEntry])
    def materialize_extraction(project_id: str, extraction_id: str) -> list[MythosEntry]:
        return service.materialize_extraction(project_id, extraction_id)

    return router
