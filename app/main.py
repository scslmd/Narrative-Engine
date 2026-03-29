from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .middleware.path_traversal import PathTraversalMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .api import (
    build_jobs_router,
    build_models_router,
    build_projects_router,
    build_story_development_router,
    build_role_model_checker_router,
)
from .api.auth import router as auth_router
from .api.backup import router as backup_router
from .api.health import router as health_router
from .schemas.models import ModelCatalogResponse
from .schemas.projects import (
    ProjectArtifactResponse,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectSummaryResponse,
)
from .settings import settings
from .persistence.story_development import StoryDevelopmentRepository
from .services.authentication import fingerprint_api_key


# Maximum request body size: 10 MB
MAX_BODY_SIZE = 10 * 1024 * 1024


def build_app() -> FastAPI:
    from .inference import build_inference_backend
    from .services.config_validator import validate_config_at_startup
    from .services.job_manager import JobManager
    from .services.local_executor import LocalExecutor
    from .services.model_registry import ModelRegistry
    from .services.projects import ProjectService
    from .services.role_model_check_manager import RoleModelCheckManager
    from .services.role_model_checker import RoleModelCheckerService

    # Validate configuration at startup (REL-07)
    validate_config_at_startup()
    
    data_root = settings.data_dir
    models_root = data_root / 'models'
    frontend_root = settings.frontend_dir
    frontend_dist_root = frontend_root / 'dist'
    frontend_serve_root = frontend_dist_root if frontend_dist_root.exists() else frontend_root
    frontend_asset_root = frontend_dist_root / 'assets' if frontend_dist_root.exists() else None
    frontend_index = frontend_serve_root / 'index.html'

    project_service = ProjectService(settings.root_dir)
    project_service.reconcile_projects()
    job_manager = JobManager(settings.operations_db_path)
    story_development_repository = StoryDevelopmentRepository(settings.operations_db_path)
    inferencer = build_inference_backend(settings)
    model_registry = ModelRegistry(models_root, inferencer=inferencer)
    role_check_manager = RoleModelCheckManager(settings.operations_db_path)
    role_check_service = RoleModelCheckerService(
        models_root,
        settings.role_model_reports_dir,
        inferencer=inferencer,
        model_registry=model_registry,
    )
    local_executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=role_check_manager,
        role_check_service=role_check_service,
        inferencer=inferencer,
        project_service=project_service,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        local_executor.start()
        try:
            yield
        finally:
            local_executor.stop()

    app = FastAPI(
        title='Narrative-Engine',
        version='0.1.0',
        lifespan=lifespan,
        max_body_size=MAX_BODY_SIZE,
    )

    # Add path traversal protection middleware (SEC-04) - must be first
    app.add_middleware(PathTraversalMiddleware)

    # Add CORS middleware first (before auth so OPTIONS preflight works without auth)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:3000', 'http://127.0.0.1:3000'],
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Authorization', 'Content-Type', 'X-Requested-With', 'X-API-Key'],
        expose_headers=['X-Total-Count', 'X-Page', 'X-Per-Page', '/health'],
    )

    # Add rate limiting middleware (SEC-05)
    app.add_middleware(RateLimitMiddleware)

    # Add audit logging middleware (REL-10)
    @app.middleware("http")
    async def audit_logging_middleware(request: Request, call_next):
        """Log all versioned API requests to structured log file (REL-10).
        
        Records:
        - timestamp
        - HTTP method
        - request path
        - response status code
        - API key fingerprint (if authenticated)
        """
        # Only log versioned API requests
        if not request.url.path.startswith('/v1'):
            return await call_next(request)
        
        # Get API key fingerprint if present
        api_key = request.headers.get('X-API-Key')
        api_key_fingerprint = None
        if api_key:
            api_key_fingerprint = fingerprint_api_key(api_key)
        
        # Record start time for duration calculation
        import time
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Build audit record
        audit_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "api_key_fingerprint": api_key_fingerprint,
        }
        
        # Extract target_resource from path and query params
        path_parts = request.url.path.split('/')
        if len(path_parts) > 2 and path_parts[1] == 'v1':
            try:
                if path_parts[2] == 'projects' and len(path_parts) > 3:
                    audit_record["project_id"] = path_parts[3]
                    audit_record["target_resource"] = f"project:{path_parts[3]}"
                elif path_parts[2] == 'jobs' and len(path_parts) > 3:
                    audit_record["target_resource"] = f"job:{path_parts[3]}"
                elif path_parts[2] == 'role-model-checker' and len(path_parts) > 3:
                    audit_record["target_resource"] = f"role_model_check:{path_parts[3]}"
                elif path_parts[2] == 'story-development':
                    project_id = request.query_params.get('project_id')
                    if project_id:
                        audit_record["project_id"] = project_id
                        audit_record["target_resource"] = f"story_project:{project_id}"
            except (IndexError, KeyError):
                pass
        
        # Write to structured log file
        try:
            from pathlib import Path
            log_path = Path(settings.structured_log_filename)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_path, 'a') as f:
                f.write(json.dumps(audit_record) + '\n')
        except Exception:
            # Don't fail the request if logging fails
            pass
        
        return response

    if settings.api_key:
        @app.middleware("http")
        async def versioned_api_key_gate(request: Request, call_next):
            if request.url.path.startswith('/v1'):
                api_key = request.headers.get('X-API-Key')
                if api_key != settings.api_key:
                    return JSONResponse(
                        status_code=401,
                        content={'detail': 'Invalid or missing API key'},
                        headers={'WWW-Authenticate': 'Bearer'},
                    )
            return await call_next(request)

    @app.get('/projects', response_model=list[ProjectSummaryResponse])
    def list_projects() -> list[ProjectSummaryResponse]:
        return project_service.list_projects()

    @app.post('/projects/create', response_model=ProjectDetailResponse)
    def create_project(request: ProjectCreateRequest) -> ProjectDetailResponse:
        try:
            return project_service.create_project(request)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get('/projects/{project_id}', response_model=ProjectDetailResponse)
    def get_project(project_id: str) -> ProjectDetailResponse:
        try:
            return project_service.get_project(project_id)
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get('/projects/{project_id}/manifest', response_model=ProjectArtifactResponse)
    def get_manifest(project_id: str) -> ProjectArtifactResponse:
        try:
            return project_service.read_artifact(project_id, 'manifest')
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get('/projects/{project_id}/sequence', response_model=ProjectArtifactResponse)
    def get_sequence(project_id: str) -> ProjectArtifactResponse:
        try:
            return project_service.read_artifact(project_id, 'sequence')
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get('/projects/{project_id}/chapter-1', response_model=ProjectArtifactResponse)
    def get_chapter(project_id: str) -> ProjectArtifactResponse:
        try:
            return project_service.read_artifact(project_id, 'chapter-1')
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get('/models', response_model=ModelCatalogResponse)
    def get_models() -> ModelCatalogResponse:
        return model_registry.build_catalog()

    app.include_router(auth_router)  # Authentication endpoints (SEC-02)
    app.include_router(backup_router)  # Backup endpoints (REL-04)
    app.include_router(health_router)  # Health endpoints (REL-05, REL-06)
    app.include_router(build_projects_router(project_service))
    app.include_router(build_jobs_router(job_manager))
    app.include_router(build_jobs_router(job_manager, prefix='/v1/jobs'))
    app.include_router(build_models_router(model_registry))
    app.include_router(build_story_development_router(story_development_repository))
    app.include_router(build_story_development_router(story_development_repository, prefix='/v1/story-development'))
    app.include_router(build_role_model_checker_router(role_check_manager, role_check_service))
    app.include_router(build_role_model_checker_router(role_check_manager, role_check_service, prefix='/v1/role-model-checker'))

    if frontend_index.exists():
        if frontend_asset_root and frontend_asset_root.exists():
            app.mount('/assets', StaticFiles(directory=frontend_asset_root), name='assets')
            app.mount('/static', StaticFiles(directory=frontend_serve_root), name='static')

            @app.get('/vite.svg', include_in_schema=False)
            def serve_vite_icon() -> FileResponse:
                return FileResponse(frontend_serve_root / 'vite.svg')
        else:
            app.mount('/static', StaticFiles(directory=frontend_root), name='static')

        @app.get('/', include_in_schema=False)
        @app.get('/role-model-checker-ui', include_in_schema=False)
        def serve_frontend() -> FileResponse:
            return FileResponse(frontend_index)

    return app
