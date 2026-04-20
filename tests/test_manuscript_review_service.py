from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import StorySuggestionLifecycleState
from app.services.drafting import DraftingService, DraftingNotFoundError
from app.services.manuscript_review import (
    ManuscriptReviewError,
    ManuscriptReviewService,
)


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


def _build(project_id: str, tmp_path: Path) -> tuple[ManuscriptReviewService, DraftingService, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    _seed_project(db_path, project_id)
    drafting = DraftingService(repository)
    review = ManuscriptReviewService(repository)
    return review, drafting, repository


def _seed_manuscript(
    drafting: DraftingService,
    project_id: str,
    document_id: str,
    content: str,
    title: str = "Test Chapter",
) -> None:
    drafting.save_manuscript_document(
        project_id,
        document_id=document_id,
        content=content,
        title=title,
    )


# ---------------------------------------------------------------------------
# test_analyze_manuscript_returns_empty_when_no_issues
# ---------------------------------------------------------------------------

def test_analyze_manuscript_returns_empty_when_no_issues(tmp_path: Path) -> None:
    project_id = "review-clean-1"
    review, drafting, _ = _build(project_id, tmp_path)
    _seed_manuscript(
        drafting,
        project_id,
        "doc-1",
        content=(
            "The morning sun rose over the valley. Elara stood at the edge of the "
            "ancient forest, her cloak pulled tight against the chill. She had "
            "come a long way to find the ruins, and now that she was here, she "
            "wondered if she was ready for what waited within.\n\n"
            "The stones were carved with symbols she almost recognized, as if the "
            "memory of them lived somewhere deep in her blood."
        ),
    )
    results = review.analyze_manuscript(project_id, document_id="doc-1")
    assert results == ()


# ---------------------------------------------------------------------------
# test_analyze_manuscript_detects_repetition
# ---------------------------------------------------------------------------

def test_analyze_manuscript_detects_repetition(tmp_path: Path) -> None:
    project_id = "review-repetition-1"
    review, drafting, _ = _build(project_id, tmp_path)
    _seed_manuscript(
        drafting,
        project_id,
        "doc-1",
        content=(
            "Elara walked forward.\n"
            "Elara walked forward.\n"
            "Elara walked forward.\n\n"
            "She stopped and looked around.\n"
            "She stopped and looked around.\n"
            "She stopped and looked around."
        ),
    )
    results = review.analyze_manuscript(project_id, document_id="doc-1")
    assert len(results) >= 1
    suggestion = results[0]
    assert suggestion.status == StorySuggestionLifecycleState.REQUESTED.value
    assert "repetition" in suggestion.rationale.lower() or "repeat" in suggestion.rationale.lower()


# ---------------------------------------------------------------------------
# test_analyze_manuscript_detects_empty_paragraphs
# ---------------------------------------------------------------------------

def test_analyze_manuscript_detects_empty_paragraphs(tmp_path: Path) -> None:
    project_id = "review-empty-1"
    review, drafting, _ = _build(project_id, tmp_path)
    _seed_manuscript(
        drafting,
        project_id,
        "doc-1",
        content=(
            "Elara stepped into the clearing.\n\n\n\n\n"
            "The ruins loomed before her.\n\n\n\n"
            "She reached out to touch the first stone."
        ),
    )
    results = review.analyze_manuscript(project_id, document_id="doc-1")
    assert len(results) >= 1
    suggestion = results[0]
    assert suggestion.status == StorySuggestionLifecycleState.REQUESTED.value
    assert "blank" in suggestion.rationale.lower() or "empty" in suggestion.rationale.lower() or "gap" in suggestion.rationale.lower()


# ---------------------------------------------------------------------------
# test_analyze_manuscript_raises_not_found_for_missing_document
# ---------------------------------------------------------------------------

def test_analyze_manuscript_raises_not_found_for_missing_document(tmp_path: Path) -> None:
    project_id = "review-missing-1"
    review, drafting, _ = _build(project_id, tmp_path)
    _seed_manuscript(drafting, project_id, "doc-1", content="Some content")
    with pytest.raises(ManuscriptReviewError):
        review.analyze_manuscript(project_id, document_id="nonexistent-doc")


# ---------------------------------------------------------------------------
# test_analyze_manuscript_raises_not_found_for_wrong_project
# ---------------------------------------------------------------------------

def test_analyze_manuscript_raises_not_found_for_wrong_project(tmp_path: Path) -> None:
    project_a = "review-project-a"
    project_b = "review-project-b"
    review, drafting_a, _ = _build(project_a, tmp_path)
    _seed_manuscript(drafting_a, project_a, "doc-1", content="Some content")
    _build(project_b, tmp_path)
    with pytest.raises(ManuscriptReviewError):
        review.analyze_manuscript(project_b, document_id="doc-1")


# ---------------------------------------------------------------------------
# test_analyze_manuscript_detects_potential_new_characters
# ---------------------------------------------------------------------------

def test_analyze_manuscript_detects_potential_new_characters(tmp_path: Path) -> None:
    project_id = "review-characters-1"
    review, drafting, repository = _build(project_id, tmp_path)
    _seed_manuscript(
        drafting,
        project_id,
        "doc-1",
        content=(
            "Elara entered the clearing. Qyxtharion was already there, "
            "waiting beside the ancient altar. The strange being known as "
            "the Voidwalker had not spoken, but Elara could feel its presence "
            "radiating cold energy.\n\n"
            "Xypheron approached from the shadows, his eyes gleaming with "
            "malice. 'You should not have come here,' he hissed."
        ),
    )
    results = review.analyze_manuscript(project_id, document_id="doc-1")
    assert len(results) >= 1
    suggestion = results[0]
    assert suggestion.status == StorySuggestionLifecycleState.REQUESTED.value
    assert "character" in suggestion.rationale.lower() or "unnamed" in suggestion.rationale.lower()


# ---------------------------------------------------------------------------
# test_create_revision_suggestion_creates_record
# ---------------------------------------------------------------------------

def test_create_revision_suggestion_creates_record(tmp_path: Path) -> None:
    project_id = "review-create-suggestion-1"
    review, drafting, repository = _build(project_id, tmp_path)
    _seed_manuscript(drafting, project_id, "doc-1", content="Some content to review")
    results = review.analyze_manuscript(project_id, document_id="doc-1")
    # After analyze, suggestions should be persisted
    suggestions = repository.list_revision_suggestions_for_document(
        project_id, target_document_id="doc-1"
    )
    assert len(suggestions) == len(results)


# ---------------------------------------------------------------------------
# test_analyze_returns_suggestions_with_correct_target_document
# ---------------------------------------------------------------------------

def test_analyze_returns_suggestions_with_correct_target_document(tmp_path: Path) -> None:
    project_id = "review-target-doc-1"
    review, drafting, _ = _build(project_id, tmp_path)
    _seed_manuscript(
        drafting,
        project_id,
        "doc-1",
        content=(
            "Elara walked forward. Elara walked forward. Elara walked forward."
        ),
    )
    results = review.analyze_manuscript(project_id, document_id="doc-1")
    for suggestion in results:
        assert suggestion.target_document_id == "doc-1"
        assert suggestion.project_id == project_id

