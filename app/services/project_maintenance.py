from __future__ import annotations

import json
import logging
import os
import shutil
import threading
from pathlib import Path

from ..persistence.projects import ProjectRepository
from ..persistence.sqlite import connect
from ..schemas.projects import (
    AuditLogTruncationRequest,
    AuditLogTruncationResponse,
    DatabaseCompactionResponse,
    MaintenanceCleanupRequest,
    MaintenanceCleanupResponse,
    MaintenanceScanResponse,
    MaintenanceSummary,
    OrphanInfo,
    ProjectDeletionResponse,
)
from ..settings import Settings

logger = logging.getLogger(__name__)


class ProjectMaintenanceError(Exception):
    pass


class ProjectMaintenanceService:
    _lock = threading.Lock()

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._repository = ProjectRepository(self._db_path)

    @property
    def _projects_dir(self) -> Path:
        return self._settings.projects_dir

    @property
    def _db_path(self) -> Path:
        return self._settings.operations_db_path

    @property
    def _audit_log_path(self) -> Path:
        return self._settings.audit_log_path

    @property
    def _checker_reports_dir(self) -> Path:
        return self._settings.role_model_reports_dir

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def scan_orphans(self) -> MaintenanceScanResponse:
        with self._lock:
            disk_projects = self._list_disk_projects()
            db_projects = self._list_db_projects()

            disk_ids = set(disk_projects.keys())
            db_ids = set(db_projects.keys())

            orphaned_dirs: list[OrphanInfo] = []
            for pid, info in sorted(disk_projects.items()):
                if not info["has_manifest"]:
                    orphaned_dirs.append(
                        OrphanInfo(
                            project_id=pid,
                            project_name=info.get("name"),
                            kind="orphaned_dir",
                            size_bytes=info["size"],
                        )
                    )

            db_only: list[OrphanInfo] = []
            for pid in sorted(db_ids - disk_ids):
                db_only.append(
                    OrphanInfo(
                        project_id=pid,
                        project_name=db_projects[pid],
                        kind="db_only",
                        size_bytes=0,
                    )
                )

            disk_only: list[OrphanInfo] = []
            for pid in sorted(disk_ids - db_ids):
                info = disk_projects[pid]
                disk_only.append(
                    OrphanInfo(
                        project_id=pid,
                        project_name=info.get("name"),
                        kind="disk_only",
                        size_bytes=info["size"],
                    )
                )

            summary = self._compute_summary()

        return MaintenanceScanResponse(
            orphaned_dirs=orphaned_dirs,
            db_only=db_only,
            disk_only=disk_only,
            summary=summary,
        )

    def cleanup(self, project_ids: list[str]) -> MaintenanceCleanupResponse:
        with self._lock:
            removed = 0
            errors: list[dict[str, str]] = []

            for pid in project_ids:
                try:
                    self._remove_single(pid)
                    removed += 1
                except Exception as exc:
                    logger.warning("Failed to clean up %s: %s", pid, exc)
                    errors.append({"project_id": pid, "error": str(exc)})

        return MaintenanceCleanupResponse(removed=removed, errors=errors)

    def delete_project(self, project_id: str) -> ProjectDeletionResponse:
        with self._lock:
            # Verify project exists
            projection = self._repository.get_project_projection(project_id)
            if projection is None:
                raise ProjectMaintenanceError(f"Project not found: {project_id}")

            # Step 1: Delete execution history
            history_removed = self._repository.delete_project_history(project_id)

            # Step 2: Remove checker reports
            self._remove_checker_reports_for_project(project_id)

            # Step 3: Delete project row from DB
            self._repository.delete_project(project_id)

            # Step 4: Remove disk directory
            project_dir = self._projects_dir / project_id
            if project_dir.exists():
                shutil.rmtree(project_dir, ignore_errors=True)

        return ProjectDeletionResponse(
            deleted=True,
            project_id=project_id,
            history_removed=history_removed,
        )

    def truncate_audit_log(
        self, retain_lines: int | None = None
    ) -> AuditLogTruncationResponse:
        with self._lock:
            keep = retain_lines if retain_lines is not None else self._settings.audit_log_retain_lines
            log_path = self._audit_log_path

            if not log_path.exists():
                return AuditLogTruncationResponse(truncated=0, retained=0)

            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            total = len(lines)
            retained_lines = lines[-keep:] if total > keep else lines
            truncated = total - len(retained_lines)

            tmp_path = log_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.writelines(retained_lines)

            os.replace(str(tmp_path), str(log_path))

        return AuditLogTruncationResponse(truncated=truncated, retained=len(retained_lines))

    def compact_database(self) -> DatabaseCompactionResponse:
        with self._lock:
            before_bytes = self._dir_size(self._db_path)

            with connect(self._db_path) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                conn.commit()

            after_bytes = self._dir_size(self._db_path)

        return DatabaseCompactionResponse(
            before_bytes=before_bytes,
            after_bytes=after_bytes,
        )

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #

    def _list_disk_projects(self) -> dict[str, dict]:
        result: dict[str, dict] = {}
        if not self._projects_dir.exists():
            return result

        for entry in sorted(self._projects_dir.iterdir()):
            if not entry.is_dir():
                continue
            manifest_path = entry / "manifest.json"
            name = None
            has_manifest = manifest_path.exists() and manifest_path.stat().st_size > 0
            if has_manifest:
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    name = data.get("project_name")
                except Exception:
                    pass
            size = self._dir_size(entry)
            result[entry.name] = {
                "has_manifest": has_manifest,
                "name": name,
                "size": size,
            }
        return result

    def _list_db_projects(self) -> dict[str, str]:
        result: dict[str, str] = {}
        with connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT project_id, project_name FROM projects ORDER BY project_id"
            ).fetchall()
        for row in rows:
            result[row["project_id"]] = row["project_name"]
        return result

    def _compute_summary(self) -> MaintenanceSummary:
        audit_lines = 0
        if self._audit_log_path.exists():
            with open(self._audit_log_path, "r", encoding="utf-8") as f:
                audit_lines = sum(1 for _ in f)

        db_size = self._dir_size(self._db_path)

        checker_files = 0
        if self._checker_reports_dir.exists():
            checker_files = sum(1 for _ in self._checker_reports_dir.rglob("*") if _.is_file())

        with connect(self._db_path) as conn:
            total_jobs = conn.execute(
                "SELECT COUNT(*) AS cnt FROM jobs"
            ).fetchone()["cnt"]
            total_checker_runs = conn.execute(
                "SELECT COUNT(*) AS cnt FROM checker_runs"
            ).fetchone()["cnt"]

        return MaintenanceSummary(
            audit_log_lines=audit_lines,
            audit_log_retain_lines=self._settings.audit_log_retain_lines,
            database_size_bytes=db_size,
            checker_report_files=checker_files,
            total_jobs=total_jobs,
            total_checker_runs=total_checker_runs,
        )

    def _remove_single(self, project_id: str) -> None:
        disk_dir = self._projects_dir / project_id
        projection = self._repository.get_project_projection(project_id)

        if projection is None:
            if disk_dir.exists():
                # Orphaned dir: exists on disk but not in DB
                shutil.rmtree(disk_dir, ignore_errors=True)
            else:
                # DB-only orphan: try removing from DB (no-op if not there)
                with connect(self._db_path) as conn:
                    conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
                    conn.commit()
        elif not disk_dir.exists():
            # DB entry without disk directory
            with connect(self._db_path) as conn:
                conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
                conn.commit()
        else:
            # Full removal: both DB and disk exist
            self._repository.delete_project_history(project_id)
            self._remove_checker_reports_for_project(project_id)
            self._repository.delete_project(project_id)
            shutil.rmtree(disk_dir, ignore_errors=True)

    def _remove_checker_reports_for_project(self, project_id: str) -> int:
        removed = 0
        if not self._checker_reports_dir.exists():
            return removed

        for run_dir in self._checker_reports_dir.iterdir():
            if not run_dir.is_dir():
                continue
            metadata_path = run_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    if meta.get("project_id") == project_id:
                        shutil.rmtree(run_dir, ignore_errors=True)
                        removed += 1
                except Exception:
                    pass
        return removed

    @staticmethod
    def _dir_size(path: Path) -> int:
        if path.is_file():
            return path.stat().st_size
        if not path.exists():
            return 0
        total = 0
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
        return total
