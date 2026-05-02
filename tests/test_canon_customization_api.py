from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.canon_customization import build_canon_customization_router
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.projects import ProjectCreateRequest
from app.services.projects import ProjectService


def _build_client(tmp_path) -> TestClient:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
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
    app = FastAPI()
    app.include_router(build_canon_customization_router(repository))
    return TestClient(app)


def test_canon_annotation_and_profile_endpoints(tmp_path) -> None:
    client = _build_client(tmp_path)

    create_annotation = client.post(
        "/v1/canon/annotations",
        json={
            "project_id": "project-1",
            "target_kind": "character",
            "target_id": "char-1",
            "field_path": "voice_notes",
            "annotation_kind": "locked",
            "note": "Keep voice stable.",
            "applies_to_modes": ["same_project_side_story"],
        },
    )
    assert create_annotation.status_code == 201
    annotation_id = create_annotation.json()["annotation_id"]

    list_annotations = client.get("/v1/canon/annotations", params={"project_id": "project-1"})
    assert list_annotations.status_code == 200
    assert len(list_annotations.json()) == 1

    create_profile = client.post(
        "/v1/canon/profiles",
        json={
            "project_id": "project-1",
            "name": "default profile",
            "canon_scope": {
                "source_project_id": "project-1",
                "scope_mode": "selected",
                "character_ids": ["char-1"],
            },
            "selected_annotation_ids": [annotation_id],
        },
    )
    assert create_profile.status_code == 201
    profile_id = create_profile.json()["profile_id"]

    preview = client.post(
        f"/v1/canon/profiles/{profile_id}/packet-preview",
        params={"project_id": "project-1"},
    )
    assert preview.status_code == 200
    assert preview.json()["customization_profile_id"] == profile_id

    delete_annotation = client.delete(
        f"/v1/canon/annotations/{annotation_id}",
        params={"project_id": "project-1"},
    )
    assert delete_annotation.status_code == 200
