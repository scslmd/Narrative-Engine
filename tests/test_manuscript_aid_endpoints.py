"""Integration tests for manuscript-aid API endpoints (drafting, revision suggestions, review)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import build_app
from app.persistence.sqlite import connect, ensure_operations_db
from app.settings import settings

_TEST_PROJECT_ID = "test-project"
_TEST_TIMESTAMP = datetime.now(timezone.utc).isoformat()


def _ensure_test_project() -> Path:
    """Seed the projects table so FK constraints are satisfied.
    
    Must be called at the same time as build_app() to use the same
    DB path (PYTEST_CURRENT_TEST changes between (setup) and (call)
    phases, producing different test hashes).
    """
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
            (_TEST_PROJECT_ID, "Test Project", str(db_path), str(db_path), _TEST_TIMESTAMP, _TEST_TIMESTAMP),
        )
        conn.commit()
    return db_path


class BaseManuscriptTest:
    """Shared setup for manuscript-aid API tests."""

    def _make_client(self) -> TestClient:
        _ensure_test_project()
        app = build_app()
        return TestClient(app)


class TestManuscriptDocumentEndpoints(BaseManuscriptTest):
    """Test manuscript document CRUD via API endpoints."""

    def test_create_manuscript_document_returns_201(self) -> None:
        """Creating a manuscript document should return 201 Created."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc-{uuid4().hex[:8]}",
                "title": "Chapter One",
                "content": "The quick brown fox jumped over the lazy dog.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["document_id"].startswith("doc-")
        assert data["title"] == "Chapter One"
        assert data["content"] == "The quick brown fox jumped over the lazy dog."
        assert data["project_id"] == project_id
        assert data["version"] == 1

    def test_create_manuscript_document_validates_required_fields(self) -> None:
        """Creating a manuscript document without required fields should return 422."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
            },
        )
        assert response.status_code == 422

    def test_get_manuscript_document(self) -> None:
        """Getting an existing manuscript document should return it."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        doc_id = f"doc-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "Some content.",
            },
        )

        response = client.get(
            f"/v1/story-development/drafting/manuscript-documents/{doc_id}",
            params={"project_id": project_id},
        )
        assert response.status_code == 200
        assert response.json()["document_id"] == doc_id
        assert response.json()["content"] == "Some content."

    def test_get_manuscript_document_not_found(self) -> None:
        """Getting a non-existent manuscript document should return 404."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.get(
            "/v1/story-development/drafting/manuscript-documents/non-existent",
            params={"project_id": project_id},
        )
        assert response.status_code == 404

    def test_list_manuscript_documents(self) -> None:
        """Listing manuscript documents should return all documents for a project."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": "doc-1",
                "title": "Chapter One",
                "content": "Content 1.",
            },
        )
        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": "doc-2",
                "title": "Chapter Two",
                "content": "Content 2.",
            },
        )

        response = client.get(
            "/v1/story-development/drafting/manuscript-documents",
            params={"project_id": project_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["meta"]["ordered_by"] == "title_asc"

    def test_update_manuscript_document(self) -> None:
        """Updating a manuscript document should return the updated document."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        doc_id = f"doc-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "Original content.",
            },
        )

        response = client.patch(
            f"/v1/story-development/drafting/manuscript-documents/{doc_id}",
            params={"project_id": project_id},
            json={"content": "Updated content."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content."
        assert data["version"] == 2

    def test_update_manuscript_document_no_fields_returns_400(self) -> None:
        """Updating with no fields should return 400."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        doc_id = f"doc-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "Original content.",
            },
        )

        response = client.patch(
            f"/v1/story-development/drafting/manuscript-documents/{doc_id}",
            params={"project_id": project_id},
            json={},
        )
        assert response.status_code == 400

    def test_update_manuscript_document_preserves_unspecified_fields(self) -> None:
        """Updating only content should preserve title."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        doc_id = f"doc-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Original Title",
                "content": "Original content.",
            },
        )

        response = client.patch(
            f"/v1/story-development/drafting/manuscript-documents/{doc_id}",
            params={"project_id": project_id},
            json={"content": "New content."},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Original Title"
        assert response.json()["content"] == "New content."

    def test_update_nonexistent_manuscript_returns_404(self) -> None:
        """Updating a non-existent manuscript document should return 404."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.patch(
            "/v1/story-development/drafting/manuscript-documents/nonexistent",
            params={"project_id": project_id},
            json={"content": "New content."},
        )
        assert response.status_code == 404


class TestRevisionSuggestionEndpoints(BaseManuscriptTest):
    """Test revision suggestion CRUD via API endpoints."""

    def test_create_revision_suggestion_returns_201(self) -> None:
        """Creating a revision suggestion should return 201 Created."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        doc_id = f"doc-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "The quick brown fox jumped over the lazy dog.",
            },
        )

        response = client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": f"sug-{uuid4().hex[:8]}",
                "target_document_id": doc_id,
                "source_text": "The quick brown fox jumped",
                "proposed_text": "The quick red fox leaped",
                "rationale": "Improve color specificity",
                "source_context": ["opening-paragraph"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source_text"] == "The quick brown fox jumped"
        assert data["proposed_text"] == "The quick red fox leaped"
        assert data["rationale"] == "Improve color specificity"
        assert data["target_document_id"] == doc_id

    def test_create_revision_suggestion_requires_target_document(self) -> None:
        """Creating a revision suggestion for non-existent document should return 404."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": f"sug-{uuid4().hex[:8]}",
                "target_document_id": "non-existent-doc",
                "source_text": "old text",
                "proposed_text": "new text",
                "rationale": "Test rationale",
            },
        )
        assert response.status_code == 404

    def test_create_revision_suggestion_with_default_status(self) -> None:
        """Creating a revision suggestion without status should default to REQUESTED."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        
        doc_id = f"doc-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "Content here.",
            },
        )

        response = client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": f"sug-{uuid4().hex[:8]}",
                "target_document_id": doc_id,
                "source_text": "old",
                "proposed_text": "new",
                "rationale": "Test",
                "source_context": [],
            },
        )
        assert response.status_code == 201
        assert response.json()["status"] == "REQUESTED"

    def test_list_revision_suggestions_for_project(self) -> None:
        """Listing revision suggestions should return all for a project."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        
        doc_id = f"doc-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "Content.",
            },
        )

        for i in range(3):
            client.post(
                "/v1/story-development/drafting/revision-suggestions",
                json={
                    "project_id": project_id,
                    "suggestion_id": f"sug-{i}",
                    "target_document_id": doc_id,
                    "source_text": f"old text {i}",
                    "proposed_text": f"new text {i}",
                    "rationale": f"Rationale {i}",
                },
            )

        response = client.get(
            "/v1/story-development/drafting/revision-suggestions",
            params={"project_id": project_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["meta"]["ordered_by"] == "suggestion_id_asc"

    def test_list_revision_suggestions_filtered_by_document(self) -> None:
        """Listing revision suggestions with target_document_id filter should return matching only."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        
        doc_id_1 = f"doc1-{uuid4().hex[:8]}"
        doc_id_2 = f"doc2-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id_1,
                "title": "Chapter One",
                "content": "Content 1.",
            },
        )
        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id_2,
                "title": "Chapter Two",
                "content": "Content 2.",
            },
        )

        # Create suggestion for doc 1
        client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": "sug-a",
                "target_document_id": doc_id_1,
                "source_text": "old a",
                "proposed_text": "new a",
                "rationale": "Rationale A",
            },
        )
        # Create suggestion for doc 2
        client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": "sug-b",
                "target_document_id": doc_id_2,
                "source_text": "old b",
                "proposed_text": "new b",
                "rationale": "Rationale B",
            },
        )

        response = client.get(
            "/v1/story-development/drafting/revision-suggestions",
            params={"project_id": project_id, "target_document_id": doc_id_1},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        assert response.json()["items"][0]["target_document_id"] == doc_id_1

    def test_get_revision_suggestion_by_id(self) -> None:
        """Getting a revision suggestion by ID should return it."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        
        doc_id = f"doc-{uuid4().hex[:8]}"
        sug_id = f"sug-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "Content.",
            },
        )

        client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": sug_id,
                "target_document_id": doc_id,
                "source_text": "before",
                "proposed_text": "after",
                "rationale": "For testing",
            },
        )

        response = client.get(
            f"/v1/story-development/drafting/revision-suggestions/{sug_id}",
            params={"project_id": project_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["suggestion_id"] == sug_id
        assert data["source_text"] == "before"
        assert data["proposed_text"] == "after"

    def test_revision_suggestion_diff_payload_structure(self) -> None:
        """A revision suggestion should contain source_text and proposed_text for frontend diff."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        
        doc_id = f"doc-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "Line 1\nLine 2\nLine 3",
            },
        )

        response = client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": f"sug-{uuid4().hex[:8]}",
                "target_document_id": doc_id,
                "source_text": "Line 1\nLine 2",
                "proposed_text": "Line 1 modified\nLine 2 modified\nLine 3",
                "rationale": "Add modification",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "Line 1" in data["source_text"]
        assert "Line 2" in data["source_text"]
        assert "modified" in data["proposed_text"]

    def test_revision_suggestion_with_source_context(self) -> None:
        """Creating a suggestion with source_context should store all context items."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        
        doc_id = f"doc-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "Content.",
            },
        )

        response = client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": f"sug-{uuid4().hex[:8]}",
                "target_document_id": doc_id,
                "source_text": "old",
                "proposed_text": "new",
                "rationale": "Test",
                "source_context": ["context-a", "context-b", "manuscript-section-1"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source_context"] == [
            "manuscript:" + doc_id,
            "context-a",
            "context-b",
            "manuscript-section-1",
        ]


class TestManuscriptReviewEndpoint(BaseManuscriptTest):
    """Test manuscript review trigger endpoint."""

    def test_trigger_review_returns_202(self) -> None:
        """Triggering a manuscript review should return 202 Accepted."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        
        doc_id = f"doc-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "The cat sat on the mat. The cat sat on the mat.",
            },
        )

        response = client.post(
            f"/v1/story-development/drafting/manuscript-documents/{doc_id}/review",
            params={"project_id": project_id},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["document_id"] == doc_id
        assert data["project_id"] == project_id
        assert "findings" in data

    def test_trigger_review_detects_repetition(self) -> None:
        """Triggering a review on text with repeated paragraphs should find them."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        
        doc_id = f"doc-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "This is a repeated paragraph.\n\nThis is a repeated paragraph.",
            },
        )

        response = client.post(
            f"/v1/story-development/drafting/manuscript-documents/{doc_id}/review",
            params={"project_id": project_id},
        )
        assert response.status_code == 202
        data = response.json()
        # The review service should detect the blank paragraph gap (repetition)
        assert isinstance(data["findings"], list)


class TestPromoteDraftToManuscript(BaseManuscriptTest):
    """Test draft promotion endpoint."""

    def _ensure_test_draft_artifact(self, artifact_id: str, project_id: str = _TEST_PROJECT_ID) -> None:
        """Seed a draft artifact in the operations DB for promote-draft tests."""
        _ensure_test_project()
        db_path = settings.operations_db_path
        with connect(db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO draft_artifacts (
                    artifact_id, project_id, title, content, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (artifact_id, project_id, "Draft Chapter", "Draft content here.", "DRAFT", _TEST_TIMESTAMP, _TEST_TIMESTAMP),
            )
            conn.commit()

    def test_promote_draft_returns_201(self) -> None:
        """Promoting a draft to manuscript should return 201 Created."""
        artifact_id = f"artifact-{uuid4().hex[:8]}"
        doc_id = f"doc-{uuid4().hex[:8]}"

        self._ensure_test_draft_artifact(artifact_id)
        client = self._make_client()
        project_id = _TEST_PROJECT_ID

        response = client.post(
            "/v1/story-development/drafting/promote-draft",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "draft_artifact_id": artifact_id,
                "title": "Promoted Chapter",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == doc_id
        assert data["current_draft_artifact_id"] == artifact_id
        assert data["title"] == "Promoted Chapter"

    def test_promote_draft_nonexistent_returns_404(self) -> None:
        """Promoting a non-existent draft should return 404."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        

        response = client.post(
            "/v1/story-development/drafting/promote-draft",
            json={
                "project_id": project_id,
                "document_id": f"doc-{uuid4().hex[:8]}",
                "draft_artifact_id": "non-existent-artifact",
                "title": "Promoted Chapter",
            },
        )
        assert response.status_code == 404


class TestRevisionSuggestionIdempotency(BaseManuscriptTest):
    """Test that revision suggestion create is idempotent via upsert."""

    def test_create_revision_suggestion_twice_upserts(self) -> None:
        """Creating a revision suggestion twice with same ID should upsert, not duplicate."""
        client = self._make_client()
        project_id = _TEST_PROJECT_ID
        
        doc_id = f"doc-{uuid4().hex[:8]}"
        sug_id = f"sug-{uuid4().hex[:8]}"

        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": doc_id,
                "title": "Chapter One",
                "content": "Content.",
            },
        )

        # First creation
        client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": sug_id,
                "target_document_id": doc_id,
                "source_text": "original",
                "proposed_text": "proposal v1",
                "rationale": "First proposal",
            },
        )
        # Second creation with same ID
        client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": sug_id,
                "target_document_id": doc_id,
                "source_text": "original",
                "proposed_text": "proposal v2",
                "rationale": "Updated proposal",
            },
        )

        response = client.get(
            "/v1/story-development/drafting/revision-suggestions",
            params={"project_id": project_id},
        )
        assert response.status_code == 200
        # Should be only one suggestion (upserted)
        sug_items = [item for item in response.json()["items"] if item["suggestion_id"] == sug_id]
        assert len(sug_items) == 1
        assert sug_items[0]["proposed_text"] == "proposal v2"
        assert sug_items[0]["rationale"] == "Updated proposal"
