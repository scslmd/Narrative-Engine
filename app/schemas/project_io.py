from __future__ import annotations

from .base import StrictModel


class ExportMetadata(StrictModel):
    """Schema for metadata.json inside export ZIP."""
    export_version: int = 1
    engine_version: str
    created_at: str
    original_project_id: str
    original_project_name: str


class ProjectExportSubmitResponse(StrictModel):
    """Returned by POST /projects/import-export (async)."""
    import_id: str
    status: str = "pending"


class ProjectExportProgressResponse(StrictModel):
    """Returned by GET /projects/export/{import_id}."""
    import_id: str
    status: str  # pending/running/completed/failed
    phase: str | None = None
    export_version: int | None = None
    created_at: str | None = None
    original_project_id: str | None = None
    result: dict | None = None  # On success: {"project_id": "...", "project_name": "..."}
    error: str | None = None


class ProjectImportRequest(StrictModel):
    """Schema for internal validation of import metadata."""
    project_name: str
    genre: str | None = None
    tone: str | None = None
