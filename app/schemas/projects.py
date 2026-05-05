from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import Field

from app.schemas.base import StrictSchemaModel
from app.schemas.manifest import Manifest, ManifestConfig
from app.schemas.enums import StoryStructure


def default_project_id() -> str:
    return str(uuid4())


class ProjectCreateRequest(StrictSchemaModel):
    project_id: str = Field(default_factory=default_project_id, min_length=1)
    project_name: str = Field(min_length=1)
    config: ManifestConfig | None = None
    constraints: list[str] = Field(default_factory=list)
    premise_text: str | None = None
    idempotency_key: str | None = Field(default=None, max_length=256)
    project_kind: str = Field(default="standard", max_length=20)
    # Direct fields (legacy/simple format)
    genre: str | None = None
    tone_profile: str | None = None
    story_structure: str | None = None

    def to_manifest(self) -> Manifest:
        if self.config is not None:
            return Manifest(
                project_id=self.project_id,
                project_name=self.project_name,
                config=self.config,
                constraints=self.constraints,
                premise_text=self.premise_text,
            )
        # Build config from direct fields (simple format)
        story_struct = StoryStructure(self.story_structure) if self.story_structure else StoryStructure.THREE_ACT
        project_kind = self.project_kind or "standard"
        if project_kind == "brain_dump":
            story_struct = StoryStructure.BRAINDUMP

        genre = self.genre
        if project_kind == "brain_dump" and not genre:
            genre = "Brain Dump"
        if not genre:
            genre = "Unknown"

        config = ManifestConfig(
            genre=genre,
            tone_profile=self.tone_profile or "Neutral",
            primary_language="English",
            secondary_language="None",
            story_structure=story_struct,
        )
        return Manifest(
            project_id=self.project_id,
            project_name=self.project_name,
            config=config,
            constraints=self.constraints,
            premise_text=self.premise_text,
        )


class ProjectSummaryResponse(StrictSchemaModel):
    project_id: str = Field(min_length=1)
    project_name: str = Field(min_length=1)
    genre: str = Field(min_length=1)
    tone_profile: str = Field(min_length=1)
    story_structure: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(StrictSchemaModel):
    project_id: str = Field(min_length=1)
    project_name: str = Field(min_length=1)
    manifest: Manifest
    project_dir: str = Field(min_length=1)
    database_exists: bool
    sequence_exists: bool
    chapter_exists: bool
    export_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime


class ProjectArtifactResponse(StrictSchemaModel):
    project_id: str = Field(min_length=1)
    artifact_name: str = Field(min_length=1)
    content: str
    updated_at: datetime
    # Optional lineage fields (populated when artifact comes from lineage-aware storage)
    lineage_id: int | None = None
    run_id: str | None = None
    step_name: str | None = None


ProjectSummary = ProjectSummaryResponse


class OrphanInfo(StrictSchemaModel):
    project_id: str = Field(min_length=1)
    project_name: str | None = None
    kind: Literal["orphaned_dir", "db_only", "disk_only"]
    size_bytes: int = Field(ge=0)


class MaintenanceSummary(StrictSchemaModel):
    audit_log_lines: int = Field(ge=0)
    audit_log_retain_lines: int = Field(ge=1)
    database_size_bytes: int = Field(ge=0)
    checker_report_files: int = Field(ge=0)
    total_jobs: int = Field(ge=0)
    total_checker_runs: int = Field(ge=0)


class MaintenanceScanResponse(StrictSchemaModel):
    orphaned_dirs: list[OrphanInfo] = Field(default_factory=list)
    db_only: list[OrphanInfo] = Field(default_factory=list)
    disk_only: list[OrphanInfo] = Field(default_factory=list)
    summary: MaintenanceSummary


class MaintenanceCleanupRequest(StrictSchemaModel):
    project_ids: list[str] = Field(min_length=1)


class MaintenanceCleanupResponse(StrictSchemaModel):
    removed: int = Field(ge=0)
    errors: list[dict[str, str]] = Field(default_factory=list)


class AuditLogTruncationRequest(StrictSchemaModel):
    retain_lines: int = Field(ge=1, default=10000)


class AuditLogTruncationResponse(StrictSchemaModel):
    truncated: int = Field(ge=0)
    retained: int = Field(ge=0)


class DatabaseCompactionResponse(StrictSchemaModel):
    before_bytes: int = Field(ge=0)
    after_bytes: int = Field(ge=0)


class ProjectDeletionResponse(StrictSchemaModel):
    deleted: bool
    project_id: str = Field(min_length=1)
    history_removed: dict[str, int]