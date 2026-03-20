from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from ..schemas.manifest import Manifest
from ..services.validation import ManifestValidationService
from .sqlite import connect, ensure_operations_db, ensure_project_db


def _utc_timestamp(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)


class ProjectRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)

    def sync_from_projects_dir(self, projects_dir: Path) -> None:
        projects_dir.mkdir(parents=True, exist_ok=True)
        for manifest_path in sorted(projects_dir.glob("*/manifest.json")):
            if manifest_path.is_file() and manifest_path.stat().st_size > 0:
                self.register_project_dir(manifest_path.parent)

    def register_project_dir(self, project_dir: Path) -> None:
        manifest_path = project_dir / "manifest.json"
        if not manifest_path.exists() or manifest_path.stat().st_size == 0:
            return
        manifest = ManifestValidationService.validate_file(manifest_path)
        database_path = project_dir / "bible.db"
        ensure_project_db(database_path)

        created_at = _utc_timestamp(manifest_path)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO projects (
                    project_id, project_name, manifest_path, db_path, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    project_name = excluded.project_name,
                    manifest_path = excluded.manifest_path,
                    db_path = excluded.db_path,
                    updated_at = excluded.updated_at
                """,
                (
                    manifest.project_id,
                    manifest.project_name,
                    str(manifest_path),
                    str(database_path),
                    created_at.isoformat(),
                    created_at.isoformat(),
                ),
            )
            for artifact_type, artifact_path in self._discover_artifacts(project_dir).items():
                timestamp = _utc_timestamp(artifact_path).isoformat()
                connection.execute(
                    """
                    INSERT INTO project_artifacts (
                        project_id, artifact_type, path, content_hash, size_bytes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, artifact_type) DO UPDATE SET
                        path = excluded.path,
                        content_hash = excluded.content_hash,
                        size_bytes = excluded.size_bytes,
                        updated_at = excluded.updated_at
                    """,
                    (
                        manifest.project_id,
                        artifact_type,
                        str(artifact_path),
                        self._hash_if_file(artifact_path),
                        artifact_path.stat().st_size if artifact_path.exists() else None,
                        timestamp,
                        timestamp,
                    ),
                )
            connection.commit()
        self._sync_project_db(database_path, manifest, project_dir)

    def get_artifact_path(self, project_id: str, artifact_type: str) -> Path | None:
        canonical = self._canonical_artifact_type(artifact_type)
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT path FROM project_artifacts WHERE project_id = ? AND artifact_type = ?",
                (project_id, canonical),
            ).fetchone()
        if row is None:
            return None
        return Path(row["path"])

    def _sync_project_db(self, db_path: Path, manifest: Manifest, project_dir: Path) -> None:
        with connect(db_path) as connection:
            for key, value in (("project_id", manifest.project_id), ("project_name", manifest.project_name)):
                connection.execute(
                    """
                    INSERT INTO project_metadata (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, value),
                )
            for artifact_type, artifact_path in self._discover_artifacts(project_dir).items():
                connection.execute(
                    """
                    INSERT INTO artifacts (artifact_type, path, updated_at) VALUES (?, ?, ?)
                    ON CONFLICT(artifact_type) DO UPDATE SET
                        path = excluded.path,
                        updated_at = excluded.updated_at
                    """,
                    (
                        artifact_type,
                        str(artifact_path),
                        _utc_timestamp(artifact_path).isoformat(),
                    ),
                )
            connection.commit()

    def _discover_artifacts(self, project_dir: Path) -> dict[str, Path]:
        artifacts: dict[str, Path] = {}
        for artifact_type, artifact_path in {
            "manifest": project_dir / "manifest.json",
            "sequence": project_dir / "sequences.json",
            "telemetry": project_dir / "telemetry.log",
            "structured_log": project_dir / "telemetry.jsonl",
        }.items():
            if artifact_path.exists():
                artifacts[artifact_type] = artifact_path
        for chapter_name in ("chapter.md", "chapter_001.md"):
            chapter_path = project_dir / chapter_name
            if chapter_path.exists():
                artifacts["chapter_1"] = chapter_path
                break
        exports_dir = project_dir / "exports"
        if exports_dir.exists():
            for export_path in sorted(exports_dir.glob("*")):
                if export_path.is_file():
                    artifacts[f"export:{export_path.name}"] = export_path
        return artifacts

    def _hash_if_file(self, artifact_path: Path) -> str | None:
        if not artifact_path.exists() or not artifact_path.is_file():
            return None
        return hashlib.sha256(artifact_path.read_bytes()).hexdigest()

    def _canonical_artifact_type(self, artifact_type: str) -> str:
        if artifact_type in {"chapter", "chapter-1", "chapter_1"}:
            return "chapter_1"
        if artifact_type in {"sequence", "sequences"}:
            return "sequence"
        return artifact_type
