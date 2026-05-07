from __future__ import annotations

import logging
from typing import Any, Callable, Protocol, TypeVar

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

R = TypeVar("R")


def handle_service_error(
    func: Callable[[], R],
    specific_error: type[Exception],
) -> R:
    """Execute a service function and translate errors to HTTP exceptions.

    Args:
        func: Zero-argument callable that performs the service operation.
        specific_error: Exception class that maps to 400 Bad Request.

    Returns:
        The result of func() on success.

    Raises:
        HTTPException: 400 for specific_error, 500 for unexpected failures.
    """
    try:
        return func()
    except specific_error as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class _ImportServiceProtocol(Protocol):
    def import_story(self, request: Any) -> Any: ...


class _MythosServiceProtocol(Protocol):
    def extract(self, request: Any) -> Any: ...


class _PatternServiceProtocol(Protocol):
    def extract(
        self,
        text: str,
        source_type: str,
        generation_mode: str,
        project_id: str | None,
        source_corpus: str | None,
    ) -> Any: ...

    def extract_from_project(
        self,
        project_id: str,
        source_type: str,
        generation_mode: str,
        source_corpus: str | None,
    ) -> Any: ...


class _MaintenanceServiceProtocol(Protocol):
    def scan_orphans(self) -> MaintenanceScanResponse: ...
    def cleanup(self, project_ids: list[str]) -> MaintenanceCleanupResponse: ...
    def delete_project(self, project_id: str) -> ProjectDeletionResponse: ...
    def truncate_audit_log(self, retain_lines: int | None = None) -> AuditLogTruncationResponse: ...
    def compact_database(self) -> DatabaseCompactionResponse: ...

from app.schemas.projects import (
    AuditLogTruncationRequest,
    AuditLogTruncationResponse,
    DatabaseCompactionResponse,
    MaintenanceCleanupRequest,
    MaintenanceCleanupResponse,
    MaintenanceScanResponse,
    ProjectArtifactResponse,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectDeletionResponse,
    ProjectSummaryResponse,
)
from app.schemas.mythos_extraction import (
    MythosExtractionRequest,
    MythosExtractionResponse,
)
from app.schemas.pattern_extraction import (
    ExtractPatternsRequest,
    PatternExtractionRequest,
    PatternExtractionResponse,
)
from app.services.mythos_extraction import MythosExtractionError
from app.services.pattern_extraction import PatternExtractionError
from app.services.projects import ProjectService
from app.services.project_export import ProjectExportService, _EXPORT_VERSION
from app.services.project_import import ProjectImportService, ProjectImportError
from app.services.project_maintenance import ProjectMaintenanceError



def build_projects_router(
    project_service: ProjectService,
    import_service: _ImportServiceProtocol | None = None,
    mythos_service: _MythosServiceProtocol | None = None,
    pattern_service: _PatternServiceProtocol | None = None,
    import_job_manager: Any | None = None,
    extraction_job_manager: Any | None = None,
    maintenance_service: _MaintenanceServiceProtocol | None = None,
) -> APIRouter:
    from ..schemas.story_import import StoryImportRequest, StoryImportResponse
    from ..services.story_import import StoryImportError

    router = APIRouter(prefix="/projects", tags=["projects"])

    @router.post("/create", response_model=ProjectDetailResponse, status_code=201)
    def create_project(request: ProjectCreateRequest) -> ProjectDetailResponse:
        try:
            return project_service.create_project(request)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("", response_model=list[ProjectSummaryResponse])
    def list_projects() -> list[ProjectSummaryResponse]:
        return project_service.list_projects()

    @router.get("/{project_id}", response_model=ProjectDetailResponse)
    def get_project(project_id: str) -> ProjectDetailResponse:
        try:
            return project_service.get_project(project_id)
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.delete("/{project_id}", response_model=ProjectDeletionResponse)
    def delete_project(project_id: str) -> ProjectDeletionResponse:
        if not maintenance_service:
            raise HTTPException(status_code=503, detail="Maintenance service unavailable")
        try:
            return maintenance_service.delete_project(project_id)
        except ProjectMaintenanceError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/{project_id}/manifest")
    def get_manifest(project_id: str) -> dict:
        try:
            return project_service.load_manifest(project_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/{project_id}/sequence", response_model=ProjectArtifactResponse)
    def get_sequence(project_id: str) -> ProjectArtifactResponse:
        try:
            return project_service.read_artifact(project_id, "sequence")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/{project_id}/chapter-1", response_model=ProjectArtifactResponse)
    def get_chapter(project_id: str) -> ProjectArtifactResponse:
        try:
            return project_service.read_artifact(project_id, "chapter-1")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    if maintenance_service is not None:
        @router.post("/maintenance/scan", response_model=MaintenanceScanResponse)
        def scan_orphans() -> MaintenanceScanResponse:
            return maintenance_service.scan_orphans()

        @router.post("/maintenance/cleanup", response_model=MaintenanceCleanupResponse)
        def cleanup(request: MaintenanceCleanupRequest) -> MaintenanceCleanupResponse:
            try:
                return maintenance_service.cleanup(request.project_ids)
            except ProjectMaintenanceError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

        @router.delete("/maintenance/projects/{project_id}", response_model=ProjectDeletionResponse)
        def delete_project(project_id: str) -> ProjectDeletionResponse:
            try:
                return maintenance_service.delete_project(project_id)
            except ProjectMaintenanceError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc

        @router.post("/maintenance/audit-log/truncate", response_model=AuditLogTruncationResponse)
        def truncate_audit_log(request: AuditLogTruncationRequest) -> AuditLogTruncationResponse:
            return maintenance_service.truncate_audit_log(retain_lines=request.retain_lines)

        @router.post("/maintenance/database/compact", response_model=DatabaseCompactionResponse)
        def compact_database() -> DatabaseCompactionResponse:
            return maintenance_service.compact_database()

    if import_service is not None and import_job_manager is not None:
        from ..schemas.story_import import ImportSubmitResponse, ImportProgressResponse

        def _run_import_worker(
            import_service: Any,
            request: StoryImportRequest,
            job_manager: Any,
            import_id: str,
        ) -> Any:
            def on_progress(phase: str, data: dict[str, Any]) -> None:
                job_manager.update_progress(import_id, phase=phase, **data)

            job_manager.update_progress(import_id, status="running", phase="initializing")
            result = import_service.import_story_with_progress(request, on_progress)
            return result

        @router.post("/import-story", response_model=ImportSubmitResponse, status_code=202)
        async def import_story(
            story_text: str | None = Form(None),
            project_name: str | None = Form(None),
            genre: str | None = Form(None),
            tone: str | None = Form(None),
            project_id: str | None = Form(None),
            file: UploadFile | None = File(None),
        ):
            text = story_text
            if file is not None:
                ext = (file.filename or "").lower().rsplit(".", 1)[-1]
                if ext not in ("txt", "md"):
                    raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
                content = await file.read()
                text = content.decode("utf-8").strip()

            if not text or len(text.strip()) < 50:
                raise HTTPException(status_code=400, detail="Story text must be at least 50 characters")

            request = StoryImportRequest(
                project_name=project_name or "",
                story_text=text,
                project_id=project_id or None,
                genre=genre or None,
                tone=tone or None,
            )

            import_id = import_job_manager.submit(
                _run_import_worker,
                import_service=import_service,
                request=request,
                job_manager=import_job_manager,
            )
            return ImportSubmitResponse(import_id=import_id)

        @router.get("/import/{import_id}", response_model=ImportProgressResponse)
        def get_import_status(import_id: str):
            try:
                return import_job_manager.get_status(import_id)
            except KeyError:
                raise HTTPException(status_code=404, detail=f"Import {import_id} not found or expired")

    if mythos_service is not None and extraction_job_manager is not None:
        from app.schemas.extraction_progress import ExtractionSubmitResponse, ExtractionProgressResponse

        def _run_mythos_worker(
            mythos_service: Any,
            request: MythosExtractionRequest,
            job_manager: Any,
            extraction_id: str,
        ) -> dict[str, Any]:
            def on_progress(phase: str, data: dict[str, Any]) -> None:
                job_manager.update_progress(extraction_id, phase=phase, **data)

            job_manager.update_progress(extraction_id, status="running", phase="initializing")
            response = mythos_service.extract_with_progress(request, on_progress)

            if response.status == "completed" and response.extraction:
                return {
                    "project_id": response.project_id,
                    "source_corpus": response.extraction.source_corpus or "",
                    "archetypal_patterns": response.extraction.archetypal_patterns,
                    "narrative_structures": response.extraction.narrative_structures,
                    "world_rules": response.extraction.cosmic_rules,
                    "symbolic_motifs": response.extraction.symbolic_motifs,
                }
            else:
                raise MythosExtractionError(response.error or "Mythos extraction failed")

        @router.post("/import-mythos", response_model=ExtractionSubmitResponse, status_code=202)
        def import_mythos(request: MythosExtractionRequest):
            if not request.text or len(request.text.strip()) < 50:
                raise HTTPException(status_code=400, detail="Text must be at least 50 characters")

            extraction_id = extraction_job_manager.submit(
                _run_mythos_worker,
                mythos_service=mythos_service,
                request=request,
                job_manager=extraction_job_manager,
            )
            return ExtractionSubmitResponse(extraction_id=extraction_id)

    if pattern_service is not None and extraction_job_manager is not None:
        from app.schemas.extraction_progress import ExtractionSubmitResponse as _ExtractionSubmitResponse, ExtractionProgressResponse as _ExtractionProgressResponse

        def _run_pattern_worker(
            pattern_service: Any,
            request: PatternExtractionRequest,
            job_manager: Any,
            extraction_id: str,
        ) -> dict[str, Any]:
            def on_progress(phase: str, data: dict[str, Any]) -> None:
                job_manager.update_progress(extraction_id, phase=phase, **data)

            job_manager.update_progress(extraction_id, status="running", phase="initializing")
            response = pattern_service.extract_with_progress(
                text=request.text,
                source_type=request.source_type,
                generation_mode=request.generation_mode,
                project_id=request.project_id,
                source_corpus=request.source_corpus,
                on_progress=on_progress,
            )

            if response.status == "completed" and response.extraction:
                return {
                    "project_id": response.project_id,
                    "source_corpus": response.extraction.source_corpus or "",
                    "archetypal_patterns": response.extraction.archetypal_patterns,
                    "narrative_structures": response.extraction.narrative_structures,
                    "world_rules": response.extraction.world_rules,
                    "symbolic_motifs": response.extraction.symbolic_motifs,
                }
            else:
                raise PatternExtractionError(response.error or "Pattern extraction failed")

        def _run_project_pattern_worker(
            pattern_service: Any,
            project_id: str,
            request: ExtractPatternsRequest,
            job_manager: Any,
            extraction_id: str,
        ) -> dict[str, Any]:
            def on_progress(phase: str, data: dict[str, Any]) -> None:
                job_manager.update_progress(extraction_id, phase=phase, **data)

            job_manager.update_progress(extraction_id, status="running", phase="initializing")
            response = pattern_service.extract_from_project(
                project_id=project_id,
                source_type=request.source_type,
                generation_mode=request.generation_mode,
                source_corpus=request.source_corpus,
            )

            if response.status == "completed" and response.extraction:
                return {
                    "project_id": response.project_id,
                    "source_corpus": response.extraction.source_corpus or "",
                    "archetypal_patterns": response.extraction.archetypal_patterns,
                    "narrative_structures": response.extraction.narrative_structures,
                    "world_rules": response.extraction.world_rules,
                    "symbolic_motifs": response.extraction.symbolic_motifs,
                }
            else:
                raise PatternExtractionError(response.error or "Pattern extraction from project failed")

        @router.post("/import-patterns", response_model=_ExtractionSubmitResponse, status_code=202)
        def import_patterns(request: PatternExtractionRequest):
            if not request.text or len(request.text.strip()) < 50:
                raise HTTPException(status_code=400, detail="Text must be at least 50 characters")

            extraction_id = extraction_job_manager.submit(
                _run_pattern_worker,
                pattern_service=pattern_service,
                request=request,
                job_manager=extraction_job_manager,
            )
            return _ExtractionSubmitResponse(extraction_id=extraction_id)

        @router.post("/{project_id}/extract-patterns", response_model=_ExtractionSubmitResponse, status_code=202)
        def extract_patterns(project_id: str, request: ExtractPatternsRequest):
            extraction_id = extraction_job_manager.submit(
                _run_project_pattern_worker,
                pattern_service=pattern_service,
                project_id=project_id,
                request=request,
                job_manager=extraction_job_manager,
            )
            return _ExtractionSubmitResponse(extraction_id=extraction_id)

        @router.get("/extraction/{extraction_id}", response_model=_ExtractionProgressResponse)
        def get_extraction_status(extraction_id: str):
            try:
                return extraction_job_manager.get_status(extraction_id)
            except KeyError:
                raise HTTPException(status_code=404, detail=f"Extraction {extraction_id} not found or expired")

    if import_job_manager is not None:
        from pathlib import Path
        from ..schemas.project_io import ProjectExportSubmitResponse, ProjectExportProgressResponse


        def _run_import_export_worker(
            import_id: str,
            zip_path: str,
            project_name: str | None,
        ) -> None:
            worker_zip_path = Path(zip_path)
            try:
                import_service = ProjectImportService()
                metadata = import_service.validate_zip(worker_zip_path)
                import_job_manager.update_progress(import_id, phase="validating_zip")

                effective_name = project_name or metadata.original_project_name

                result = import_service.import_from_zip(worker_zip_path, effective_name)
                import_job_manager.complete(import_id, result=result)
            except ProjectImportError as e:
                import_job_manager.fail(import_id, error=str(e))
            except Exception as e:
                import_job_manager.fail(import_id, error=f"Unexpected error: {e}")

        @router.post("/import-export", status_code=202)
        async def import_export_zip(
            project_name: str | None = Form(None),
            file: UploadFile = File(...),
        ):
            """Import a project from an uploaded ZIP archive. Returns 202 with import_id."""

            if not file.filename or not file.filename.endswith(".zip"):
                raise HTTPException(status_code=422, detail="Only .zip files are accepted")

            import tempfile as _tempfile
            import uuid as _uuid

            tmp_dir = _tempfile.mkdtemp()
            zip_path = f"{tmp_dir}/import_{_uuid.uuid4().hex}.zip"

            content = await file.read()
            MAX_IMPORT_SIZE = 524_288_000
            if len(content) > MAX_IMPORT_SIZE:
                raise HTTPException(
                    status_code=422,
                    detail=f"ZIP file too large. Maximum size: {MAX_IMPORT_SIZE / 1_000_000:.0f} MB",
                )

            with open(zip_path, "wb") as zf:
                zf.write(content)

            return ProjectExportSubmitResponse(
                import_id=import_job_manager.submit(
                    _run_import_export_worker,
                    zip_path=zip_path,
                    project_name=project_name,
                ),
            )

        @router.get("/export/{import_id}", response_model=dict)
        def get_export_import_status(import_id: str):
            """Get the status of an export/import job."""
            try:
                status = import_job_manager.get_status(import_id)
                return {
                    "import_id": status.import_id,
                    "status": status.status,
                    "phase": status.phase,
                    "chapters_processed": status.chapters_processed,
                    "total_estimated_chapters": status.total_estimated_chapters,
                    "chunks_processed": status.chunks_processed,
                    "total_estimated_chunks": status.total_estimated_chunks,
                    "result": status.result,
                    "error": status.error,
                }
            except KeyError:
                raise HTTPException(status_code=404, detail="Import job not found or expired")

        @router.post("/{project_id}/export")
        async def export_project(project_id: str):
            """Export a project as a ZIP file stream."""
            try:
                projection = project_service._require_projection(project_id)
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="Project not found")

            from pathlib import Path as _Path
            project_dir = projection.manifest_path.parent if projection else None
            if not project_dir or not project_dir.exists():
                raise HTTPException(status_code=404, detail="Project directory not found")

            manifest_path = project_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path) as mf:
                        import json as _json

                        manifest = _json.load(mf)
                    project_name = manifest.get("project_name", f"project-{project_id}")
                except Exception:
                    project_name = f"project-{project_id}"
            else:
                project_name = f"project-{project_id}"

            import tempfile as _tempfile2
            import uuid as _uuid2

            zip_dir = (
                _Path(_tempfile2.mkdtemp())
                / f"{project_name.replace(' ', '_')}-{project_id}-v{_EXPORT_VERSION}.zip"
            )

            try:
                export_service = ProjectExportService()
                export_service.create_zip(project_dir, zip_dir, project_name, project_id)

                def stream_gen():
                    with open(zip_dir, "rb") as zf:
                        while chunk := zf.read(8192):
                            yield chunk

                return StreamingResponse(
                    stream_gen(),
                    media_type="application/zip",
                    headers={
                        "Content-Disposition": f'attachment; filename="{project_name.replace(" ", "_")}-{project_id}-v{_EXPORT_VERSION}.zip"'
                    },
                )
            except Exception:
                try:
                    if zip_dir.exists():
                        zip_dir.unlink()
                except OSError:
                    pass
                try:
                    if zip_dir.parent.exists():
                        zip_dir.parent.rmdir()
                except OSError:
                    pass
                raise HTTPException(status_code=500, detail="Failed to create export archive")

    return router
