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
                "Polish API Test Project",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


def _build_client(tmp_path: Path) -> tuple[TestClient, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "polish-api"
    _seed_project(db_path, project_id)
    repository = StoryDevelopmentRepository(db_path)
    app = FastAPI()
    app.include_router(build_story_development_router(repository))
    return TestClient(app), repository


# --- Analyze Tests ---


def test_analyze_document_returns_metrics(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/polish/analyze",
        json={
            "project_id": "polish-api",
            "document_id": "doc-1",
            "text": "The quick brown fox jumps over the lazy dog. The dog barked loudly.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["word_count"] > 0
    assert data["sentence_count"] > 0
    assert data["avg_sentence_length"] > 0
    assert "readability_score" in data


def test_analyze_document_returns_report_id(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/polish/analyze",
        json={
            "project_id": "polish-api",
            "document_id": "doc-2",
            "text": "Some text here.",
        },
    )
    assert response.status_code == 200
    assert "report_id" in response.json()


# --- Reports Tests ---


def test_list_reports_returns_empty(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.get(
        "/story-development/polish/reports",
        params={"project_id": "polish-api"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_list_reports_filters_by_document_id(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    client.post(
        "/story-development/polish/analyze",
        json={
            "project_id": "polish-api",
            "document_id": "doc-a",
            "text": "Document A text.",
        },
    )
    client.post(
        "/story-development/polish/analyze",
        json={
            "project_id": "polish-api",
            "document_id": "doc-b",
            "text": "Document B text.",
        },
    )
    response = client.get(
        "/story-development/polish/reports",
        params={"project_id": "polish-api", "document_id": "doc-a"},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


# --- Export Tests ---


def test_export_manuscript_returns_202(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/polish/export",
        json={
            "project_id": "polish-api",
            "document_id": "doc-1",
            "format": "pdf",
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert "export_id" in data
    assert data["format"] == "pdf"


def test_export_manuscript_default_format(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/polish/export",
        json={
            "project_id": "polish-api",
            "document_id": "doc-1",
            "format": "markdown",
        },
    )
    assert response.status_code == 202
    assert response.json()["format"] == "markdown"


def test_get_export_status_returns_status(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    export_resp = client.post(
        "/story-development/polish/export",
        json={
            "project_id": "polish-api",
            "document_id": "doc-1",
            "format": "docx",
        },
    )
    export_id = export_resp.json()["export_id"]
    response = client.get(
        f"/story-development/polish/export/{export_id}",
        params={"project_id": "polish-api"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["export_id"] == export_id
    assert data["status"] in ("queued", "running", "completed", "failed")


def test_get_export_status_not_found_returns_404(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.get(
        "/story-development/polish/export/nonexistent",
        params={"project_id": "polish-api"},
    )
    assert response.status_code == 404


def test_export_with_options(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/polish/export",
        json={
            "project_id": "polish-api",
            "document_id": "doc-1",
            "format": "epub",
            "include_frontmatter": True,
            "include_toc": True,
            "stylesheet": "custom.css",
        },
    )
    assert response.status_code == 202
