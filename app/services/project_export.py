from __future__ import annotations

import json
import logging
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from app.persistence.sqlite import connect as _connect_ops_db
from app.schemas.project_io import ExportMetadata
from app.settings import settings

logger = logging.getLogger(__name__)

_EXPORT_VERSION = 1


_OPS_TABLES_WITH_PROJECT_ID: tuple[str, ...] = (
    "projects",
    "project_artifacts",
    "jobs",
    "checker_runs",
    "story_flow_definitions",
    "story_flow_stages",
    "brainstorm_items",
    "brain_dump_sessions",
    "foundation_profiles",
    "foundation_revisions",
    "character_profiles",
    "world_bible_entries",
    "arc_candidates",
    "arc_stage_maps",
    "arc_selections",
    "story_decision_nodes",
    "branch_points",
    "story_branches",
    "branch_state_refs",
    "branch_comparisons",
    "branch_merge_decisions",
    "checker_findings",
    "review_decisions",
    "inspect_run_links",
    "sequence_plans",
    "chapter_plans",
    "scene_plans",
    "beat_plans",
    "chapter_packets",
    "planning_dependencies",
    "continuity_threads",
    "continuity_states",
    "continuity_findings",
    "draft_briefs",
    "drafting_context_packets",
    "draft_artifacts",
    "manuscript_documents",
    "revision_suggestions",
    "canon_annotations",
    "canon_customization_profiles",
    "mythos_entries",
    "pattern_entries",
    "relationship_edges",
    "manuscript_assist_runs",
    "manuscript_assist_suggestions",
    "manuscript_assist_gate_results",
)


class ProjectExportService:
    """Create comprehensive project ZIP archives."""

    def __init__(self, ops_db_path: Path | None = None) -> None:
        self._ops_db_path = ops_db_path or settings.operations_db_path

    @staticmethod
    def _walk_project_dir(project_dir: Path) -> list[Path]:
        """Recursively walk the project directory and return a sorted file list."""
        files: list[Path] = []
        for root, _dirs, filenames in os.walk(project_dir):
            for fname in sorted(filenames):
                fpath = Path(root) / fname
                if fpath.name.endswith(("-wal", "-shm")):
                    continue
                files.append(fpath)
        return files

    def _dump_table_json(self, conn, table_name: str, project_id: str) -> list[dict]:
        """Query all rows from a table where project_id matches."""
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM {table_name} WHERE project_id = ?",
            (project_id,),
        )
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows: list[dict] = []
        for row in cursor.fetchall():
            row_dict: dict = {}
            for col, val in zip(columns, row):
                if isinstance(val, bytes):
                    try:
                        row_dict[col] = val.decode("utf-8")
                    except UnicodeDecodeError:
                        row_dict[col] = None
                elif hasattr(val, "isoformat"):
                    row_dict[col] = val.isoformat()
                else:
                    row_dict[col] = val
            rows.append(row_dict)
        return rows

    def dump_ops_data(self, project_id: str) -> dict[str, list[dict]]:
        """Dump all ops DB rows scoped to a project_id."""
        conn = _connect_ops_db(self._ops_db_path)
        try:
            result: dict[str, list[dict]] = {}
            for table in _OPS_TABLES_WITH_PROJECT_ID:
                rows = self._dump_table_json(conn, table, project_id)
                if rows:
                    result[table] = rows
            return result
        finally:
            conn.close()

    def create_zip(
        self,
        project_dir: Path,
        output_path: Path,
        project_name: str,
        project_id: str,
        engine_version: str = "1.5.1",
    ) -> None:
        """Create a ZIP archive of the project directory + ops DB dump."""
        metadata = ExportMetadata(
            export_version=_EXPORT_VERSION,
            engine_version=engine_version,
            created_at=datetime.now(timezone.utc).isoformat(),
            original_project_id=project_id,
            original_project_name=project_name,
        )

        ops_data = self.dump_ops_data(project_id)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("metadata.json", json.dumps(metadata.model_dump(), indent=2))

            project_files = self._walk_project_dir(project_dir)
            for fpath in project_files:
                arcname = str(fpath.relative_to(project_dir.parent))
                zf.write(fpath, arcname)

            if ops_data:
                zf.writestr("ops_db/", "")
                for table_name, rows in sorted(ops_data.items()):
                    zf.writestr(f"ops_db/{table_name}.json", json.dumps(rows, indent=2, default=str))

    @classmethod
    def project_files(cls, project_dir: Path) -> list[Path]:
        """List all files that would be included."""
        return cls._walk_project_dir(project_dir)
