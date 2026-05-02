from __future__ import annotations

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.canon_customization import CanonAnnotationCreateRequest, CanonCustomizationProfileCreateRequest
from app.schemas.projects import ProjectCreateRequest
from app.services.canon_customization import CanonCustomizationService
from app.services.projects import ProjectService


def _setup(tmp_path):
    project_service = ProjectService(tmp_path)
    project_service.create_project(
        ProjectCreateRequest(
            project_id="project-1",
            project_name="Project One",
            genre="Fantasy",
            tone_profile="Neutral",
            story_structure="THREE_ACT",
        )
    )
    repository = StoryDevelopmentRepository(tmp_path / "data" / "state" / "narrative_ops.db")
    return repository


def test_canon_customization_service_profile_and_preview(tmp_path) -> None:
    repository = _setup(tmp_path)
    service = CanonCustomizationService(repository)
    annotation = service.save_annotation(
        CanonAnnotationCreateRequest(
            project_id="project-1",
            target_kind="character",
            target_id="char-1",
            field_path="voice_notes",
            annotation_kind="locked",
        )
    )
    profile = service.create_profile(
        CanonCustomizationProfileCreateRequest(
            project_id="project-1",
            name="default",
            canon_scope={
                "source_project_id": "project-1",
                "scope_mode": "selected",
                "character_ids": ["char-1"],
            },
            selected_annotation_ids=[annotation.annotation_id],
        )
    )
    packet = service.preview_packet("project-1", profile.profile_id)
    assert packet.customization_profile_id == profile.profile_id
