from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ..schemas.manifest import Manifest
from .sqlite import connect, ensure_operations_db, ensure_project_db


def _utc_timestamp(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


@dataclass(frozen=True)
class ProjectProjection:
    project_id: str
    project_name: str
    manifest_path: Path
    db_path: Path
    created_at: datetime
    updated_at: datetime
    artifact_paths: dict[str, Path]
    export_count: int


class ProjectRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)

    def reconcile_projects_dir(self, projects_dir: Path) -> int:
        projects_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for manifest_path in sorted(projects_dir.glob("*/manifest.json")):
            if manifest_path.is_file() and manifest_path.stat().st_size > 0:
                self.register_project_dir(manifest_path.parent)
                count += 1
        return count

    def register_project_dir(self, project_dir: Path) -> None:
        from ..services.validation import ManifestValidationService

        manifest_path = project_dir / "manifest.json"
        if not manifest_path.exists() or manifest_path.stat().st_size == 0:
            return
        manifest = ManifestValidationService.validate_file(manifest_path)
        database_path = project_dir / "bible.db"
        ensure_project_db(database_path)

        artifacts = self._discover_artifacts(project_dir)
        created_at = _utc_timestamp(manifest_path)
        latest_timestamp = max((_utc_timestamp(path) for path in artifacts.values()), default=created_at)
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
                    latest_timestamp.isoformat(),
                ),
            )
            for artifact_type, artifact_path in artifacts.items():
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

    def list_project_projections(self) -> list[ProjectProjection]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    project_id,
                    project_name,
                    manifest_path,
                    db_path,
                    created_at,
                    updated_at
                FROM projects
                ORDER BY project_name COLLATE NOCASE, project_id
                """
            ).fetchall()
        return [self._build_projection(row) for row in rows]

    def get_project_projection(self, project_id: str) -> ProjectProjection | None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT
                    project_id,
                    project_name,
                    manifest_path,
                    db_path,
                    created_at,
                    updated_at
                FROM projects
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        return self._build_projection(row)

    def get_artifact_path(self, project_id: str, artifact_type: str) -> Path | None:
        projection = self.get_project_projection(project_id)
        if projection is None:
            return None
        return projection.artifact_paths.get(self._canonical_artifact_type(artifact_type))

    def register_artifact_path(self, project_id: str, artifact_type: str, artifact_path: Path) -> None:
        canonical_type = self._canonical_artifact_type(artifact_type)
        if not artifact_path.exists() or not artifact_path.is_file():
            raise FileNotFoundError(str(artifact_path))
        projection = self.get_project_projection(project_id)
        if projection is None:
            raise FileNotFoundError(f"Project projection not found for project_id={project_id}")
        timestamp = _utc_timestamp(artifact_path).isoformat()
        content_hash = self._hash_if_file(artifact_path)
        size_bytes = artifact_path.stat().st_size
        previous_artifact_row, previous_project_updated_at = self._snapshot_artifact_registration(
            project_id=project_id,
            artifact_type=canonical_type,
        )
        self._upsert_operations_artifact(
            project_id=project_id,
            artifact_type=canonical_type,
            artifact_path=artifact_path,
            content_hash=content_hash,
            size_bytes=size_bytes,
            timestamp=timestamp,
        )
        try:
            self._upsert_project_db_artifact(
                db_path=projection.db_path,
                artifact_type=canonical_type,
                artifact_path=artifact_path,
                timestamp=timestamp,
            )
        except Exception:
            self._restore_operations_artifact(
                project_id=project_id,
                artifact_type=canonical_type,
                previous_artifact_row=previous_artifact_row,
                previous_project_updated_at=previous_project_updated_at,
            )
            raise

    def _snapshot_artifact_registration(
        self,
        *,
        project_id: str,
        artifact_type: str,
    ) -> tuple[dict[str, object] | None, str | None]:
        with connect(self.db_path) as connection:
            artifact_row = connection.execute(
                """
                SELECT path, content_hash, size_bytes, created_at, updated_at
                FROM project_artifacts
                WHERE project_id = ? AND artifact_type = ?
                """,
                (project_id, artifact_type),
            ).fetchone()
            project_row = connection.execute(
                "SELECT updated_at FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        snapshot = None
        if artifact_row is not None:
            snapshot = {
                "path": artifact_row["path"],
                "content_hash": artifact_row["content_hash"],
                "size_bytes": artifact_row["size_bytes"],
                "created_at": artifact_row["created_at"],
                "updated_at": artifact_row["updated_at"],
            }
        return snapshot, (project_row["updated_at"] if project_row is not None else None)

    def _upsert_operations_artifact(
        self,
        *,
        project_id: str,
        artifact_type: str,
        artifact_path: Path,
        content_hash: str | None,
        size_bytes: int | None,
        timestamp: str,
    ) -> None:
        with connect(self.db_path) as connection:
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
                    project_id,
                    artifact_type,
                    str(artifact_path),
                    content_hash,
                    size_bytes,
                    timestamp,
                    timestamp,
                ),
            )
            connection.execute(
                "UPDATE projects SET updated_at = ? WHERE project_id = ?",
                (timestamp, project_id),
            )
            connection.commit()

    def _upsert_project_db_artifact(
        self,
        *,
        db_path: Path,
        artifact_type: str,
        artifact_path: Path,
        timestamp: str,
    ) -> None:
        with connect(db_path) as connection:
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
                    timestamp,
                ),
            )
            connection.commit()

    def _restore_operations_artifact(
        self,
        *,
        project_id: str,
        artifact_type: str,
        previous_artifact_row: dict[str, object] | None,
        previous_project_updated_at: str | None,
    ) -> None:
        with connect(self.db_path) as connection:
            if previous_artifact_row is None:
                connection.execute(
                    """
                    DELETE FROM project_artifacts
                    WHERE project_id = ? AND artifact_type = ?
                    """,
                    (project_id, artifact_type),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO project_artifacts (
                        project_id, artifact_type, path, content_hash, size_bytes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, artifact_type) DO UPDATE SET
                        path = excluded.path,
                        content_hash = excluded.content_hash,
                        size_bytes = excluded.size_bytes,
                        created_at = excluded.created_at,
                        updated_at = excluded.updated_at
                    """,
                    (
                        project_id,
                        artifact_type,
                        previous_artifact_row["path"],
                        previous_artifact_row["content_hash"],
                        previous_artifact_row["size_bytes"],
                        previous_artifact_row["created_at"],
                        previous_artifact_row["updated_at"],
                    ),
                )
            if previous_project_updated_at is not None:
                connection.execute(
                    "UPDATE projects SET updated_at = ? WHERE project_id = ?",
                    (previous_project_updated_at, project_id),
                )
            connection.commit()

    def _build_projection(self, row) -> ProjectProjection:
        project_id = row["project_id"]
        with connect(self.db_path) as connection:
            artifact_rows = connection.execute(
                """
                SELECT artifact_type, path
                FROM project_artifacts
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchall()
        artifact_paths = {
            artifact_row["artifact_type"]: Path(artifact_row["path"])
            for artifact_row in artifact_rows
        }
        export_count = sum(1 for artifact_type in artifact_paths if artifact_type.startswith("export:"))
        return ProjectProjection(
            project_id=project_id,
            project_name=row["project_name"],
            manifest_path=Path(row["manifest_path"]),
            db_path=Path(row["db_path"]),
            created_at=_parse_timestamp(row["created_at"]),
            updated_at=_parse_timestamp(row["updated_at"]),
            artifact_paths=artifact_paths,
            export_count=export_count,
        )

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
