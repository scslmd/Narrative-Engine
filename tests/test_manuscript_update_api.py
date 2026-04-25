from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from starlette.testclient import TestClient
import pytest

from app.api.story_development import build_story_development_router
from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import StorySuggestionLifecycleState
from app.services.drafting import DraftingService
from fastapi import FastAPI

pytestmark = pytest.mark.integration


_STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)


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
                f"Project {project_id}",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                _STAMP.isoformat(),
                _STAMP.isoformat(),
            ),
        )
        connection.commit()


def _build_client(tmp_path: Path) -> tuple[TestClient, StoryDevelopmentRepository, str]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "patch-manuscript-1"
    _seed_project(db_path, project_id)
    repository = StoryDevelopmentRepository(db_path)
    app = FastAPI()
    app.include_router(build_story_development_router(repository))
    return TestClient(app), repository, project_id


def _seed_manuscript(repository: StoryDevelopmentRepository, project_id: str, document_id: str, content: str, title: str = "Test Chapter") -> None:
    drafting = DraftingService(repository)
    drafting.save_manuscript_document(
        project_id,
        document_id=document_id,
        content=content,
        title=title,
    )


# ---------------------------------------------------------------------------
# test_update_manuscript_content_updates_and_returns_document
# ---------------------------------------------------------------------------

def test_update_manuscript_content_updates_and_returns_document(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)
    _seed_manuscript(repository, project_id, "doc-1", content="Original content", title="Test Chapter")

    response = client.patch(
        f"/story-development/drafting/manuscript-documents/doc-1",
        params={"project_id": project_id},
        json={"content": "Updated content"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated content"
    assert data["document_id"] == "doc-1"
    assert data["title"] == "Test Chapter"


# ---------------------------------------------------------------------------
# test_update_manuscript_increment_version
# ---------------------------------------------------------------------------

def test_update_manuscript_increment_version(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)
    _seed_manuscript(repository, project_id, "doc-1", content="Original content", title="Test Chapter")

    first = client.patch(
        f"/story-development/drafting/manuscript-documents/doc-1",
        params={"project_id": project_id},
        json={"content": "First update"},
    )
    assert first.status_code == 200
    v1 = first.json()["version"]

    second = client.patch(
        f"/story-development/drafting/manuscript-documents/doc-1",
        params={"project_id": project_id},
        json={"content": "Second update"},
    )
    assert second.status_code == 200
    v2 = second.json()["version"]
    assert v2 == v1 + 1


# ---------------------------------------------------------------------------
# test_update_manuscript_partial_title_only
# ---------------------------------------------------------------------------

def test_update_manuscript_partial_title_only(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)
    _seed_manuscript(repository, project_id, "doc-1", content="Original content", title="Test Chapter")

    response = client.patch(
        f"/story-development/drafting/manuscript-documents/doc-1",
        params={"project_id": project_id},
        json={"title": "New Title"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["content"] == "Original content"


# ---------------------------------------------------------------------------
# test_update_manuscript_partial_content_only
# ---------------------------------------------------------------------------

def test_update_manuscript_partial_content_only(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)
    _seed_manuscript(repository, project_id, "doc-1", content="Original content", title="Test Chapter")

    response = client.patch(
        f"/story-development/drafting/manuscript-documents/doc-1",
        params={"project_id": project_id},
        json={"content": "Brand new content here"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Brand new content here"
    assert data["title"] == "Test Chapter"


# ---------------------------------------------------------------------------
# test_update_manuscript_returns_400_when_no_fields_provided
# ---------------------------------------------------------------------------

def test_update_manuscript_returns_400_when_no_fields_provided(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)
    _seed_manuscript(repository, project_id, "doc-1", content="Original content", title="Test Chapter")

    response = client.patch(
        f"/story-development/drafting/manuscript-documents/doc-1",
        params={"project_id": project_id},
        json={},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# test_update_manuscript_returns_404_for_missing_document
# ---------------------------------------------------------------------------

def test_update_manuscript_returns_404_for_missing_document(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)

    response = client.patch(
        f"/story-development/drafting/manuscript-documents/nonexistent",
        params={"project_id": project_id},
        json={"content": "Some content"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# test_update_manuscript_returns_404_for_wrong_project
# ---------------------------------------------------------------------------

def test_update_manuscript_returns_404_for_wrong_project(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)
    _seed_manuscript(repository, project_id, "doc-1", content="Original content", title="Test Chapter")

    response = client.patch(
        f"/story-development/drafting/manuscript-documents/doc-1",
        params={"project_id": "wrong-project"},
        json={"content": "Some content"},
    )
    assert response.status_code == 404
