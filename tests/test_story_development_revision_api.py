from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api import build_story_development_router
from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository

pytestmark = pytest.mark.integration

STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)


def _seed_project(db_path: Path, project_id: str) -> None:
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                "Revision API Test Project",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


def _build_client(tmp_path: Path) -> tuple[TestClient, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "revision-api"
    _seed_project(db_path, project_id)
    repository = StoryDevelopmentRepository(db_path)
    app = FastAPI()
    app.include_router(build_story_development_router(repository))
    return TestClient(app), repository


# --- List Tests ---


def test_list_revision_passes_returns_empty(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.get("/story-development/revision/passes", params={"project_id": "revision-api"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_list_revision_passes_filters_by_pass_type(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    client.post(
        "/story-development/revision/passes",
        json={"project_id": "revision-api", "pass_type": "structural"},
    )
    client.post(
        "/story-development/revision/passes",
        json={"project_id": "revision-api", "pass_type": "character"},
    )
    response = client.get(
        "/story-development/revision/passes",
        params={"project_id": "revision-api", "pass_type": "structural"},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_list_revision_passes_filters_by_status(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    client.post(
        "/story-development/revision/passes",
        json={"project_id": "revision-api", "pass_type": "structural", "status": "pending"},
    )
    client.post(
        "/story-development/revision/passes",
        json={"project_id": "revision-api", "pass_type": "structural", "status": "in_progress"},
    )
    response = client.get(
        "/story-development/revision/passes",
        params={"project_id": "revision-api", "status": "pending"},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


# --- Create Tests ---


def test_create_revision_pass_returns_201(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/revision/passes",
        json={"project_id": "revision-api", "pass_type": "structural"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["pass_type"] == "structural"
    assert data["status"] == "pending"
    assert "pass_id" in data
    assert data["project_id"] == "revision-api"


def test_create_revision_pass_includes_default_checklist(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/revision/passes",
        json={"project_id": "revision-api", "pass_type": "structural"},
    )
    assert response.status_code == 201
    assert len(response.json()["checklist"]) > 0


# --- Get Tests ---


def test_get_revision_pass_returns_200(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    create_resp = client.post(
        "/story-development/revision/passes",
        json={"project_id": "revision-api", "pass_type": "character"},
    )
    pass_id = create_resp.json()["pass_id"]
    response = client.get(
        f"/story-development/revision/passes/{pass_id}",
        params={"project_id": "revision-api"},
    )
    assert response.status_code == 200
    assert response.json()["pass_type"] == "character"


def test_get_revision_pass_not_found_returns_404(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.get(
        "/story-development/revision/passes/nonexistent",
        params={"project_id": "revision-api"},
    )
    assert response.status_code == 404


# --- Update Tests ---


def test_update_revision_pass_returns_200(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    create_resp = client.post(
        "/story-development/revision/passes",
        json={"project_id": "revision-api", "pass_type": "line_edit"},
    )
    pass_id = create_resp.json()["pass_id"]
    response = client.patch(
        f"/story-development/revision/passes/{pass_id}",
        params={"project_id": "revision-api"},
        json={"notes": "Updated notes"},
    )
    assert response.status_code == 200
    assert response.json()["notes"] == "Updated notes"


def test_update_revision_pass_not_found_returns_404(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.patch(
        "/story-development/revision/passes/nonexistent",
        params={"project_id": "revision-api"},
        json={"notes": "Updated"},
    )
    assert response.status_code == 404


# --- Complete Tests ---


def test_complete_revision_pass(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    create_resp = client.post(
        "/story-development/revision/passes",
        json={"project_id": "revision-api", "pass_type": "copy_edit"},
    )
    pass_id = create_resp.json()["pass_id"]
    response = client.post(
        f"/story-development/revision/passes/{pass_id}/complete",
        params={"project_id": "revision-api"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["completed_at"] is not None


def test_complete_revision_pass_not_found_returns_404(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/revision/passes/nonexistent/complete",
        params={"project_id": "revision-api"},
    )
    assert response.status_code == 404


# --- Checklist Tests ---


def test_get_checklist_returns_items(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.get("/story-development/revision/checklists/structural")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("item_id" in item for item in data)


def test_checklist_mutation_after_completion_returns_409(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    create_resp = client.post(
        "/story-development/revision/passes",
        json={"project_id": "revision-api", "pass_type": "structural"},
    )
    pass_id = create_resp.json()["pass_id"]
    client.post(
        f"/story-development/revision/passes/{pass_id}/complete",
        params={"project_id": "revision-api"},
    )
    response = client.patch(
        f"/story-development/revision/passes/{pass_id}",
        params={"project_id": "revision-api"},
        json={
            "checklist": [
                {"item_id": "structure-1", "label": "Check plot structure", "done": True},
                {"item_id": "structure-2", "label": "Verify pacing", "done": False},
                {"item_id": "structure-3", "label": "Review scene transitions", "done": False},
            ]
        },
    )
    assert response.status_code == 409
