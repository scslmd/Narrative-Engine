from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    json_object as _json_object,
    json_objects as _json_objects,
    now as _now,
)
from . import CanonGenerationPacketRecord, CanonGenerationRunRecord, GenerationGateResultRecord
from .converters import (
    _canon_generation_run_row_to_record, _canon_generation_packet_row_to_record,
    _generation_gate_result_row_to_record,
)

from ..sqlite import connect


class _GenerationRunMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_canon_generation_run(
        self,
        *,
        generation_id: str,
        source_project_id: str,
        target_project_id: str,
        mode: str,
        request_json: Mapping[str, Any],
        canon_scope_json: Mapping[str, Any],
        canon_policy_json: Mapping[str, Any],
        status: str,
        gate_status: str = "pending",
        warnings: list[str] | None = None,
        created_job_ids: list[str] | None = None,
        created_artifacts: Sequence[Mapping[str, Any]] | None = None,
        idempotency_key: str | None = None,
        request_hash: str = "",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> CanonGenerationRunRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            if idempotency_key:
                existing = connection.execute(
                    """
                    SELECT generation_id, request_hash
                    FROM canon_generation_runs
                    WHERE source_project_id = ? AND idempotency_key = ?
                    """,
                    (source_project_id, idempotency_key),
                ).fetchone()
                if existing is not None and existing["request_hash"] != request_hash:
                    raise ValueError("idempotency key conflict: request hash mismatch")
            connection.execute(
                """
                INSERT INTO canon_generation_runs (
                    generation_id, source_project_id, target_project_id, mode,
                    request_json, canon_scope_json, canon_policy_json,
                    status, gate_status, warnings_json, created_job_ids_json, created_artifacts_json,
                    idempotency_key, request_hash, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(generation_id) DO UPDATE SET
                    source_project_id = excluded.source_project_id,
                    target_project_id = excluded.target_project_id,
                    mode = excluded.mode,
                    request_json = excluded.request_json,
                    canon_scope_json = excluded.canon_scope_json,
                    canon_policy_json = excluded.canon_policy_json,
                    status = excluded.status,
                    gate_status = excluded.gate_status,
                    warnings_json = excluded.warnings_json,
                    created_job_ids_json = excluded.created_job_ids_json,
                    created_artifacts_json = excluded.created_artifacts_json,
                    idempotency_key = excluded.idempotency_key,
                    request_hash = excluded.request_hash,
                    updated_at = excluded.updated_at
                """,
                (
                    generation_id,
                    source_project_id,
                    target_project_id,
                    mode,
                    _json_object(request_json),
                    _json_object(canon_scope_json),
                    _json_object(canon_policy_json),
                    status,
                    gate_status,
                    _json_list(warnings),
                    _json_list(created_job_ids),
                    _json_objects(created_artifacts),
                    idempotency_key,
                    request_hash,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_canon_generation_run(generation_id)



    def get_canon_generation_run(self, generation_id: str) -> CanonGenerationRunRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM canon_generation_runs
                WHERE generation_id = ?
                """,
                (generation_id,),
            ).fetchone()
        if row is None:
            raise KeyError(generation_id)
        return _canon_generation_run_row_to_record(row)



    def list_canon_generation_runs(self, project_id: str, *, role: str = "either") -> list[CanonGenerationRunRecord]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_role = self._normalize_text(role, field_name="role").lower()
        if normalized_role not in {"source", "target", "either"}:
            raise ValueError("role must be one of: source, target, either")
        if normalized_role == "source":
            where_clause = "source_project_id = ?"
            params: tuple[str, ...] = (normalized_project_id,)
        elif normalized_role == "target":
            where_clause = "target_project_id = ?"
            params = (normalized_project_id,)
        else:
            where_clause = "(source_project_id = ? OR target_project_id = ?)"
            params = (normalized_project_id, normalized_project_id)
        with connect(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM canon_generation_runs
                WHERE {where_clause}
                ORDER BY created_at DESC
                """,
                params,
            ).fetchall()
        return [_canon_generation_run_row_to_record(row) for row in rows]


class _GenerationPacketMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_canon_generation_packet(
        self,
        *,
        packet_id: str,
        generation_id: str,
        source_project_id: str,
        target_project_id: str,
        packet_json: Mapping[str, Any],
        source_hashes_json: Mapping[str, str],
        prompt_budget_json: Mapping[str, Any],
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> CanonGenerationPacketRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO canon_generation_packets (
                    packet_id, generation_id, source_project_id, target_project_id,
                    packet_json, source_hashes_json, prompt_budget_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(packet_id) DO UPDATE SET
                    generation_id = excluded.generation_id,
                    source_project_id = excluded.source_project_id,
                    target_project_id = excluded.target_project_id,
                    packet_json = excluded.packet_json,
                    source_hashes_json = excluded.source_hashes_json,
                    prompt_budget_json = excluded.prompt_budget_json,
                    updated_at = excluded.updated_at
                """,
                (
                    packet_id,
                    generation_id,
                    source_project_id,
                    target_project_id,
                    _json_object(packet_json),
                    _json_object(source_hashes_json),
                    _json_object(prompt_budget_json),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_canon_generation_packet(packet_id)



    def get_canon_generation_packet(self, packet_id: str) -> CanonGenerationPacketRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM canon_generation_packets
                WHERE packet_id = ?
                """,
                (packet_id,),
            ).fetchone()
        if row is None:
            raise KeyError(packet_id)
        return _canon_generation_packet_row_to_record(row)



    def list_canon_generation_packets_for_generation(
        self,
        generation_id: str,
    ) -> list[CanonGenerationPacketRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM canon_generation_packets
                WHERE generation_id = ?
                ORDER BY created_at DESC
                """,
                (generation_id,),
            ).fetchall()
        return [_canon_generation_packet_row_to_record(row) for row in rows]


class _GateResultMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_generation_gate_result(
        self,
        *,
        gate_result_id: str,
        generation_id: str,
        project_id: str,
        artifact_kind: str,
        artifact_id: str,
        gate_name: str,
        passed: bool,
        severity: str,
        reasons: list[str] | None = None,
        repair_attempted: bool = False,
        repair_job_id: str | None = None,
        created_at: datetime | None = None,
    ) -> GenerationGateResultRecord:
        now = _now(created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO generation_gate_results (
                    gate_result_id, generation_id, project_id, artifact_kind, artifact_id,
                    gate_name, passed, severity, reasons_json, repair_attempted, repair_job_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(gate_result_id) DO UPDATE SET
                    generation_id = excluded.generation_id,
                    project_id = excluded.project_id,
                    artifact_kind = excluded.artifact_kind,
                    artifact_id = excluded.artifact_id,
                    gate_name = excluded.gate_name,
                    passed = excluded.passed,
                    severity = excluded.severity,
                    reasons_json = excluded.reasons_json,
                    repair_attempted = excluded.repair_attempted,
                    repair_job_id = excluded.repair_job_id,
                    created_at = excluded.created_at
                """,
                (
                    gate_result_id,
                    generation_id,
                    project_id,
                    artifact_kind,
                    artifact_id,
                    gate_name,
                    1 if passed else 0,
                    severity,
                    _json_list(reasons),
                    1 if repair_attempted else 0,
                    repair_job_id,
                    now.isoformat(),
                ),
            )
            connection.commit()
        return self.get_generation_gate_result(gate_result_id)



    def get_generation_gate_result(self, gate_result_id: str) -> GenerationGateResultRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM generation_gate_results
                WHERE gate_result_id = ?
                """,
                (gate_result_id,),
            ).fetchone()
        if row is None:
            raise KeyError(gate_result_id)
        return _generation_gate_result_row_to_record(row)



    def list_generation_gate_results(self, generation_id: str) -> list[GenerationGateResultRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM generation_gate_results
                WHERE generation_id = ?
                ORDER BY created_at DESC
                """,
                (generation_id,),
            ).fetchall()
        return [_generation_gate_result_row_to_record(row) for row in rows]
