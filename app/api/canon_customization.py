from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.canon_customization import (
    CanonAnnotation,
    CanonAnnotationCreateRequest,
    CanonCustomizationProfile,
    CanonCustomizationProfileCreateRequest,
    CanonCustomizationProfileUpdateRequest,
)
from app.schemas.generation import CanonGenerationPacket
from app.services.canon_customization import CanonCustomizationService


def build_canon_customization_router(
    repository: StoryDevelopmentRepository,
    prefix: str = "/v1/canon",
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["canon-customization"])
    service = CanonCustomizationService(repository)

    @router.get("/annotations", response_model=list[CanonAnnotation])
    def list_annotations(
        project_id: str = Query(..., min_length=1),
        target_kind: str | None = Query(default=None),
        target_id: str | None = Query(default=None),
    ) -> list[CanonAnnotation]:
        return service.list_annotations(project_id, target_kind, target_id)

    @router.post("/annotations", response_model=CanonAnnotation, status_code=201)
    def create_annotation(payload: CanonAnnotationCreateRequest) -> CanonAnnotation:
        return service.save_annotation(payload)

    @router.delete("/annotations/{annotation_id}", status_code=200)
    def delete_annotation(annotation_id: str, project_id: str = Query(..., min_length=1)) -> dict[str, str]:
        try:
            service.delete_annotation(project_id, annotation_id)
            return {"status": "deleted", "annotation_id": annotation_id}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="annotation not found") from exc

    @router.get("/profiles", response_model=list[CanonCustomizationProfile])
    def list_profiles(project_id: str = Query(..., min_length=1)) -> list[CanonCustomizationProfile]:
        return service.list_profiles(project_id)

    @router.post("/profiles", response_model=CanonCustomizationProfile, status_code=201)
    def create_profile(payload: CanonCustomizationProfileCreateRequest) -> CanonCustomizationProfile:
        return service.create_profile(payload)

    @router.patch("/profiles/{profile_id}", response_model=CanonCustomizationProfile)
    def update_profile(
        profile_id: str,
        payload: CanonCustomizationProfileUpdateRequest,
        project_id: str = Query(..., min_length=1),
    ) -> CanonCustomizationProfile:
        try:
            return service.update_profile(profile_id, project_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="profile not found") from exc

    @router.delete("/profiles/{profile_id}", status_code=200)
    def delete_profile(profile_id: str, project_id: str = Query(..., min_length=1)) -> dict[str, str]:
        try:
            service.delete_profile(project_id, profile_id)
            return {"status": "deleted", "profile_id": profile_id}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="profile not found") from exc

    @router.post("/profiles/{profile_id}/packet-preview", response_model=CanonGenerationPacket)
    def packet_preview(profile_id: str, project_id: str = Query(..., min_length=1)) -> CanonGenerationPacket:
        try:
            return service.preview_packet(project_id, profile_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="profile not found") from exc

    return router
