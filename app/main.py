from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import (
    build_jobs_router,
    build_models_router,
    build_projects_router,
    build_role_model_checker_router,
)
from .services import JobManager, ModelRegistry, ProjectService, RoleModelCheckManager, RoleModelCheckerService


def build_app() -> FastAPI:
    root = Path(__file__).resolve().parents[1]
    data_root = root / 'data'
    models_root = data_root / 'models'
    frontend_root = root / 'frontend'

    project_service = ProjectService(root)
    job_manager = JobManager(root / 'data' / 'state' / 'narrative_ops.db')
    model_registry = ModelRegistry(models_root)
    role_check_manager = RoleModelCheckManager(root / 'data' / 'state' / 'narrative_ops.db')
    role_check_service = RoleModelCheckerService(models_root, root / 'data' / 'role_model_checker_runs')

    app = FastAPI(title='Narrative-Core Recovered', version='0.1.0-recovered')
    app.include_router(build_projects_router(project_service))
    app.include_router(build_jobs_router(job_manager))
    app.include_router(build_models_router(model_registry))
    app.include_router(build_role_model_checker_router(role_check_manager, role_check_service))

    if frontend_root.exists():
        app.mount('/static', StaticFiles(directory=frontend_root), name='static')

        @app.get('/', include_in_schema=False)
        @app.get('/role-model-checker-ui', include_in_schema=False)
        def serve_frontend() -> FileResponse:
            return FileResponse(frontend_root / 'index.html')

    @app.get('/health')
    def health() -> dict[str, str]:
        return {'status': 'ok', 'mode': 'recovered'}

    return app


app = build_app()
