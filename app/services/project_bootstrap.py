from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.persistence.sqlite import ensure_project_db
from app.schemas.manifest import Manifest
from app.settings import settings


def ensure_project_structure(root_dir: Path | None = None) -> dict[str, Path]:
    base_dir = root_dir or settings.root_dir
    directories = {
        "app": base_dir / "app",
        "api": base_dir / "app" / "api",
        "schemas": base_dir / "app" / "schemas",
        "services": base_dir / "app" / "services",
        "data": base_dir / "data",
        "projects": base_dir / "data" / "projects",
        "models": base_dir / "data" / "models",
        "state": base_dir / "data" / "state",
        "docs": base_dir / "docs",
        "frontend": base_dir / "frontend",
    }
    for path in directories.values():
        path.mkdir(parents=True, exist_ok=True)
    return directories


def initialize_project_artifacts(
    project_id: UUID | str,
    manifest: Manifest | None = None,
    root_dir: Path | None = None,
) -> dict[str, Path]:
    ensure_project_structure(root_dir=root_dir)
    base_dir = root_dir or settings.root_dir
    project_dir = base_dir / "data" / "projects" / str(project_id)
    exports_dir = project_dir / "exports"
    project_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "project_dir": project_dir,
        "manifest": project_dir / "manifest.json",
        "database": project_dir / "bible.db",
        "sequence": project_dir / "sequences.json",
        "chapter_1": project_dir / "chapter.md",
        "telemetry": project_dir / settings.telemetry_filename,
        "structured_log": project_dir / settings.structured_log_filename,
        "exports": exports_dir,
    }

    if manifest is not None:
        paths["manifest"].write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    elif not paths["manifest"].exists():
        paths["manifest"].touch()

    for key in ("sequence", "chapter_1", "telemetry", "structured_log"):
        if not paths[key].exists():
            paths[key].touch()
    ensure_project_db(paths["database"])

    return paths
