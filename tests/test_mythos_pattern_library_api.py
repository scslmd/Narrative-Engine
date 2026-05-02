from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.mythos_library import build_mythos_library_router
from app.api.pattern_library import build_pattern_library_router
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
    app.include_router(build_mythos_library_router(repository))
    app.include_router(build_pattern_library_router(repository))
    return TestClient(app)


def test_mythos_and_pattern_crud_endpoints(tmp_path) -> None:
    client = _build_client(tmp_path)

    mythos_create = client.post(
        "/v1/mythos/entries",
        json={
            "project_id": "project-1",
            "entry_type": "motif",
            "name": "Storm Crown",
        },
    )
    assert mythos_create.status_code == 201
    mythos_id = mythos_create.json()["mythos_id"]

    mythos_list = client.get("/v1/mythos/entries", params={"project_id": "project-1"})
    assert mythos_list.status_code == 200
    assert len(mythos_list.json()) == 1

    mythos_patch = client.patch(
        f"/v1/mythos/entries/{mythos_id}",
        params={"project_id": "project-1"},
        json={"name": "Storm Crown Updated"},
    )
    assert mythos_patch.status_code == 200

    pattern_create = client.post(
        "/v1/patterns/entries",
        json={
            "project_id": "project-1",
            "pattern_type": "plot",
            "name": "Hero Return",
        },
    )
    assert pattern_create.status_code == 201
    pattern_id = pattern_create.json()["pattern_id"]

    pattern_list = client.get("/v1/patterns/entries", params={"project_id": "project-1"})
    assert pattern_list.status_code == 200
    assert len(pattern_list.json()) == 1

    pattern_patch = client.patch(
        f"/v1/patterns/entries/{pattern_id}",
        params={"project_id": "project-1"},
        json={"name": "Hero Return Updated"},
    )
    assert pattern_patch.status_code == 200
