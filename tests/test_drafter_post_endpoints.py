"""Integration tests for drafting POST endpoints (draft artifacts, continuation, alternate variants)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import build_app
from app.persistence.sqlite import connect, ensure_operations_db
from app.settings import settings

_TEST_PROJECT_ID = "test-project-drafting"
_TEST_TIMESTAMP = datetime.now(timezone.utc).isoformat()


def _ensure_test_project() -> Path:
    db_path = settings.operations_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    ensure_operations_db(db_path)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (_TEST_PROJECT_ID, "Test Project Drafting", str(db_path), str(db_path), _TEST_TIMESTAMP, _TEST_TIMESTAMP),
        )
        conn.commit()
    return db_path


class BaseDraftingTest:
    def _make_client(self) -> TestClient:
        _ensure_test_project()
        app = build_app()
        return TestClient(app)


class TestDraftArtifactEndpoints(BaseDraftingTest):
    """Test draft artifact POST endpoints via API."""

    def test_create_draft_artifact_returns_201(self) -> None:
        """Creating a draft artifact should return 201 Created."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        artifact_id = f"draft-{uuid4().hex[:8]}"

        response = client.post(
            "/v1/story-development/drafting/draft-artifacts",
            json={
                "project_id": project_id,
                "artifact_id": artifact_id,
                "title": "Scene Draft 1",
                "content": "The character walks into the room.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["artifact_id"] == artifact_id
        assert data["title"] == "Scene Draft 1"
        assert data["content"] == "The character walks into the room."
        assert data["project_id"] == project_id
        assert data["status"] == "DRAFT"

    def test_create_draft_artifact_validates_required_fields(self) -> None:
        """Creating a draft artifact without required fields should return 422."""
        client = self._make_client()
        response = client.post(
            "/v1/story-development/drafting/draft-artifacts",
            json={
                "project_id": _TEST_PROJECT_ID,
            },
        )
        assert response.status_code == 422

    def test_create_draft_artifact_with_provenance(self) -> None:
        """Creating a draft artifact with source_plan_ids and provenance_note."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        artifact_id = f"draft-{uuid4().hex[:8]}"

        response = client.post(
            "/v1/story-development/drafting/draft-artifacts",
            json={
                "project_id": project_id,
                "artifact_id": artifact_id,
                "title": "Draft With Provenance",
                "content": "Content with provenance.",
                "source_plan_ids": ["plan-1", "plan-2"],
                "source_context": ["context-a"],
                "provenance_note": "Generated from sequence plan.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["artifact_id"] == artifact_id
        assert data["source_plan_ids"] == ["plan-1", "plan-2"]
        assert data["provenance_note"] == "Generated from sequence plan."

    def test_create_draft_artifact_with_status(self) -> None:
        """Creating a draft artifact with PROPOSED status."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        artifact_id = f"draft-{uuid4().hex[:8]}"

        response = client.post(
            "/v1/story-development/drafting/draft-artifacts",
            json={
                "project_id": project_id,
                "artifact_id": artifact_id,
                "title": "Proposed Draft",
                "content": "Proposed content.",
                "status": "PROPOSED",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "PROPOSED"

    def test_continue_draft_from_prior_draft(self) -> None:
        """Continuing a draft from a prior draft artifact."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        # Create base draft
        base_id = f"draft-{uuid4().hex[:8]}"
        client.post(
            "/v1/story-development/drafting/draft-artifacts",
            json={
                "project_id": project_id,
                "artifact_id": base_id,
                "title": "Base Draft",
                "content": "Original content.",
                "source_plan_ids": ["plan-base"],
            },
        )

        # Continue from base draft
        continuation_id = f"draft-{uuid4().hex[:8]}"
        response = client.post(
            "/v1/story-development/drafting/draft-artifacts/continue",
            json={
                "project_id": project_id,
                "artifact_id": continuation_id,
                "title": "Continued Draft",
                "content": "Extended content.",
                "prior_draft_artifact_id": base_id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["artifact_id"] == continuation_id
        assert "draft:" + base_id in data["source_context"]
        assert "plan-base" in data["source_plan_ids"]

    def test_continue_draft_from_manuscript_document(self) -> None:
        """Continuing a draft from a manuscript document."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        # Create manuscript document
        doc_id = f"doc-{uuid4().hex[:8]}"
        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "Manuscript content.",
            },
        )

        # Continue from manuscript
        continuation_id = f"draft-{uuid4().hex[:8]}"
        response = client.post(
            "/v1/story-development/drafting/draft-artifacts/continue",
            json={
                "project_id": project_id,
                "artifact_id": continuation_id,
                "title": "Draft from Manuscript",
                "content": "Draft continuation.",
                "prior_manuscript_document_id": doc_id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["artifact_id"] == continuation_id
        assert "manuscript:" + doc_id in data["source_context"]

    def test_continue_draft_requires_one_source(self) -> None:
        """Continuing a draft without a source should return 400."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.post(
            "/v1/story-development/drafting/draft-artifacts/continue",
            json={
                "project_id": project_id,
                "artifact_id": "draft-new",
                "title": "No source draft",
                "content": "Content without source.",
            },
        )
        assert response.status_code == 400

    def test_continue_draft_invalidates_both_sources(self) -> None:
        """Continuing a draft with both sources should return 400."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.post(
            "/v1/story-development/drafting/draft-artifacts/continue",
            json={
                "project_id": project_id,
                "artifact_id": "draft-new",
                "title": "Both sources",
                "content": "Content.",
                "prior_draft_artifact_id": "draft-x",
                "prior_manuscript_document_id": "doc-y",
            },
        )
        assert response.status_code == 400

    def test_alternate_variant_from_draft(self) -> None:
        """Creating an alternate variant from a draft artifact."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        # Create base draft
        base_id = f"draft-{uuid4().hex[:8]}"
        client.post(
            "/v1/story-development/drafting/draft-artifacts",
            json={
                "project_id": project_id,
                "artifact_id": base_id,
                "title": "Base Draft",
                "content": "Original.",
                "source_plan_ids": ["plan-base"],
            },
        )

        # Create alternate variant
        variant_id = f"draft-{uuid4().hex[:8]}"
        response = client.post(
            "/v1/story-development/drafting/draft-artifacts/alternate-variant",
            json={
                "project_id": project_id,
                "artifact_id": variant_id,
                "title": "Alternate Draft",
                "content": "Alternative content.",
                "base_draft_artifact_id": base_id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["artifact_id"] == variant_id
        assert data["status"] == "PROPOSED"
        assert "draft:" + base_id in data["source_context"]
        assert "plan-base" in data["source_plan_ids"]

    def test_alternate_variant_from_manuscript(self) -> None:
        """Creating an alternate variant from a manuscript document."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        # Create manuscript
        doc_id = f"doc-{uuid4().hex[:8]}"
        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter",
                "content": "Content.",
            },
        )

        # Create alternate variant
        variant_id = f"draft-{uuid4().hex[:8]}"
        response = client.post(
            "/v1/story-development/drafting/draft-artifacts/alternate-variant",
            json={
                "project_id": project_id,
                "artifact_id": variant_id,
                "title": "Variant from Manuscript",
                "content": "Variant content.",
                "base_manuscript_document_id": doc_id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["artifact_id"] == variant_id
        assert data["status"] == "PROPOSED"
        assert "manuscript:" + doc_id in data["source_context"]

    def test_alternate_variant_requires_one_source(self) -> None:
        """Creating an alternate variant without a source should return 400."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.post(
            "/v1/story-development/drafting/draft-artifacts/alternate-variant",
            json={
                "project_id": project_id,
                "artifact_id": "draft-variant",
                "title": "No source variant",
                "content": "Content.",
            },
        )
        assert response.status_code == 400

    def test_alternate_variant_invalidates_both_sources(self) -> None:
        """Creating an alternate variant with both sources should return 400."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.post(
            "/v1/story-development/drafting/draft-artifacts/alternate-variant",
            json={
                "project_id": project_id,
                "artifact_id": "draft-variant",
                "title": "Both sources",
                "content": "Content.",
                "base_draft_artifact_id": "draft-x",
                "base_manuscript_document_id": "doc-y",
            },
        )
        assert response.status_code == 400

    def test_alternate_variant_base_not_found(self) -> None:
        """Creating an alternate variant with non-existent base should return 404."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.post(
            "/v1/story-development/drafting/draft-artifacts/alternate-variant",
            json={
                "project_id": project_id,
                "artifact_id": "draft-variant",
                "title": "Non-existent base",
                "content": "Content.",
                "base_draft_artifact_id": "non-existent-draft",
            },
        )
        assert response.status_code == 404

    def test_continue_draft_prior_not_found(self) -> None:
        """Continuing a draft with non-existent prior source should return 404."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.post(
            "/v1/story-development/drafting/draft-artifacts/continue",
            json={
                "project_id": project_id,
                "artifact_id": "draft-continue",
                "title": "Non-existent prior",
                "content": "Content.",
                "prior_draft_artifact_id": "non-existent-draft",
            },
        )
        assert response.status_code == 404
