from __future__ import annotations

from datetime import datetime
import json
from .shared_utils import (
    json_list as _json_list,
    now as _now,
)
from . import (
    ExportStatusRecord,
    PolishReportRecord,
)
from .converters import (
    _export_status_row_to_record,
    _polish_report_row_to_record,
)

from ..sqlite import connect


class _PolishMixin:

    def __init__(self, db_path):

        self.db_path = db_path


    def save_polish_report(
        self,
        *,
        report_id: str,
        project_id: str,
        document_id: str,
        readability_score: float,
        word_count: int,
        sentence_count: int,
        avg_sentence_length: float,
        passive_voice_count: int,
        repetitive_words: list[str],
        style_issues: list[str],
        generated_at: datetime,
    ) -> PolishReportRecord:
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO polish_reports (
                    report_id, project_id, document_id, readability_score, word_count, sentence_count,
                    avg_sentence_length, passive_voice_count, repetitive_words_json, style_issues_json, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    project_id,
                    document_id,
                    float(readability_score),
                    int(word_count),
                    int(sentence_count),
                    float(avg_sentence_length),
                    int(passive_voice_count),
                    _json_list(repetitive_words),
                    _json_list(style_issues),
                    generated_at.isoformat(),
                ),
            )
            connection.commit()
        return self.get_polish_report(report_id)


    def get_polish_report(self, report_id: str) -> PolishReportRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM polish_reports
                WHERE report_id = ?
                """,
                (report_id,),
            ).fetchone()
        if row is None:
            raise KeyError(report_id)
        return _polish_report_row_to_record(row)


    def list_polish_reports(self, project_id: str, document_id: str | None = None) -> list[PolishReportRecord]:
        with connect(self.db_path) as connection:
            if document_id is not None:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM polish_reports
                    WHERE project_id = ? AND document_id = ?
                    ORDER BY generated_at DESC
                    """,
                    (project_id, document_id),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM polish_reports
                    WHERE project_id = ?
                    ORDER BY generated_at DESC
                    """,
                    (project_id,),
                ).fetchall()
        return [_polish_report_row_to_record(row) for row in rows]


class _ExportStatusMixin:

    def __init__(self, db_path):

        self.db_path = db_path


    def create_export_status(
        self,
        *,
        export_id: str,
        project_id: str,
        document_id: str,
        format: str,
        status: str = "queued",
        artifact_path: str | None = None,
        error_message: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ExportStatusRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO export_statuses (
                    export_id, project_id, document_id, format, status, artifact_path, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    export_id,
                    project_id,
                    document_id,
                    format,
                    status,
                    artifact_path,
                    error_message,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_export_status(export_id)


    def update_export_status(
        self,
        export_id: str,
        *,
        status: str | None = None,
        artifact_path: str | None = None,
        error_message: str | None = None,
        updated_at: datetime | None = None,
    ) -> ExportStatusRecord:
        updates = []
        params = []
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if artifact_path is not None:
            updates.append("artifact_path = ?")
            params.append(artifact_path)
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)
        if not updates:
            return self.get_export_status(export_id)
        updated = _now(updated_at)
        updates.append("updated_at = ?")
        params.append(updated.isoformat())
        params.append(export_id)
        with connect(self.db_path) as connection:
            connection.execute(
                f"""
                UPDATE export_statuses
                SET {', '.join(updates)}
                WHERE export_id = ?
                """,
                params,
            )
            connection.commit()
        return self.get_export_status(export_id)


    def get_export_status(self, export_id: str) -> ExportStatusRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM export_statuses
                WHERE export_id = ?
                """,
                (export_id,),
            ).fetchone()
        if row is None:
            raise KeyError(export_id)
        return _export_status_row_to_record(row)
