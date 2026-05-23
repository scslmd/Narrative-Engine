from pathlib import Path
from typing import Any
from uuid import UUID

from ...services.file_permissions import FilePermissionValidator
from .helpers import upstream_artifact_sources as _upstream_artifact_sources

class _ArtifactIOMixin:

    def _write_staged_output(self, *, output_path: Path, output_text: str) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        validator = FilePermissionValidator(strict=True)
        validator.validate_directory(output_path.parent, check_world_writable=True)
        
        staged_output_path = output_path.with_name(f"{output_path.name}.staged")
        staged_output_path.write_text(output_text, encoding="utf-8")
        return staged_output_path
    def _publish_staged_output(self, *, staged_output_path: Path, output_path: Path) -> Path | None:
        backup_output_path: Path | None = None
        if output_path.exists():
            backup_output_path = output_path.with_name(f"{output_path.name}.bak")
            if backup_output_path.exists():
                backup_output_path.unlink()
            output_path.replace(backup_output_path)
        staged_output_path.replace(output_path)
        return backup_output_path
    def _restore_published_output(
        self,
        *,
        output_path: Path,
        staged_output_path: Path,
        backup_output_path: Path | None,
    ) -> None:
        try:
            if output_path.exists():
                output_path.unlink()
        except Exception:
            pass
        try:
            if backup_output_path is not None and backup_output_path.exists():
                backup_output_path.replace(output_path)
        except Exception:
            pass
        try:
            if staged_output_path.exists():
                staged_output_path.unlink()
        except Exception:
            pass
    def _finalize_published_output(
        self,
        *,
        staged_output_path: Path,
        backup_output_path: Path | None,
    ) -> None:
        if staged_output_path.exists():
            staged_output_path.unlink()
        if backup_output_path is not None and backup_output_path.exists():
            backup_output_path.unlink()
    def _read_optional_artifact(self, project_id: str, artifact_name: str) -> str | None:
        try:
            content = self._project_service.read_artifact(project_id, artifact_name).content
        except FileNotFoundError:
            return None
        if not content.strip():
            return None
        return content
    def _resolve_runtime_artifact_inputs(
        self,
        *,
        job_id: UUID,
        attempt: dict[str, Any],
        project_id: str,
        step_name: str,
    ) -> dict[str, str]:
        attempt_number = int(attempt["attempt_number"])
        existing = self._step_records.list_runtime_artifact_selections(
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=attempt_number,
            step_name=step_name,
        )
        if existing:
            return {str(row["artifact_role"]): str(row["selected_content"]) for row in existing}

        resolved: dict[str, str] = {}
        for artifact_role, project_artifact_name in _upstream_artifact_sources(step_name):
            content = self._read_optional_artifact(project_id, project_artifact_name)
            if content is None:
                continue
            lineage = self._step_records.get_latest_canonical_artifact(
                project_id=project_id,
                artifact_role=artifact_role,
            )
            self._step_records.create_runtime_artifact_selection(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=attempt_number,
                step_name=step_name,
                project_id=project_id,
                artifact_role=artifact_role,
                selected_artifact_lineage_id=(
                    int(lineage["artifact_lineage_id"])
                    if lineage is not None and lineage.get("artifact_lineage_id") is not None
                    else None
                ),
                selected_path=str(lineage["path"]) if lineage is not None and lineage.get("path") is not None else None,
                selected_content=content,
            )
            resolved[artifact_role] = content
        return resolved