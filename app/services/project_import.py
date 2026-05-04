from __future__ import annotations

import json
import logging
import shutil
import uuid
import zipfile
from pathlib import Path

import sqlite3

from app.services.project_bootstrap import initialize_project_artifacts
from app.schemas.project_io import ExportMetadata
from app.settings import settings

logger = logging.getLogger(__name__)


class ProjectImportError(ValueError):
    """Raised when import validation or execution fails."""
    pass


_MIN_EXPORT_VERSION = 1
_CURRENT_EXPORT_VERSION = 1


class ProjectImportService:
    """Import a project from an exported ZIP archive."""

    def validate_zip(self, zip_path: Path) -> ExportMetadata:
        """Validate ZIP structure and read metadata. Raises ProjectImportError on failure."""
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                if "metadata.json" not in zf.namelist():
                    raise ProjectImportError("Invalid export: missing metadata.json")

                with zf.open("metadata.json") as f:
                    raw = json.loads(f.read().decode("utf-8"))

                metadata = ExportMetadata.model_validate(raw)
        except zipfile.BadZipFile:
            raise ProjectImportError("The uploaded file is not a valid ZIP archive")
        except (json.JSONDecodeError, ValueError) as e:
            raise ProjectImportError(f"Invalid export format: {e}")

        if metadata.export_version < _MIN_EXPORT_VERSION:
            raise ProjectImportError(
                f"Export version {metadata.export_version} is not supported. "
                f"Minimum supported: {_MIN_EXPORT_VERSION}"
            )

        return metadata

    @staticmethod
    def migrate_v1_to_current(rows: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """Migration pass for export version 1 → current."""
        return rows

    def extract_zip(self, zip_path: Path, target_dir: Path) -> dict[str, list[dict]]:
        """Extract ZIP contents to target directory. Returns ops_db parsed data."""
        target_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.filename.startswith("/") or ".." in Path(info.filename).parts:
                    raise ProjectImportError(f"Path traversal detected in ZIP entry: {info.filename}")

                target_path = target_dir / info.filename

                if info.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as src, open(target_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)

        ops_data: dict[str, list[dict]] = {}
        ops_dir = target_dir / "ops_db"
        if ops_dir.exists():
            for json_file in sorted(ops_dir.glob("*.json")):
                table_name = json_file.stem
                with open(json_file, "r", encoding="utf-8") as f:
                    ops_data[table_name] = json.load(f)

        return ops_data

    def restore_ops_db(self, conn: sqlite3.Connection, ops_data: dict[str, list[dict]]) -> int:
        """Restore ops DB rows from extracted data. Returns total rows restored."""
        cursor = conn.cursor()
        total_restored = 0

        for table_name, rows in sorted(ops_data.items()):
            if not rows:
                continue

            columns = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(columns))
            col_names = ", ".join(columns)

            for row in rows:
                values = [row[col] for col in columns]
                try:
                    cursor.execute(
                        f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})",
                        values,
                    )
                    total_restored += 1
                except sqlite3.Error as e:
                    logger.warning("Failed to restore row in %s: %s — skipping", table_name, e)

        conn.commit()
        return total_restored

    def import_from_zip(
        self,
        zip_path: Path,
        new_project_name: str | None = None,
        ops_db_path: Path | None = None,
    ) -> dict:
        """Full import flow: validate → extract → migrate → create project → restore ops DB.

        Returns {"project_id": str, "project_name": str, "rows_restored": int}.
        Raises ProjectImportError on failure.
        """
        metadata = self.validate_zip(zip_path)

        ops_db = ops_db_path or settings.operations_db_path
        temp_dir = Path(str(ops_db).parent) / f".import_{metadata.original_project_id}_{uuid.uuid4().hex[:8]}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            ops_data = self.extract_zip(zip_path, temp_dir)

            if metadata.export_version != _CURRENT_EXPORT_VERSION:
                ops_data = self.migrate_v1_to_current(ops_data)

            project_id = f"{metadata.original_project_id}_imported_{uuid.uuid4().hex[:8]}"
            project_name = new_project_name or metadata.original_project_name

            initialize_project_artifacts(project_id, root_dir=settings.root_dir)

            for item in temp_dir.iterdir():
                if item.name == "ops_db":
                    continue
                dest = settings.projects_dir / project_id / item.name
                if item.is_file():
                    shutil.copy2(item, dest)

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

        conn = sqlite3.connect(str(ops_db))
        try:
            rows_restored = self.restore_ops_db(conn, ops_data)
        finally:
            conn.close()

        return {
            "project_id": project_id,
            "project_name": project_name,
            "rows_restored": rows_restored,
            "export_version": metadata.export_version,
        }
