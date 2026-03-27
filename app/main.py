from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .inference import build_inference_backend
from .middleware.auth import AuthMiddleware
from .middleware.path_traversal import PathTraversalMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .api import (
    build_jobs_router,
    build_models_router,
    build_projects_router,
    build_story_development_router,
    build_role_model_checker_router,
)
from .settings import settings
from .persistence.story_development import StoryDevelopmentRepository
from .services import JobManager, ModelRegistry, ProjectService, RoleModelCheckManager, RoleModelCheckerService
from .services import LocalExecutor
from .services.config_validator import validate_config_at_startup


# Maximum request body size: 10 MB
MAX_BODY_SIZE = 10 * 1024 * 1024


def build_app() -> FastAPI:
    # Validate configuration at startup (REL-07)
    validate_config_at_startup()
    
    root = Path(__file__).resolve().parents[1]
    data_root = root / 'data'
    models_root = data_root / 'models'
    frontend_root = root / 'frontend'

    project_service = ProjectService(root)
    project_service.reconcile_projects()
    job_manager = JobManager(root / 'data' / 'state' / 'narrative_ops.db')
    story_development_repository = StoryDevelopmentRepository(root / 'data' / 'state' / 'narrative_ops.db')
    inferencer = build_inference_backend(settings)
    model_registry = ModelRegistry(models_root, inferencer=inferencer)
    role_check_manager = RoleModelCheckManager(root / 'data' / 'state' / 'narrative_ops.db')
    role_check_service = RoleModelCheckerService(
        models_root,
        root / 'data' / 'role_model_checker_runs',
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
        expose_headers=['X-Total-Count', 'X-Page', 'X-Per-Page'],
    )

    # Add authentication middleware (skips /health endpoint)
    if settings.api_key:
        app.add_middleware(AuthMiddleware, api_key=settings.api_key)

    # Add rate limiting middleware (SEC-05) - after auth so limits apply per authenticated client
    app.add_middleware(RateLimitMiddleware)

    app.include_router(build_projects_router(project_service))
    app.include_router(build_jobs_router(job_manager))
    app.include_router(build_models_router(model_registry))
    app.include_router(build_story_development_router(story_development_repository))
    app.include_router(build_role_model_checker_router(role_check_manager, role_check_service))

    if frontend_root.exists():
        app.mount('/static', StaticFiles(directory=frontend_root), name='static')

        @app.get('/', include_in_schema=False)
        @app.get('/role-model-checker-ui', include_in_schema=False)
        def serve_frontend() -> FileResponse:
            return FileResponse(frontend_root / 'index.html')

    @app.get('/health')
    def health() -> dict[str, str]:
        return {'status': 'ok', 'mode': 'local'}

    return app
