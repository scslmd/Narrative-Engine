from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .inference import build_inference_backend
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


def build_app() -> FastAPI:
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

    app = FastAPI(title='Narrative-Engine', version='0.1.0', lifespan=lifespan)
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


app = build_app()
