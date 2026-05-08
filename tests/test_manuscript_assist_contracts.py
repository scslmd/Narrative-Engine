"""Tests for manuscript-aid request contracts and diff-style response payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.services.drafting import DraftingService
from app.schemas import StorySuggestionLifecycleState


STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)


def _make_db(tmp_path: Path) -> Path:
    return tmp_path / "data" / "state" / "narrative_ops.db"


def _seed_project(db_path: Path, project_id: str) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                f"Test Project {project_id[:8]}",
                f"data/projects/{project_id}/manifest.json",
                f"data/projects/{project_id}/bible.db",
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


class TestManuscriptAidRequestContract:
    """Test the manuscript-aid request contracts (revision suggestions)."""

    def _build_service(self, tmp_path: Path) -> tuple[DraftingService, StoryDevelopmentRepository]:
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        repo = StoryDevelopmentRepository(db_path)
        return DraftingService(repo), repo

    def test_create_revision_suggestion_validates_target_document(self, tmp_path: Path) -> None:
        """Creating a revision suggestion should fail when target document doesn't exist."""
        service, _ = self._build_service(tmp_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        source_text = "The quick brown fox."
        proposed_text = "The quick red fox."

        with pytest.raises(Exception):
            service.create_revision_suggestion(
                project_id,
                suggestion_id=f"suggestion-{uuid4().hex[:8]}",
                target_document_id="non-existent-document",
                source_text=source_text,
                proposed_text=proposed_text,
                rationale="Color correction",
                source_context=["manuscript-section-1"],
                status=StorySuggestionLifecycleState.REQUESTED,
            )

    def test_create_revision_suggestion_stores_before_and_after_text(self, tmp_path: Path) -> None:
        """A revision suggestion should store both source_text and proposed_text for diff."""
        service, repo = self._build_service(tmp_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(repo.db_path, project_id)

        manuscript = service.save_manuscript_document(
            project_id,
            document_id=f"doc-{uuid4().hex[:8]}",
            title="Chapter One",
            content="The quick brown fox jumped over the lazy dog.",
        )

        suggestion = service.create_revision_suggestion(
            project_id,
            suggestion_id=f"suggestion-{uuid4().hex[:8]}",
            target_document_id=manuscript.document_id,
            source_text="The quick brown fox jumped over the lazy dog.",
            proposed_text="The quick red fox leaped over the sleeping dog.",
            rationale="Improve specificity and tone",
            source_context=["opening-paragraph"],
            status=StorySuggestionLifecycleState.REQUESTED,
        )
        assert suggestion.source_text == "The quick brown fox jumped over the lazy dog."
        assert suggestion.proposed_text == "The quick red fox leaped over the sleeping dog."
        assert suggestion.rationale == "Improve specificity and tone"
        assert suggestion.status == StorySuggestionLifecycleState.REQUESTED

    def test_create_revision_suggestion_with_json_context(self, tmp_path: Path) -> None:
        """Source context should be stored as a JSON-serializable list."""
        service, repo = self._build_service(tmp_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(repo.db_path, project_id)

        manuscript = service.save_manuscript_document(
            project_id,
            document_id=f"doc-{uuid4().hex[:8]}",
            title="Chapter One",
            content="Some content here.",
        )

        suggestion = service.create_revision_suggestion(
            project_id,
            suggestion_id=f"suggestion-{uuid4().hex[:8]}",
            target_document_id=manuscript.document_id,
            source_text="old text",
            proposed_text="new text",
            rationale="Test rationale",
            source_context=["context-a", "context-b"],
            status=StorySuggestionLifecycleState.REQUESTED,
        )
        assert "manuscript:" + manuscript.document_id in suggestion.source_context
        assert "context-a" in suggestion.source_context
        assert "context-b" in suggestion.source_context

    def test_list_revision_suggestions_for_project(self, tmp_path: Path) -> None:
        """Listing revision suggestions by project should return all suggestions."""
        service, repo = self._build_service(tmp_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(repo.db_path, project_id)

        manuscript = service.save_manuscript_document(
            project_id,
            document_id=f"doc-{uuid4().hex[:8]}",
            title="Chapter One",
            content="Content 1.",
        )

        manuscript2 = service.save_manuscript_document(
            project_id,
            document_id=f"doc2-{uuid4().hex[:8]}",
            title="Chapter Two",
            content="Content 2.",
        )

        service.create_revision_suggestion(
            project_id,
            suggestion_id="sug-1",
            target_document_id=manuscript.document_id,
            source_text="old 1",
            proposed_text="new 1",
            rationale="Reason 1",
            source_context=["ctx-1"],
        )
        service.create_revision_suggestion(
            project_id,
            suggestion_id="sug-2",
            target_document_id=manuscript.document_id,
            source_text="old 2",
            proposed_text="new 2",
            rationale="Reason 2",
            source_context=["ctx-2"],
        )
        service.create_revision_suggestion(
            project_id,
            suggestion_id="sug-3",
            target_document_id=manuscript2.document_id,
            source_text="old 3",
            proposed_text="new 3",
            rationale="Reason 3",
            source_context=["ctx-3"],
        )

        suggestions = service.list_revision_suggestions(project_id)
        assert len(suggestions) == 3

        suggestions_for_doc = service.list_revision_suggestions_for_document(
            project_id, target_document_id=manuscript.document_id,
        )
        assert len(suggestions_for_doc) == 2

    def test_get_revision_suggestion_by_id(self, tmp_path: Path) -> None:
        """Getting a suggestion by ID should return the correct record."""
        service, repo = self._build_service(tmp_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        sug_id = f"sug-{uuid4().hex[:8]}"
        _seed_project(repo.db_path, project_id)

        manuscript = service.save_manuscript_document(
            project_id,
            document_id=f"doc-{uuid4().hex[:8]}",
            title="Chapter One",
            content="Content.",
        )

        suggestion = service.create_revision_suggestion(
            project_id,
            suggestion_id=sug_id,
            target_document_id=manuscript.document_id,
            source_text="before",
            proposed_text="after",
            rationale="For testing",
        )
        fetched = service.get_revision_suggestion(project_id, suggestion_id=sug_id)
        assert fetched.suggestion_id == sug_id
        assert fetched.source_text == "before"
        assert fetched.proposed_text == "after"

    def test_upsert_revision_suggestion_is_idempotent(self, tmp_path: Path) -> None:
        """Calling create_revision_suggestion twice with same ID should not create duplicates."""
        service, repo = self._build_service(tmp_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        sug_id = f"sug-{uuid4().hex[:8]}"
        _seed_project(repo.db_path, project_id)

        manuscript = service.save_manuscript_document(
            project_id,
            document_id=f"doc-{uuid4().hex[:8]}",
            title="Chapter One",
            content="Content.",
        )

        service.create_revision_suggestion(
            project_id,
            suggestion_id=sug_id,
            target_document_id=manuscript.document_id,
            source_text="original",
            proposed_text="proposal v1",
            rationale="First proposal",
        )
        service.create_revision_suggestion(
            project_id,
            suggestion_id=sug_id,
            target_document_id=manuscript.document_id,
            source_text="original",
            proposed_text="proposal v2",
            rationale="Updated proposal",
        )

        suggestions = service.list_revision_suggestions(project_id)
        assert len(suggestions) == 1
        assert suggestions[0].proposed_text == "proposal v2"


class TestDiffPayloadContract:
    """Test that diff-style response payloads are correctly structured."""

    def _build_service(self, tmp_path: Path) -> tuple[DraftingService, StoryDevelopmentRepository]:
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        repo = StoryDevelopmentRepository(db_path)
        return DraftingService(repo), repo

    def test_diff_payload_contains_both_texts(self, tmp_path: Path) -> None:
        """A revision suggestion payload should contain source_text and proposed_text for frontend diff."""
        service, repo = self._build_service(tmp_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(repo.db_path, project_id)

        manuscript = service.save_manuscript_document(
            project_id,
            document_id=f"doc-{uuid4().hex[:8]}",
            title="Chapter One",
            content="Line 1\nLine 2\nLine 3",
        )

        suggestion = service.create_revision_suggestion(
            project_id,
            suggestion_id=f"sug-{uuid4().hex[:8]}",
            target_document_id=manuscript.document_id,
            source_text="Line 1\nLine 2",
            proposed_text="Line 1\nLine 2 modified\nLine 3",
            rationale="Add modification",
        )
        # Verify both fields are present and correctly set
        assert suggestion.source_text == "Line 1\nLine 2"
        assert suggestion.proposed_text == "Line 1\nLine 2 modified\nLine 3"
        # Rationale should be present for context
        assert suggestion.rationale == "Add modification"

    def test_diff_payload_source_text_matches_manuscript_segment(self, tmp_path: Path) -> None:
        """Source text should match the actual manuscript content segment it references."""
        service, repo = self._build_service(tmp_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(repo.db_path, project_id)

        full_content = """Chapter One

The morning sun cast long shadows across the valley. Birds chirped
in the trees as the protagonist woke from a restless night's sleep.

The day ahead promised nothing but trouble."""

        manuscript = service.save_manuscript_document(
            project_id,
            document_id=f"doc-{uuid4().hex[:8]}",
            title="Chapter One",
            content=full_content,
        )

        source_segment = "The morning sun cast long shadows across the valley."

        suggestion = service.create_revision_suggestion(
            project_id,
            suggestion_id=f"sug-{uuid4().hex[:8]}",
            target_document_id=manuscript.document_id,
            source_text=source_segment,
            proposed_text="Dawn light stretched across the valley floor.",
            rationale="More vivid description",
        )

        assert suggestion.source_text == source_segment
        assert manuscript.content == full_content
        # Source should be a substring of the manuscript
        assert suggestion.source_text in manuscript.content

    def test_diff_payload_multiple_suggestions_same_segment(self, tmp_path: Path) -> None:
        """Multiple suggestions can target the same source text segment."""
        service, repo = self._build_service(tmp_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(repo.db_path, project_id)

        manuscript = service.save_manuscript_document(
            project_id,
            document_id=f"doc-{uuid4().hex[:8]}",
            title="Chapter One",
            content="The cat sat on the mat.",
        )

        sug1 = service.create_revision_suggestion(
            project_id,
            suggestion_id="sug-1",
            target_document_id=manuscript.document_id,
            source_text="The cat sat on the mat.",
            proposed_text="The black cat perched on the woven rug.",
            rationale="Add color and specificity",
        )
        sug2 = service.create_revision_suggestion(
            project_id,
            suggestion_id="sug-2",
            target_document_id=manuscript.document_id,
            source_text="The cat sat on the mat.",
            proposed_text="A feline rested upon the floor covering.",
            rationale="More formal tone",
        )

        suggestions = service.list_revision_suggestions(project_id)
        assert len(suggestions) == 2
        assert sug1.suggestion_id == "sug-1"
        assert sug2.suggestion_id == "sug-2"
        # Same source, different proposals
        assert sug1.source_text == sug2.source_text
        assert sug1.proposed_text != sug2.proposed_text


class TestManuscriptAidStatusTransitions:
    """Test revision suggestion lifecycle state management."""

    def _build_service(self, tmp_path: Path) -> tuple[DraftingService, StoryDevelopmentRepository]:
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        repo = StoryDevelopmentRepository(db_path)
        return DraftingService(repo), repo

    def test_suggestion_status_changes(self, tmp_path: Path) -> None:
        """Revision suggestions should support status transitions."""
        service, repo = self._build_service(tmp_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(repo.db_path, project_id)

        manuscript = service.save_manuscript_document(
            project_id,
            document_id=f"doc-{uuid4().hex[:8]}",
            title="Chapter One",
            content="Content here.",
        )

        suggestion = service.create_revision_suggestion(
            project_id,
            suggestion_id="sug-1",
            target_document_id=manuscript.document_id,
            source_text="old",
            proposed_text="new",
            rationale="For review",
            status=StorySuggestionLifecycleState.REQUESTED,
        )
        assert suggestion.status == StorySuggestionLifecycleState.REQUESTED

        # Update to accepted
        record = repo.upsert_revision_suggestion(
            suggestion_id="sug-1",
            project_id=project_id,
            target_document_id=manuscript.document_id,
            source_text="old",
            proposed_text="new",
            rationale="Accepted after review",
            source_context=["ctx-1"],
            status=StorySuggestionLifecycleState.ACCEPTED,
        )
        assert record.status == StorySuggestionLifecycleState.ACCEPTED

        # Update to rejected
        record = repo.upsert_revision_suggestion(
            suggestion_id="sug-1",
            project_id=project_id,
            target_document_id=manuscript.document_id,
            source_text="old",
            proposed_text="new",
            rationale="Rejected - not suitable",
            source_context=["ctx-1"],
            status=StorySuggestionLifecycleState.REJECTED,
        )
        assert record.status == StorySuggestionLifecycleState.REJECTED
