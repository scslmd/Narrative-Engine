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
    project_id = "review-trigger-1"
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
# test_trigger_review_returns_202_with_findings
# ---------------------------------------------------------------------------

def test_trigger_review_returns_202_with_findings(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)
    _seed_manuscript(
        repository, project_id, "doc-1",
        content=(
            "Elara walked forward.\n"
            "Elara walked forward.\n"
            "Elara walked forward."
        ),
    )

    response = client.post(
        f"/story-development/drafting/manuscript-documents/doc-1/review",
        params={"project_id": project_id},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["document_id"] == "doc-1"
    assert data["project_id"] == project_id
    assert len(data["findings"]) >= 1
    assert data["findings"][0]["target_document_id"] == "doc-1"


# ---------------------------------------------------------------------------
# test_trigger_review_returns_202_with_empty_findings
# ---------------------------------------------------------------------------

def test_trigger_review_returns_202_with_empty_findings(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)
    _seed_manuscript(
        repository, project_id, "doc-1",
        content="The morning sun rose over the valley. Elara stood at the edge of the ancient forest.",
    )

    response = client.post(
        f"/story-development/drafting/manuscript-documents/doc-1/review",
        params={"project_id": project_id},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["document_id"] == "doc-1"
    assert data["findings"] == []


# ---------------------------------------------------------------------------
# test_trigger_review_creates_suggestion_records_in_db
# ---------------------------------------------------------------------------

def test_trigger_review_creates_suggestion_records_in_db(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)
    _seed_manuscript(
        repository, project_id, "doc-1",
        content=(
            "Elara walked forward.\n"
            "Elara walked forward.\n"
            "Elara walked forward."
        ),
    )

    response = client.post(
        f"/story-development/drafting/manuscript-documents/doc-1/review",
        params={"project_id": project_id},
    )
    assert response.status_code == 202

    db_suggestions = repository.list_revision_suggestions_for_document(
        project_id, target_document_id="doc-1"
    )
    assert len(db_suggestions) >= 1


# ---------------------------------------------------------------------------
# test_trigger_review_returns_404_for_missing_document
# ---------------------------------------------------------------------------

def test_trigger_review_returns_404_for_missing_document(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)

    response = client.post(
        f"/story-development/drafting/manuscript-documents/nonexistent/review",
        params={"project_id": project_id},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# test_trigger_review_returns_404_for_wrong_project
# ---------------------------------------------------------------------------

def test_trigger_review_returns_404_for_wrong_project(tmp_path: Path) -> None:
    client, repository, project_id = _build_client(tmp_path)
    _seed_manuscript(repository, project_id, "doc-1", content="Some content")

    response = client.post(
        f"/story-development/drafting/manuscript-documents/doc-1/review",
        params={"project_id": "wrong-project"},
    )
    assert response.status_code == 404
