from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from ..persistence import ArtifactLineageRepository, StepRecordRepository
from ..persistence.steps import stable_hash_payload, stable_hash_text
from ..settings import settings


class StepRecordService:
    def __init__(self, db_path: Path | None = None) -> None:
        operations_db_path = db_path or settings.operations_db_path
        self._steps = StepRecordRepository(operations_db_path)
        self._lineage = ArtifactLineageRepository(operations_db_path)

    def create_step_record(
        self,
        *,
        logical_run_id: str,
        run_id: UUID,
        run_kind: str,
        attempt_number: int,
        step_name: str,
        step_index: int,
        state: str,
        project_id: str | None,
        model_id: str | None,
        critic_profile: str | None,
        backend_name: str | None,
        backend_version: str | None,
        input_payload: object | None,
        output_payload: object | None,
        prompt_payload: object | None,
        input_artifact_refs: list[str],
        output_artifact_refs: list[str],
        started_at: datetime | None,
        finished_at: datetime | None,
        finish_reason: str | None,
        error_code: str | None,
        error_category: str | None,
        executor_id: str | None,
        lease_owner: str | None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> int:
        now = finished_at or started_at or datetime.now(timezone.utc)
        duration_seconds = None
        if started_at is not None and finished_at is not None:
            duration_seconds = round((finished_at - started_at).total_seconds(), 3)
        return self._steps.create_step_record(
            logical_run_id=logical_run_id,
            run_id=str(run_id),
            run_kind=run_kind,
            attempt_number=attempt_number,
            step_name=step_name,
            step_index=step_index,
            state=state,
            project_id=project_id,
            model_id=model_id,
            critic_profile=critic_profile,
            backend_name=backend_name,
            backend_version=backend_version,
            input_hash=stable_hash_payload(input_payload) if input_payload is not None else None,
            output_hash=stable_hash_payload(output_payload) if output_payload is not None else None,
            prompt_hash=stable_hash_payload(prompt_payload) if prompt_payload is not None else None,
            input_artifact_refs=input_artifact_refs,
            output_artifact_refs=output_artifact_refs,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_seconds,
            finish_reason=finish_reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            error_code=error_code,
            error_category=error_category,
            executor_id=executor_id,
            lease_owner=lease_owner,
            created_at=now,
            updated_at=now,
        )

    def create_lineage_record(
        self,
        *,
        logical_run_id: str,
        run_id: UUID,
        run_kind: str,
        attempt_number: int,
        step_name: str,
        project_id: str | None,
        artifact_role: str,
        artifact_kind: str,
        path: str,
        content_hash_source: str | bytes | None,
        status: str,
        validation_state: str,
        produced_at: datetime,
        registered_at: datetime | None,
        supersedes_artifact_lineage_id: int | None,
        source_artifact_refs: list[str],
        source_content_hashes: list[str],
        output_of_step_record_id: int,
    ) -> int:
        content_hash = None
        if isinstance(content_hash_source, bytes):
            content_hash = stable_hash_text(content_hash_source.decode("utf-8", errors="replace"))
        elif isinstance(content_hash_source, str):
            content_hash = stable_hash_text(content_hash_source)
        return self._lineage.create_lineage_record(
            logical_run_id=logical_run_id,
            run_id=str(run_id),
            run_kind=run_kind,
            attempt_number=attempt_number,
            step_name=step_name,
            project_id=project_id,
            artifact_role=artifact_role,
            artifact_kind=artifact_kind,
            path=path,
            content_hash=content_hash,
            status=status,
            validation_state=validation_state,
            produced_at=produced_at,
            registered_at=registered_at,
            supersedes_artifact_lineage_id=supersedes_artifact_lineage_id,
            source_artifact_refs=source_artifact_refs,
            source_content_hashes=source_content_hashes,
            output_of_step_record_id=output_of_step_record_id,
        )

    def list_step_records(self, *, run_id: UUID, run_kind: str, attempt_number: int | None = None) -> list[dict[str, object]]:
        return self._steps.list_for_run(run_id=str(run_id), run_kind=run_kind, attempt_number=attempt_number)

    def list_artifact_lineage(self, *, run_id: UUID, run_kind: str, attempt_number: int | None = None) -> list[dict[str, object]]:
        return self._lineage.list_for_run(run_id=str(run_id), run_kind=run_kind, attempt_number=attempt_number)
