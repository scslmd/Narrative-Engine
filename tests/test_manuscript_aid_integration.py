"""Integration tests for manuscript aid API endpoints."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import build_story_development_router
from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import StoryArtifactLifecycleState, StorySuggestionLifecycleState


def _build_client(tmp_path: Path, project_id: str) -> tuple[TestClient, str, Path]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    ensure_operations_db(db_path)
    _seed_project(db_path, project_id)

    repo = StoryDevelopmentRepository(db_path)
    router = build_story_development_router(repo, prefix="")
    app = FastAPI()
    app.include_router(router, prefix="/v1/story-development")

    client = TestClient(app)
    return client, project_id, db_path


def _seed_project(db_path: Path, project_id: str) -> None:
    with connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """
            INSERT INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                "Manuscript Aid Integration Test Project",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                "2026-03-20T12:00:00+00:00",
                "2026-03-20T12:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO draft_artifacts (
                artifact_id, project_id, title, content, source_plan_ids_json,
                status, provenance_note, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "artifact-1",
                project_id,
                "Chapter One Draft",
                "Once upon a time, the world was quiet.",
                "[]",
                StoryArtifactLifecycleState.DRAFT,
                "Initial draft from chapter plan",
                "2026-03-20T12:00:00+00:00",
                "2026-03-20T12:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO chapter_plans (
                chapter_id, project_id, sequence_id, title, summary,
                objective, conflict, stakes, status, position, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ch-1",
                project_id,
                None,
                "Chapter One",
                "The beginning",
                "Introduce the world",
                "Unknown threat",
                "Everyone",
                "draft",
                0,
                "2026-03-20T12:00:00+00:00",
                "2026-03-20T12:00:00+00:00",
            ),
        )
        connection.commit()


class TestManuscriptDocumentEndpoints:
    """Integration tests for manuscript document API endpoints."""

    def test_create_manuscript_document_returns_201(self, tmp_path: Path) -> None:
        """Creating a manuscript document should return 201."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

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
        assert data["project_id"] == project_id
        assert data["title"] == "Chapter One"
        assert data["content"] == "The quick brown fox jumped over the lazy dog."

    def test_create_manuscript_document_with_chapter_ref(
        self, tmp_path: Path
    ) -> None:
        """Creating a manuscript document with chapter_id should link to it."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc-{uuid4().hex[:8]}",
                "title": "Chapter One Draft",
                "content": "The world was quiet.",
                "chapter_id": "ch-1",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["chapter_id"] == "ch-1"

    def test_list_manuscript_documents(self, tmp_path: Path) -> None:
        """Listing manuscript documents should return all documents for a project."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        # Create two documents
        for i in range(2):
            client.post(
                "/v1/story-development/drafting/manuscript-documents",
                json={
                    "project_id": project_id,
                    "document_id": f"doc-{i}",
                    "title": f"Document {i}",
                    "content": f"Content {i}",
                },
            )

        response = client.get(
            "/v1/story-development/drafting/manuscript-documents",
            params={"project_id": project_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert len(data["items"]) == 2

    def test_get_manuscript_document(self, tmp_path: Path) -> None:
        """Getting a specific manuscript document should return it."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        # Create a document
        create_response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc-{uuid4().hex[:8]}",
                "title": "Chapter One",
                "content": "The world was quiet.",
            },
        )
        doc_id = create_response.json()["document_id"]

        response = client.get(
            f"/v1/story-development/drafting/manuscript-documents/{doc_id}",
            params={"project_id": project_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id
        assert data["title"] == "Chapter One"

    def test_get_manuscript_document_not_found(
        self, tmp_path: Path
    ) -> None:
        """Getting a non-existent document should return 404."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        response = client.get(
            "/v1/story-development/drafting/manuscript-documents/nonexistent",
            params={"project_id": project_id},
        )
        assert response.status_code == 404

    def test_update_manuscript_document(self, tmp_path: Path) -> None:
        """Updating a manuscript document should return the updated document."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        # Create a document
        create_response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc-{uuid4().hex[:8]}",
                "title": "Original Title",
                "content": "Original content.",
            },
        )
        doc_id = create_response.json()["document_id"]

        # Update the document
        response = client.patch(
            f"/v1/story-development/drafting/manuscript-documents/{doc_id}",
            params={"project_id": project_id},
            json={"title": "Updated Title", "content": "Updated content."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content."

    def test_update_manuscript_document_partial(self, tmp_path: Path) -> None:
        """Updating only title should preserve original content."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        # Create a document
        create_response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc-{uuid4().hex[:8]}",
                "title": "Original Title",
                "content": "Original content.",
            },
        )
        doc_id = create_response.json()["document_id"]

        # Update only title
        response = client.patch(
            f"/v1/story-development/drafting/manuscript-documents/{doc_id}",
            params={"project_id": project_id},
            json={"title": "New Title"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["content"] == "Original content."


class TestRevisionSuggestionEndpoints:
    """Integration tests for revision suggestion API endpoints."""

    def test_create_revision_suggestion_returns_201(
        self, tmp_path: Path
    ) -> None:
        """Creating a revision suggestion should return 201."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        # Create a manuscript document first
        doc_response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc-{uuid4().hex[:8]}",
                "title": "Chapter One",
                "content": "The quick brown fox jumped over the lazy dog.",
            },
        )
        doc_id = doc_response.json()["document_id"]

        response = client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": f"sug-{uuid4().hex[:8]}",
                "target_document_id": doc_id,
                "source_text": "The quick brown fox jumped over the lazy dog.",
                "proposed_text": "The swift amber fox leaped over the sleeping canine.",
                "rationale": "Improve specificity and tone",
                "source_context": ["opening-paragraph"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["target_document_id"] == doc_id
        assert data["rationale"] == "Improve specificity and tone"

    def test_create_revision_suggestion_requires_target_document(
        self, tmp_path: Path
    ) -> None:
        """Creating a revision suggestion without a valid target document should return 404."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        response = client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": f"sug-{uuid4().hex[:8]}",
                "target_document_id": "nonexistent-document",
                "source_text": "old text",
                "proposed_text": "new text",
                "rationale": "Test rationale",
            },
        )
        assert response.status_code == 404

    def test_list_revision_suggestions(self, tmp_path: Path) -> None:
        """Listing revision suggestions should return all suggestions for a project."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        # Create documents and suggestions
        doc1_response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc1-{uuid4().hex[:8]}",
                "title": "Chapter One",
                "content": "Content one.",
            },
        )
        doc1_id = doc1_response.json()["document_id"]

        doc2_response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc2-{uuid4().hex[:8]}",
                "title": "Chapter Two",
                "content": "Content two.",
            },
        )
        doc2_id = doc2_response.json()["document_id"]

        # Create suggestions for both documents
        client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": "sug-1",
                "target_document_id": doc1_id,
                "source_text": "old1",
                "proposed_text": "new1",
                "rationale": "Rationale 1",
            },
        )
        client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": "sug-2",
                "target_document_id": doc2_id,
                "source_text": "old2",
                "proposed_text": "new2",
                "rationale": "Rationale 2",
            },
        )

        response = client.get(
            "/v1/story-development/drafting/revision-suggestions",
            params={"project_id": project_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    def test_list_revision_suggestions_filtered_by_document(
        self, tmp_path: Path
    ) -> None:
        """Listing revision suggestions filtered by target_document_id should return only matching."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        # Create documents and suggestions
        doc1_response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc1-{uuid4().hex[:8]}",
                "title": "Chapter One",
                "content": "Content one.",
            },
        )
        doc1_id = doc1_response.json()["document_id"]

        doc2_response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc2-{uuid4().hex[:8]}",
                "title": "Chapter Two",
                "content": "Content two.",
            },
        )
        doc2_id = doc2_response.json()["document_id"]

        client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": "sug-1",
                "target_document_id": doc1_id,
                "source_text": "old1",
                "proposed_text": "new1",
                "rationale": "Rationale 1",
            },
        )
        client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": "sug-2",
                "target_document_id": doc2_id,
                "source_text": "old2",
                "proposed_text": "new2",
                "rationale": "Rationale 2",
            },
        )

        response = client.get(
            "/v1/story-development/drafting/revision-suggestions",
            params={"project_id": project_id, "target_document_id": doc1_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["target_document_id"] == doc1_id

    def test_get_revision_suggestion(self, tmp_path: Path) -> None:
        """Getting a specific revision suggestion should return it."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        # Create a document and suggestion
        doc_response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc-{uuid4().hex[:8]}",
                "title": "Chapter One",
                "content": "Content.",
            },
        )
        doc_id = doc_response.json()["document_id"]

        sug_response = client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": f"sug-{uuid4().hex[:8]}",
                "target_document_id": doc_id,
                "source_text": "old",
                "proposed_text": "new",
                "rationale": "Test rationale",
            },
        )
        sug_id = sug_response.json()["suggestion_id"]

        response = client.get(
            f"/v1/story-development/drafting/revision-suggestions/{sug_id}",
            params={"project_id": project_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["suggestion_id"] == sug_id
        assert data["source_text"] == "old"
        assert data["proposed_text"] == "new"

    def test_get_revision_suggestion_not_found(
        self, tmp_path: Path
    ) -> None:
        """Getting a non-existent suggestion should return 404."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        response = client.get(
            "/v1/story-development/drafting/revision-suggestions/nonexistent",
            params={"project_id": project_id},
        )
        assert response.status_code == 404

    def test_revision_suggestion_stores_source_and_proposed_text(
        self, tmp_path: Path
    ) -> None:
        """A revision suggestion should store both source_text and proposed_text."""
        project_id = f"test-proj-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id)

        doc_response = client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id,
                "document_id": f"doc-{uuid4().hex[:8]}",
                "title": "Chapter One",
                "content": "The quick brown fox jumped over the lazy dog.",
            },
        )
        doc_id = doc_response.json()["document_id"]

        response = client.post(
            "/v1/story-development/drafting/revision-suggestions",
            json={
                "project_id": project_id,
                "suggestion_id": f"sug-{uuid4().hex[:8]}",
                "target_document_id": doc_id,
                "source_text": "The quick brown fox jumped over the lazy dog.",
                "proposed_text": "The swift amber fox leaped over the sleeping canine.",
                "rationale": "Improve specificity",
                "source_context": ["opening-paragraph"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert (
            data["source_text"]
            == "The quick brown fox jumped over the lazy dog."
        )
        assert (
            data["proposed_text"]
            == "The swift amber fox leaped over the sleeping canine."
        )


class TestManuscriptDocumentCrossProject:
    """Cross-project isolation tests for manuscript documents."""

    def test_documents_are_project_isolated(self, tmp_path: Path) -> None:
        """Creating a document in one project should not affect another project."""
        project_id_1 = f"test-proj-1-{uuid4().hex[:8]}"
        project_id_2 = f"test-proj-2-{uuid4().hex[:8]}"
        client, _, _ = _build_client(tmp_path, project_id_1)

        # Create a document in project 1
        client.post(
            "/v1/story-development/drafting/manuscript-documents",
            json={
                "project_id": project_id_1,
                "document_id": "doc-shared-id",
                "title": "Document in Project 1",
                "content": "Content for project 1.",
            },
        )

        # Build a new client for project 2
        client2, _, _ = _build_client(tmp_path, project_id_2)

        # Listing documents for project 2 should be empty
        response = client2.get(
            "/v1/story-development/drafting/manuscript-documents",
            params={"project_id": project_id_2},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0

        # Listing documents for project 1 should have one
        response = client.get(
            "/v1/story-development/drafting/manuscript-documents",
            params={"project_id": project_id_1},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
