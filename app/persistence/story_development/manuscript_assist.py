from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    json_object as _json_object,
    now as _now,
)
from . import (
    ManuscriptAssistGateResultRecord, ManuscriptAssistRunRecord,
    ManuscriptAssistSuggestionRecord,
)
from .converters import (
    _manuscript_assist_run_row_to_record, _manuscript_assist_suggestion_row_to_record,
    _manuscript_assist_gate_result_row_to_record,
)

from ..sqlite import connect


class _AssistRunMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_manuscript_assist_run(
        self,
        *,
        assist_id: str,
        project_id: str,
        document_id: str,
        assist_kind: str,
        request_json: Mapping[str, Any],
        status: str,
        summary: str = "",
        created_draft_artifact_id: str | None = None,
        created_branch_id: str | None = None,
        created_manuscript_document_id: str | None = None,
        job_ids: list[str] | None = None,
        warnings: list[str] | None = None,
        idempotency_key: str | None = None,
        request_hash: str = "",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ManuscriptAssistRunRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            if idempotency_key:
                existing = connection.execute(
                    """
                    SELECT assist_id, request_hash
                    FROM manuscript_assist_runs
                    WHERE project_id = ? AND idempotency_key = ?
                    """,
                    (project_id, idempotency_key),
                ).fetchone()
                if existing is not None and existing["request_hash"] != request_hash:
                    raise ValueError("idempotency key conflict: request hash mismatch")
            connection.execute(
                """
                INSERT INTO manuscript_assist_runs (
                    assist_id, project_id, document_id, assist_kind, request_json, status, summary,
                    created_draft_artifact_id, created_branch_id, created_manuscript_document_id,
                    job_ids_json, warnings_json, idempotency_key, request_hash, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(assist_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    document_id = excluded.document_id,
                    assist_kind = excluded.assist_kind,
                    request_json = excluded.request_json,
                    status = excluded.status,
                    summary = excluded.summary,
                    created_draft_artifact_id = excluded.created_draft_artifact_id,
                    created_branch_id = excluded.created_branch_id,
                    created_manuscript_document_id = excluded.created_manuscript_document_id,
                    job_ids_json = excluded.job_ids_json,
                    warnings_json = excluded.warnings_json,
                    idempotency_key = excluded.idempotency_key,
                    request_hash = excluded.request_hash,
                    updated_at = excluded.updated_at
                """,
                (
                    assist_id,
                    project_id,
                    document_id,
                    assist_kind,
                    _json_object(request_json),
                    status,
                    summary,
                    created_draft_artifact_id,
                    created_branch_id,
                    created_manuscript_document_id,
                    _json_list(job_ids),
                    _json_list(warnings),
                    idempotency_key,
                    request_hash,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_manuscript_assist_run(assist_id)



    def get_manuscript_assist_run(self, assist_id: str) -> ManuscriptAssistRunRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM manuscript_assist_runs
                WHERE assist_id = ?
                """,
                (assist_id,),
            ).fetchone()
        if row is None:
            raise KeyError(assist_id)
        return _manuscript_assist_run_row_to_record(row)



    def list_manuscript_assist_runs(
        self,
        project_id: str,
        document_id: str | None = None,
    ) -> list[ManuscriptAssistRunRecord]:
        with connect(self.db_path) as connection:
            if document_id is None:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM manuscript_assist_runs
                    WHERE project_id = ?
                    ORDER BY updated_at DESC
                    """,
                    (project_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM manuscript_assist_runs
                    WHERE project_id = ? AND document_id = ?
                    ORDER BY updated_at DESC
                    """,
                    (project_id, document_id),
                ).fetchall()
        return [_manuscript_assist_run_row_to_record(row) for row in rows]


class _AssistSuggestionMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_manuscript_assist_suggestion(
        self,
        *,
        suggestion_id: str,
        assist_id: str,
        project_id: str,
        target_document_id: str,
        suggestion_kind: str,
        source_text: str,
        proposed_text: str,
        rationale: str,
        range_json: Mapping[str, Any] | None = None,
        canon_risk: str = "none",
        confidence_score: float = 0.0,
        source_context: list[str] | None = None,
        status: str = "REQUESTED",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ManuscriptAssistSuggestionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO manuscript_assist_suggestions (
                    suggestion_id, assist_id, project_id, target_document_id, suggestion_kind,
                    source_text, proposed_text, rationale, range_json, canon_risk, confidence_score,
                    source_context_json, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(suggestion_id) DO UPDATE SET
                    assist_id = excluded.assist_id,
                    project_id = excluded.project_id,
                    target_document_id = excluded.target_document_id,
                    suggestion_kind = excluded.suggestion_kind,
                    source_text = excluded.source_text,
                    proposed_text = excluded.proposed_text,
                    rationale = excluded.rationale,
                    range_json = excluded.range_json,
                    canon_risk = excluded.canon_risk,
                    confidence_score = excluded.confidence_score,
                    source_context_json = excluded.source_context_json,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    suggestion_id,
                    assist_id,
                    project_id,
                    target_document_id,
                    suggestion_kind,
                    source_text,
                    proposed_text,
                    rationale,
                    _json_object(range_json) if range_json is not None else None,
                    canon_risk,
                    float(confidence_score),
                    _json_list(source_context),
                    status,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_manuscript_assist_suggestion(suggestion_id)



    def get_manuscript_assist_suggestion(self, suggestion_id: str) -> ManuscriptAssistSuggestionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM manuscript_assist_suggestions
                WHERE suggestion_id = ?
                """,
                (suggestion_id,),
            ).fetchone()
        if row is None:
            raise KeyError(suggestion_id)
        return _manuscript_assist_suggestion_row_to_record(row)



    def list_manuscript_assist_suggestions(
        self,
        project_id: str,
        document_id: str,
        status: str | None = None,
    ) -> list[ManuscriptAssistSuggestionRecord]:
        with connect(self.db_path) as connection:
            if status is None:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM manuscript_assist_suggestions
                    WHERE project_id = ? AND target_document_id = ?
                    ORDER BY updated_at DESC
                    """,
                    (project_id, document_id),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM manuscript_assist_suggestions
                    WHERE project_id = ? AND target_document_id = ? AND status = ?
                    ORDER BY updated_at DESC
                    """,
                    (project_id, document_id, status),
                ).fetchall()
        return [_manuscript_assist_suggestion_row_to_record(row) for row in rows]



    def update_manuscript_assist_suggestion_status(self, suggestion_id: str, status: str) -> ManuscriptAssistSuggestionRecord:
        with connect(self.db_path) as connection:
            connection.execute(
                """
                UPDATE manuscript_assist_suggestions
                SET status = ?, updated_at = ?
                WHERE suggestion_id = ?
                """,
                (status, _now().isoformat(), suggestion_id),
            )
            connection.commit()
        return self.get_manuscript_assist_suggestion(suggestion_id)


class _AssistGateMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_manuscript_assist_gate_result(
        self,
        *,
        gate_result_id: str,
        assist_id: str,
        project_id: str,
        document_id: str,
        gate_name: str,
        passed: bool,
        severity: str,
        reasons: list[str] | None = None,
        created_at: datetime | None = None,
    ) -> ManuscriptAssistGateResultRecord:
        now = _now(created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO manuscript_assist_gate_results (
                    gate_result_id, assist_id, project_id, document_id, gate_name,
                    passed, severity, reasons_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(gate_result_id) DO UPDATE SET
                    assist_id = excluded.assist_id,
                    project_id = excluded.project_id,
                    document_id = excluded.document_id,
                    gate_name = excluded.gate_name,
                    passed = excluded.passed,
                    severity = excluded.severity,
                    reasons_json = excluded.reasons_json,
                    created_at = excluded.created_at
                """,
                (
                    gate_result_id,
                    assist_id,
                    project_id,
                    document_id,
                    gate_name,
                    1 if passed else 0,
                    severity,
                    _json_list(reasons),
                    now.isoformat(),
                ),
            )
            connection.commit()
        return self.get_manuscript_assist_gate_result(gate_result_id)



    def get_manuscript_assist_gate_result(self, gate_result_id: str) -> ManuscriptAssistGateResultRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM manuscript_assist_gate_results
                WHERE gate_result_id = ?
                """,
                (gate_result_id,),
            ).fetchone()
        if row is None:
            raise KeyError(gate_result_id)
        return _manuscript_assist_gate_result_row_to_record(row)



    def list_manuscript_assist_gate_results(self, assist_id: str) -> list[ManuscriptAssistGateResultRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM manuscript_assist_gate_results
                WHERE assist_id = ?
                ORDER BY created_at DESC
                """,
                (assist_id,),
            ).fetchall()
        return [_manuscript_assist_gate_result_row_to_record(row) for row in rows]
