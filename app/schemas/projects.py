from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import Field

from app.schemas.base import StrictSchemaModel
from app.schemas.manifest import Manifest, ManifestConfig


def default_project_id() -> str:
    return str(uuid4())


class ProjectCreateRequest(StrictSchemaModel):
    project_id: str = Field(default_factory=default_project_id, min_length=1)
    project_name: str = Field(min_length=1)
    config: ManifestConfig
    constraints: list[str] = Field(default_factory=list)
    premise_text: str | None = None

    def to_manifest(self) -> Manifest:
        return Manifest(
            project_id=self.project_id,
            project_name=self.project_name,
            config=self.config,
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


ProjectSummary = ProjectSummaryResponse