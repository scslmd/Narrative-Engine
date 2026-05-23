from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    now as _now,
)
from . import CheckerFindingRecord, InspectRunLinkRecord, ReviewDecisionRecord
from .converters import (
    _checker_finding_row_to_record, _review_decision_row_to_record,
    _inspect_run_link_row_to_record,
)

from ..sqlite import connect


class _CheckerFindingMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_checker_finding(
        self,
        *,
        finding_id: str,
        project_id: str,
        source_object_id: str,
        source_object_kind: str,
        severity: str,
        summary: str,
        details: str | None = None,
        source_context: Sequence[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> CheckerFindingRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO checker_findings (
                    finding_id, project_id, source_object_id, source_object_kind, severity, summary, details,
                    source_context_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(finding_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    source_object_id = excluded.source_object_id,
                    source_object_kind = excluded.source_object_kind,
                    severity = excluded.severity,
                    summary = excluded.summary,
                    details = excluded.details,
                    source_context_json = excluded.source_context_json,
                    updated_at = excluded.updated_at
                """,
                (
                    finding_id,
                    project_id,
                    source_object_id,
                    source_object_kind,
                    severity,
                    summary,
                    details,
                    _json_list(list(source_context or [])),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_checker_finding(finding_id)



    def get_checker_finding(self, finding_id: str) -> CheckerFindingRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM checker_findings
                WHERE finding_id = ?
                """,
                (finding_id,),
            ).fetchone()
        if row is None:
            raise KeyError(finding_id)
        return _checker_finding_row_to_record(row)



    def list_checker_findings(self, project_id: str) -> list[CheckerFindingRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM checker_findings
                WHERE project_id = ?
                ORDER BY created_at ASC, finding_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_checker_finding_row_to_record(row) for row in rows]



    def list_checker_findings_for_source(self, project_id: str, *, source_object_kind: str, source_object_id: str) -> list[CheckerFindingRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM checker_findings
                WHERE project_id = ? AND source_object_kind = ? AND source_object_id = ?
                ORDER BY created_at ASC, finding_id ASC
                """,
                (project_id, source_object_kind, source_object_id),
            ).fetchall()
        return [_checker_finding_row_to_record(row) for row in rows]


class _ReviewDecisionMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_review_decision(
        self,
        *,
        decision_id: str,
        project_id: str,
        target_id: str,
        target_kind: str,
        decision: str,
        notes: str | None = None,
        source_context: Sequence[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ReviewDecisionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO review_decisions (
                    decision_id, project_id, target_id, target_kind, decision, notes, source_context_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(decision_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    target_id = excluded.target_id,
                    target_kind = excluded.target_kind,
                    decision = excluded.decision,
                    notes = excluded.notes,
                    source_context_json = excluded.source_context_json,
                    updated_at = excluded.updated_at
                """,
                (
                    decision_id,
                    project_id,
                    target_id,
                    target_kind,
                    decision,
                    notes,
                    _json_list(list(source_context or [])),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_review_decision(decision_id)



    def get_review_decision(self, decision_id: str) -> ReviewDecisionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM review_decisions
                WHERE decision_id = ?
                """,
                (decision_id,),
            ).fetchone()
        if row is None:
            raise KeyError(decision_id)
        return _review_decision_row_to_record(row)



    def list_review_decisions(self, project_id: str) -> list[ReviewDecisionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM review_decisions
                WHERE project_id = ?
                ORDER BY created_at ASC, decision_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_review_decision_row_to_record(row) for row in rows]



    def list_review_decisions_for_target(self, project_id: str, *, target_kind: str, target_id: str) -> list[ReviewDecisionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM review_decisions
                WHERE project_id = ? AND target_kind = ? AND target_id = ?
                ORDER BY created_at ASC, decision_id ASC
                """,
                (project_id, target_kind, target_id),
            ).fetchall()
        return [_review_decision_row_to_record(row) for row in rows]


class _InspectLinkMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_inspect_run_link(
        self,
        *,
        link_id: str,
        project_id: str,
        object_kind: str,
        object_id: str,
        logical_run_id: str,
        run_id: str,
        run_kind: str,
        attempt_number: int | None = None,
        label: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> InspectRunLinkRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO inspect_run_links (
                    link_id, project_id, object_kind, object_id, logical_run_id, run_id, run_kind,
                    attempt_number, label, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(link_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    object_kind = excluded.object_kind,
                    object_id = excluded.object_id,
                    logical_run_id = excluded.logical_run_id,
                    run_id = excluded.run_id,
                    run_kind = excluded.run_kind,
                    attempt_number = excluded.attempt_number,
                    label = excluded.label,
                    updated_at = excluded.updated_at
                """,
                (
                    link_id,
                    project_id,
                    object_kind,
                    object_id,
                    logical_run_id,
                    run_id,
                    run_kind,
                    attempt_number,
                    label,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_inspect_run_link(link_id)



    def get_inspect_run_link(self, link_id: str) -> InspectRunLinkRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM inspect_run_links
                WHERE link_id = ?
                """,
                (link_id,),
            ).fetchone()
        if row is None:
            raise KeyError(link_id)
        return _inspect_run_link_row_to_record(row)



    def list_inspect_run_links(self, project_id: str) -> list[InspectRunLinkRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM inspect_run_links
                WHERE project_id = ?
                ORDER BY created_at ASC, link_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_inspect_run_link_row_to_record(row) for row in rows]



    def list_inspect_run_links_for_object(self, project_id: str, *, object_kind: str, object_id: str) -> list[InspectRunLinkRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM inspect_run_links
                WHERE project_id = ? AND object_kind = ? AND object_id = ?
                ORDER BY created_at ASC, link_id ASC
                """,
                (project_id, object_kind, object_id),
            ).fetchall()
        return [_inspect_run_link_row_to_record(row) for row in rows]



    def list_inspect_run_links_for_run(self, project_id: str, *, run_id: str) -> list[InspectRunLinkRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM inspect_run_links
                WHERE project_id = ? AND run_id = ?
                ORDER BY created_at ASC, link_id ASC
                """,
                (project_id, run_id),
            ).fetchall()
        return [_inspect_run_link_row_to_record(row) for row in rows]



    def list_inspect_run_links_for_logical_run(self, project_id: str, *, logical_run_id: str) -> list[InspectRunLinkRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM inspect_run_links
                WHERE project_id = ? AND logical_run_id = ?
                ORDER BY created_at ASC, link_id ASC
                """,
                (project_id, logical_run_id),
            ).fetchall()
        return [_inspect_run_link_row_to_record(row) for row in rows]
