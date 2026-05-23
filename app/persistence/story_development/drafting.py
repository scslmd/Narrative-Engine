from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    now as _now,
)
from . import (
    DraftArtifactRecord,
    ManuscriptDocumentRecord,
    RevisionSuggestionRecord,
    StoryArtifactLifecycleState,
    StorySuggestionLifecycleState,
)
from .converters import (
    _draft_artifact_row_to_record, _manuscript_document_row_to_record,
    _revision_suggestion_row_to_record,
)

from ..sqlite import connect


class _DraftArtifactMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_draft_artifact(
        self,
        *,
        artifact_id: str,
        project_id: str,
        title: str,
        content: str,
        source_plan_ids: Sequence[str] | None = None,
        source_context: Sequence[str] | None = None,
        provenance_note: str | None = None,
        status: StoryArtifactLifecycleState = StoryArtifactLifecycleState.DRAFT,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> DraftArtifactRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO draft_artifacts (
                    artifact_id, project_id, title, content, source_plan_ids_json, source_context_json,
                    provenance_note, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(artifact_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    content = excluded.content,
                    source_plan_ids_json = excluded.source_plan_ids_json,
                    source_context_json = excluded.source_context_json,
                    provenance_note = excluded.provenance_note,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    artifact_id,
                    project_id,
                    title,
                    content,
                    _json_list(list(source_plan_ids or [])),
                    _json_list(list(source_context or [])),
                    provenance_note,
                    status.value if isinstance(status, StoryArtifactLifecycleState) else str(status),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_draft_artifact(artifact_id)



    def get_draft_artifact(self, artifact_id: str) -> DraftArtifactRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM draft_artifacts
                WHERE artifact_id = ?
                """,
                (artifact_id,),
            ).fetchone()
        if row is None:
            raise KeyError(artifact_id)
        return _draft_artifact_row_to_record(row)



    def list_draft_artifacts(self, project_id: str) -> list[DraftArtifactRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM draft_artifacts
                WHERE project_id = ?
                ORDER BY title COLLATE NOCASE, artifact_id
                """,
                (project_id,),
            ).fetchall()
        return [_draft_artifact_row_to_record(row) for row in rows]


class _ManuscriptDocumentMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_manuscript_document(
        self,
        *,
        document_id: str,
        project_id: str,
        title: str,
        display_title: str | None = None,
        content: str,
        chapter_id: str | None = None,
        scene_id: str | None = None,
        current_draft_artifact_id: str | None = None,
        version: int = 1,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ManuscriptDocumentRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        if chapter_id is not None:
            chapter = self.get_chapter_plan(chapter_id)
            if chapter.project_id != project_id:
                raise ValueError("chapter_id must belong to the same project")
        if scene_id is not None:
            scene = self.get_scene_plan(scene_id)
            if scene.project_id != project_id:
                raise ValueError("scene_id must belong to the same project")
        if current_draft_artifact_id is not None:
            draft = self.get_draft_artifact(current_draft_artifact_id)
            if draft.project_id != project_id:
                raise ValueError("current_draft_artifact_id must belong to the same project")
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO manuscript_documents (
                    document_id, project_id, title, display_title, content, chapter_id, scene_id, current_draft_artifact_id,
                    version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    display_title = excluded.display_title,
                    content = excluded.content,
                    chapter_id = excluded.chapter_id,
                    scene_id = excluded.scene_id,
                    current_draft_artifact_id = excluded.current_draft_artifact_id,
                    version = excluded.version,
                    updated_at = excluded.updated_at
                """,
                (
                    document_id,
                    project_id,
                    title,
                    display_title,
                    content,
                    chapter_id,
                    scene_id,
                    current_draft_artifact_id,
                    int(version),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_manuscript_document(document_id)



    def get_manuscript_document(self, document_id: str) -> ManuscriptDocumentRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM manuscript_documents
                WHERE document_id = ?
                """,
                (document_id,),
            ).fetchone()
        if row is None:
            raise KeyError(document_id)
        return _manuscript_document_row_to_record(row)



    def list_manuscript_documents(self, project_id: str) -> list[ManuscriptDocumentRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM manuscript_documents
                WHERE project_id = ?
                ORDER BY title COLLATE NOCASE, document_id
                """,
                (project_id,),
            ).fetchall()
        return [_manuscript_document_row_to_record(row) for row in rows]


class _RevisionSuggestionMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_revision_suggestion(
        self,
        *,
        suggestion_id: str,
        project_id: str,
        target_document_id: str,
        source_text: str,
        proposed_text: str,
        rationale: str,
        source_context: Sequence[str] | None = None,
        status: StorySuggestionLifecycleState = StorySuggestionLifecycleState.REQUESTED,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> RevisionSuggestionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        document = self.get_manuscript_document(target_document_id)
        if document.project_id != project_id:
            raise ValueError("target_document_id must belong to the same project")
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO revision_suggestions (
                    suggestion_id, project_id, target_document_id, source_text, proposed_text, rationale,
                    source_context_json, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(suggestion_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    target_document_id = excluded.target_document_id,
                    source_text = excluded.source_text,
                    proposed_text = excluded.proposed_text,
                    rationale = excluded.rationale,
                    source_context_json = excluded.source_context_json,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    suggestion_id,
                    project_id,
                    target_document_id,
                    source_text,
                    proposed_text,
                    rationale,
                    _json_list(list(source_context or [])),
                    status.value if isinstance(status, StorySuggestionLifecycleState) else str(status),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_revision_suggestion(suggestion_id)



    def get_revision_suggestion(self, suggestion_id: str) -> RevisionSuggestionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM revision_suggestions
                WHERE suggestion_id = ?
                """,
                (suggestion_id,),
            ).fetchone()
        if row is None:
            raise KeyError(suggestion_id)
        return _revision_suggestion_row_to_record(row)



    def list_revision_suggestions(self, project_id: str) -> list[RevisionSuggestionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM revision_suggestions
                WHERE project_id = ?
                ORDER BY suggestion_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_revision_suggestion_row_to_record(row) for row in rows]



    def list_revision_suggestions_for_document(self, project_id: str, *, target_document_id: str) -> list[RevisionSuggestionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM revision_suggestions
                WHERE project_id = ? AND target_document_id = ?
                ORDER BY suggestion_id ASC
                """,
                (project_id, target_document_id),
            ).fetchall()
        return [_revision_suggestion_row_to_record(row) for row in rows]
