"""Integration tests for review routing POST endpoints (inspect links)."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.story_development import build_story_development_router
from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository

pytestmark = pytest.mark.integration


def _build_client(tmp_path: Path, project_id: str) -> tuple[TestClient, str, Path]:
    db_path = tmp_path / "data" / "state" / "review_ops.db"
    db_path = ensure_operations_db(db_path)
    repository = StoryDevelopmentRepository(db_path)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, "Test Project Review", str(db_path), str(db_path), "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        conn.commit()
    app = FastAPI()
    app.include_router(build_story_development_router(repository))
    return TestClient(app), project_id, db_path


class TestInspectLinkEndpoints:
    """Test inspect link POST endpoints via API."""

    def test_create_inspect_link_returns_201(self, tmp_path: Path) -> None:
        """Creating an inspect link should return 201 Created."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, project_id, _ = _build_client(tmp_path, project_id)
        link_id = f"link-{uuid4().hex[:8]}"

        response = client.post(
            "/story-development/review/inspect-links",
            json={
                "project_id": project_id,
                "link_id": link_id,
                "object_kind": "job",
                "object_id": "job-123",
                "logical_run_id": "run-456",
                "run_id": "run-456",
                "run_kind": "job",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["link_id"] == link_id
        assert data["object_kind"] == "job"
        assert data["object_id"] == "job-123"
        assert data["logical_run_id"] == "run-456"
        assert data["run_kind"] == "job"

    def test_create_inspect_link_validates_required_fields(self, tmp_path: Path) -> None:
        """Creating an inspect link without required fields should return 422."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)
        response = client.post(
            "/story-development/review/inspect-links",
            json={
                "project_id": project_id,
            },
        )
        assert response.status_code == 422

    def test_create_inspect_link_with_optional_fields(self, tmp_path: Path) -> None:
        """Creating an inspect link with optional fields."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, project_id, _ = _build_client(tmp_path, project_id)
        link_id = f"link-{uuid4().hex[:8]}"

        response = client.post(
            "/story-development/review/inspect-links",
            json={
                "project_id": project_id,
                "link_id": link_id,
                "object_kind": "checker",
                "object_id": "checker-789",
                "logical_run_id": "checker-run",
                "run_id": "checker-run",
                "run_kind": "checker",
                "attempt_number": 2,
                "label": "Architect role check",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["link_id"] == link_id
        assert data["attempt_number"] == 2
        assert data["label"] == "Architect role check"

    def test_create_inspect_link_from_job(self, tmp_path: Path) -> None:
        """Creating an inspect link pointing to a job run."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, project_id, _ = _build_client(tmp_path, project_id)

        job_id = f"job-{uuid4().hex[:8]}"
        response = client.post(
            "/story-development/review/inspect-links",
            json={
                "project_id": project_id,
                "link_id": f"link-{uuid4().hex[:8]}",
                "object_kind": "job",
                "object_id": job_id,
                "logical_run_id": job_id,
                "run_id": job_id,
                "run_kind": "job",
                "label": "P-100 architect phase",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["object_id"] == job_id
        assert data["run_kind"] == "job"

    def test_create_inspect_link_from_checker(self, tmp_path: Path) -> None:
        """Creating an inspect link pointing to a checker run."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, project_id, _ = _build_client(tmp_path, project_id)

        run_id = f"run-{uuid4().hex[:8]}"
        response = client.post(
            "/story-development/review/inspect-links",
            json={
                "project_id": project_id,
                "link_id": f"link-{uuid4().hex[:8]}",
                "object_kind": "checker",
                "object_id": run_id,
                "logical_run_id": run_id,
                "run_id": run_id,
                "run_kind": "checker",
                "label": "Critic role validation",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["object_id"] == run_id
        assert data["run_kind"] == "checker"

    def test_create_inspect_link_with_manuscript_object(self, tmp_path: Path) -> None:
        """Creating an inspect link pointing to a manuscript document."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, project_id, _ = _build_client(tmp_path, project_id)

        doc_id = f"doc-{uuid4().hex[:8]}"
        response = client.post(
            "/story-development/review/inspect-links",
            json={
                "project_id": project_id,
                "link_id": f"link-{uuid4().hex[:8]}",
                "object_kind": "manuscript",
                "object_id": doc_id,
                "logical_run_id": "review-run",
                "run_id": "review-run",
                "run_kind": "job",
                "label": "Manuscript consistency check",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["object_kind"] == "manuscript"
        assert data["object_id"] == doc_id

    def test_create_inspect_link_rejects_invalid_pattern(self, tmp_path: Path) -> None:
        """Creating an inspect link with invalid ID pattern should return 422."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, project_id, _ = _build_client(tmp_path, project_id)
        response = client.post(
            "/story-development/review/inspect-links",
            json={
                "project_id": project_id,
                "link_id": "link with spaces",
                "object_kind": "job",
                "object_id": "obj-1",
                "logical_run_id": "run-1",
                "run_id": "run-1",
                "run_kind": "job",
            },
        )
        assert response.status_code == 422

    def test_list_inspect_links_after_creation(self, tmp_path: Path) -> None:
        """Listing inspect links after creation should include the new link."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, project_id, _ = _build_client(tmp_path, project_id)
        link_ids = []

        for i in range(3):
            link_id = f"link-{uuid4().hex[:8]}"
            link_ids.append(link_id)
            client.post(
                "/story-development/review/inspect-links",
                json={
                    "project_id": project_id,
                    "link_id": link_id,
                    "object_kind": "job",
                    "object_id": f"job-{i}",
                    "logical_run_id": f"run-{i}",
                    "run_id": f"run-{i}",
                    "run_kind": "job",
                },
            )

        response = client.get(
            "/story-development/review/inspect-links",
            params={"project_id": project_id},
        )
        assert response.status_code == 200
        data = response.json()
        found_ids = {item["link_id"] for item in data["items"]}
        assert found_ids == set(link_ids)
