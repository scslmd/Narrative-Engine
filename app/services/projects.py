from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.persistence import ProjectProjection, ProjectRepository
from app.schemas.projects import (
    ProjectArtifactResponse,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectSummaryResponse,
)
from app.services.project_bootstrap import initialize_project_artifacts
from app.services.validation import ManifestValidationService
from app.settings import settings


class ProjectService:
    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or settings.root_dir
        self.projects_dir = self.root_dir / "data" / "projects"
        self.repository = ProjectRepository(
            settings.operations_db_path if self.root_dir == settings.root_dir else self.root_dir / "data" / "state" / "narrative_ops.db"
        )

    def reconcile_projects(self) -> int:
        return self.repository.reconcile_projects_dir(self.projects_dir)

    def create_project(self, request: ProjectCreateRequest) -> ProjectDetailResponse:
        manifest = request.to_manifest()
        initialize_project_artifacts(request.project_id, manifest=manifest, root_dir=self.root_dir)
        self.repository.register_project_dir(self.projects_dir / request.project_id)
        return self.get_project(request.project_id)

    def list_projects(self) -> list[ProjectSummaryResponse]:
        results: list[ProjectSummaryResponse] = []
        for projection in self.repository.list_project_projections():
            manifest = ManifestValidationService.validate_file(projection.manifest_path)
            results.append(
                ProjectSummaryResponse(
                    project_id=manifest.project_id,
                    project_name=manifest.project_name,
                    genre=manifest.config.genre,
                    tone_profile=manifest.config.tone_profile,
                    story_structure=manifest.config.story_structure,
                    created_at=projection.created_at,
                    updated_at=projection.updated_at,
                )
            )
        return results

    def get_project(self, project_id: str) -> ProjectDetailResponse:
        projection = self.repository.get_project_projection(project_id)
        if projection is None or not projection.manifest_path.exists() or projection.manifest_path.stat().st_size == 0:
            raise FileNotFoundError(f"Project manifest not found for project_id={project_id}")

        manifest = ManifestValidationService.validate_file(projection.manifest_path)
        sequence_path = projection.artifact_paths.get("sequence")
        chapter_path = projection.artifact_paths.get("chapter_1")

        return ProjectDetailResponse(
            project_id=manifest.project_id,
            project_name=manifest.project_name,
            manifest=manifest,
            project_dir=str(projection.manifest_path.parent),
            database_exists=projection.db_path.exists(),
            sequence_exists=sequence_path is not None and sequence_path.exists() and sequence_path.stat().st_size > 0,
            chapter_exists=chapter_path is not None and chapter_path.exists() and chapter_path.stat().st_size > 0,
            export_count=projection.export_count,
            created_at=projection.created_at,
            updated_at=projection.updated_at,
        )

    def read_artifact(self, project_id: str, artifact_name: str) -> ProjectArtifactResponse:
        projection = self._require_projection(project_id)
        artifact_path = self._artifact_path(projection, artifact_name)
        if artifact_path is None or not artifact_path.exists():
            raise FileNotFoundError(f"Artifact not found: {artifact_name}")

        content = artifact_path.read_text(encoding="utf-8")
        if artifact_name == "manifest":
            parsed = json.loads(content)
            content = json.dumps(parsed, ensure_ascii=True, indent=2, sort_keys=True)

        return ProjectArtifactResponse(
            project_id=projection.project_id,
            artifact_name=artifact_name,
            content=content,
            updated_at=_file_timestamp(artifact_path),
        )

    def _require_projection(self, project_id: str) -> ProjectProjection:
        projection = self.repository.get_project_projection(project_id)
        if projection is None:
            raise FileNotFoundError(f"Project manifest not found for project_id={project_id}")
        return projection

    def _artifact_path(self, projection: ProjectProjection, artifact_name: str) -> Path | None:
        if artifact_name == "manifest":
            return projection.manifest_path
        return projection.artifact_paths.get(_canonical_artifact_type(artifact_name))


def _file_timestamp(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)


def _canonical_artifact_type(artifact_type: str) -> str:
    if artifact_type in {"chapter", "chapter-1", "chapter_1"}:
        return "chapter_1"
    if artifact_type in {"sequence", "sequences"}:
        return "sequence"
    return artifact_type
