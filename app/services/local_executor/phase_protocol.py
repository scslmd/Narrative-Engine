from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from ...persistence.steps import stable_hash_payload
from .helpers import utcnow as _utcnow

class _PhaseProtocolMixin:

    def _finalize_generated_job_phase(
        self,
        *,
        job_id: UUID,
        current_phase: str,
        attempt: dict[str, Any],
        project_id: str,
        step_name: str,
        detail: str,
        model_id: str | None,
        backend_name: str,
        backend_version: str | None,
        input_payload: object,
        output_payload: object,
        prompt_payload: object,
        input_artifact_refs: list[str],
        output_artifact_refs: list[str],
        started_at: datetime,
        finished_at: datetime,
        finish_reason: str,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        total_tokens: int | None,
        artifact_role: str,
        artifact_kind: str,
        output_path: Path,
        staged_output_path: Path,
        content_hash_source: str,
        source_content_hashes: list[str],
        project_artifact_name: str,
    ) -> None:
        step_record_id: int | None = None
        lineage_record_id: int | None = None
        backup_output_path: Path | None = None
        try:
            backup_output_path = self._publish_staged_output(
                staged_output_path=staged_output_path,
                output_path=output_path,
            )
            step_record_id = self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name=step_name,
                step_index=1,
                state="COMPLETED",
                project_id=project_id,
                model_id=model_id,
                critic_profile=None,
                backend_name=backend_name,
                backend_version=backend_version,
                input_hash=stable_hash_payload(input_payload) if input_payload else None,
                output_hash=stable_hash_payload(output_payload) if output_payload else None,
                prompt_hash=stable_hash_payload(prompt_payload) if prompt_payload else None,
                input_artifact_refs=input_artifact_refs,
                output_artifact_refs=output_artifact_refs,
                started_at=started_at,
                finished_at=finished_at,
                finish_reason=finish_reason,
                error_code=None,
                error_category=None,
                executor_id="job-worker-local",
                lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                created_at=started_at,
                updated_at=finished_at,
            )
            lineage_record_id = self._step_records.create_lineage_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name=step_name,
                project_id=project_id,
                artifact_role=artifact_role,
                artifact_kind=artifact_kind,
                path=str(output_path),
                content_hash=content_hash_source,
                status="CANONICAL",
                validation_state="PASSED",
                produced_at=finished_at,
                registered_at=finished_at,
                supersedes_artifact_lineage_id=None,
                source_artifact_refs=input_artifact_refs,
                source_content_hashes=source_content_hashes,
                output_of_step_record_id=step_record_id,
            )
            self._project_service.register_generated_artifact(
                project_id,
                project_artifact_name,
                output_path,
            )
        except Exception as exc:
            failure_finished_at = _utcnow()
            if lineage_record_id is not None:
                try:
                    self._step_records.delete_lineage_record(artifact_lineage_id=lineage_record_id)
                except Exception:
                    pass
            self._restore_published_output(
                output_path=output_path,
                staged_output_path=staged_output_path,
                backup_output_path=backup_output_path,
            )
            if step_record_id is not None:
                try:
                    self._step_records.mark_step_record_failed(
                        step_record_id=step_record_id,
                        finish_reason="persistence_error",
                        error_code=str(exc),
                        error_category="persistence",
                        finished_at=failure_finished_at,
                    )
                except Exception:
                    pass
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                current_step=step_name,
                error=str(exc),
                error_category="persistence",
                detail=f"{step_name.capitalize()} phase persistence failed.",
                finish_reason="persistence_error",
                failure_stage="persistence",
                retryable=False,
            )
            if step_record_id is None:
                try:
                    self._step_records.create_step_record(
                        logical_run_id=str(attempt["logical_run_id"]),
                        run_id=job_id,
                        run_kind="pipeline_job",
                        attempt_number=int(attempt["attempt_number"]),
                        step_name=step_name,
                        step_index=1,
                        state="FAILED",
                        project_id=project_id,
                        model_id=model_id,
                        critic_profile=None,
                        backend_name=backend_name,
                        backend_version=backend_version,
                        input_hash=stable_hash_payload(input_payload) if input_payload else None,
                        output_hash=stable_hash_payload({"error": str(exc), "artifact_path": str(output_path)}),
                        prompt_hash=stable_hash_payload(prompt_payload) if prompt_payload else None,
                        input_artifact_refs=input_artifact_refs,
                        output_artifact_refs=[],
                        started_at=started_at,
                        finished_at=failure_finished_at,
                        finish_reason="persistence_error",
                        error_code=str(exc),
                        error_category="persistence",
                        executor_id="job-worker-local",
                        lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                    )
                except Exception:
                    pass
            return

        self._finalize_published_output(
            staged_output_path=staged_output_path,
            backup_output_path=backup_output_path,
        )

        self._job_manager.update_job(
            job_id,
            status="COMPLETED",
            current_phase=current_phase,
            current_step=step_name,
            detail=detail,
            progress_current=1,
            progress_total=1,
            finish_reason=finish_reason,
        )