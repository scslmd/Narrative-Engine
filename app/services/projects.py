from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.persistence import ProjectRepository
from app.schemas.projects import (
    ProjectArtifactResponse,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectSummaryResponse,
)
from app.services.project_bootstrap import initialize_project_artifacts
from app.services.validation import ManifestValidationService
from app.settings import settings


def _file_timestamp(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)


class ProjectService:
    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or settings.root_dir
        self.projects_dir = self.root_dir / "data" / "projects"
        self.repository = ProjectRepository(
            settings.operations_db_path if self.root_dir == settings.root_dir else self.root_dir / "data" / "state" / "narrative_ops.db"
        )
        self.repository.sync_from_projects_dir(self.projects_dir)

    def create_project(self, request: ProjectCreateRequest) -> ProjectDetailResponse:
        manifest = request.to_manifest()
        initialize_project_artifacts(request.project_id, manifest=manifest, root_dir=self.root_dir)
        self.repository.register_project_dir(self.projects_dir / request.project_id)
        return self.get_project(request.project_id)

    def list_projects(self) -> list[ProjectSummaryResponse]:
        results: list[ProjectSummaryResponse] = []
        for manifest_path in sorted(self.projects_dir.glob("*/manifest.json")):
            if not manifest_path.is_file() or manifest_path.stat().st_size == 0:
                continue
            manifest = ManifestValidationService.validate_file(manifest_path)
            created_at = _file_timestamp(manifest_path)
            results.append(
                ProjectSummaryResponse(
                    project_id=manifest.project_id,
                    project_name=manifest.project_name,
                    genre=manifest.config.genre,
                    tone_profile=manifest.config.tone_profile,
                    story_structure=manifest.config.story_structure,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )
        return results

    def get_project(self, project_id: str) -> ProjectDetailResponse:
        project_dir = self.projects_dir / str(project_id)
        manifest_path = project_dir / "manifest.json"
        if not manifest_path.exists() or manifest_path.stat().st_size == 0:
            raise FileNotFoundError(f"Project manifest not found for project_id={project_id}")

        manifest = ManifestValidationService.validate_file(manifest_path)
        sequence_path = self._artifact_path(project_id, "sequence")
        chapter_path = self._artifact_path(project_id, "chapter-1")
        exports_dir = project_dir / "exports"
        created_at = _file_timestamp(manifest_path)
        updated_source = manifest_path
        for candidate in (sequence_path, chapter_path):
            if candidate is not None and candidate.exists() and candidate.stat().st_mtime > updated_source.stat().st_mtime:
                updated_source = candidate

        return ProjectDetailResponse(
            project_id=manifest.project_id,
            project_name=manifest.project_name,
            manifest=manifest,
            project_dir=str(project_dir),
            database_exists=(project_dir / "bible.db").exists(),
            sequence_exists=sequence_path is not None and sequence_path.exists() and sequence_path.stat().st_size > 0,
            chapter_exists=chapter_path is not None and chapter_path.exists() and chapter_path.stat().st_size > 0,
            export_count=len(list(exports_dir.glob("*.md"))) if exports_dir.exists() else 0,
            created_at=created_at,
            updated_at=_file_timestamp(updated_source),
        )

    def read_artifact(self, project_id: str, artifact_name: str) -> ProjectArtifactResponse:
        artifact_path = self._artifact_path(project_id, artifact_name)
        if artifact_path is None or not artifact_path.exists():
            raise FileNotFoundError(f"Artifact not found: {artifact_name}")

        content = artifact_path.read_text(encoding="utf-8")
        if artifact_name == "manifest":
            parsed = json.loads(content)
            content = json.dumps(parsed, ensure_ascii=True, indent=2, sort_keys=True)

        return ProjectArtifactResponse(
            project_id=str(project_id),
            artifact_name=artifact_name,
            content=content,
            updated_at=_file_timestamp(artifact_path),
        )

    def _artifact_path(self, project_id: str, artifact_name: str) -> Path | None:
        project_dir = self.projects_dir / str(project_id)
        if artifact_name == "manifest":
            return project_dir / "manifest.json"
        return self.repository.get_artifact_path(project_id, artifact_name)
