from __future__ import annotations

import pytest

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.manuscript_assist import ApplyAssistSuggestionRequest, ManuscriptAssistRequest
from app.services.drafting import DraftingService
from app.services.job_manager import JobManager
from app.services.manuscript_assist import ManuscriptAssistConflictError, ManuscriptAssistService
from app.persistence.sqlite import connect


def _service(tmp_path):
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO projects (project_id, project_name, manifest_path, db_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("proj-1", "Project 1", "manifest.json", "project.db", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        )
        connection.commit()
    drafting = DraftingService(repo)
    jobs = JobManager(db_path)
    return ManuscriptAssistService(repository=repo, drafting_service=drafting, job_manager=jobs), repo


def test_manuscript_assist_submit_and_apply(tmp_path) -> None:
    service, repo = _service(tmp_path)
    repo.upsert_manuscript_document(
        document_id="doc-1",
        project_id="proj-1",
        title="T",
        content="Hello world",
        version=1,
    )
    run = service.submit_assist(
        ManuscriptAssistRequest.model_validate(
            {
                "project_id": "proj-1",
                "document_id": "doc-1",
                "assist_kind": "line_edit_selection",
                "instruction": "Tighten",
                "text_range": {
                    "start_offset": 0,
                    "end_offset": 5,
                    "selected_text": "Hello",
                    "anchor_before": "",
                    "anchor_after": " world",
                },
            }
        )
    )
    repo.upsert_manuscript_assist_suggestion(
        suggestion_id="sug-1",
        assist_id=run.assist_id,
        project_id="proj-1",
        target_document_id="doc-1",
        suggestion_kind="line_edit_selection",
        source_text="Hello",
        proposed_text="Hi",
        rationale="Shorter",
        range_json={
            "start_offset": 0,
            "end_offset": 5,
            "selected_text": "Hello",
            "anchor_before": "",
            "anchor_after": " world",
        },
        status="PENDING",
    )
    applied = service.apply_suggestion(
        ApplyAssistSuggestionRequest.model_validate(
            {
                "project_id": "proj-1",
                "document_id": "doc-1",
                "suggestion_id": "sug-1",
                "expected_document_version": 1,
                "apply_mode": "replace_range",
            }
        )
    )
    assert applied.manuscript.content.startswith("Hi world")
    assert applied.manuscript.version == 2
    assert applied.suggestion.status == "ACCEPTED"


def test_manuscript_assist_apply_version_conflict(tmp_path) -> None:
    service, repo = _service(tmp_path)
    repo.upsert_manuscript_document(
        document_id="doc-1",
        project_id="proj-1",
        title="T",
        content="Hello world",
        version=2,
    )
    with pytest.raises(ManuscriptAssistConflictError, match="version conflict"):
        service.apply_suggestion(
            ApplyAssistSuggestionRequest.model_validate(
                {
                    "project_id": "proj-1",
                    "document_id": "doc-1",
                    "suggestion_id": "sug-1",
                    "expected_document_version": 1,
                    "apply_mode": "replace_range",
                }
            )
        )
