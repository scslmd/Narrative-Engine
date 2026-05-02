from __future__ import annotations

import hmac
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .middleware.path_traversal import PathTraversalMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .api import (
    build_canon_customization_router,
    build_jobs_router,
    build_manuscript_assist_router,
    build_models_router,
    build_mythos_library_router,
    build_pattern_library_router,
    build_projects_router,
    build_story_generation_router,
    build_story_development_router,
    build_role_model_checker_router,
)
from .api.auth import router as auth_router
from .api.backup import router as backup_router
from .api.health import router as health_router
from .schemas.models import ModelCatalogResponse
from .schemas.projects import (
    ProjectArtifactResponse,
    ProjectDetailResponse,
    ProjectSummaryResponse,
)
from .constants import MAX_BODY_SIZE
from .settings import settings
from .persistence.story_development import StoryDevelopmentRepository
from .services.authentication import fingerprint_api_key


def _is_id_or_title_segment(segment: str) -> bool:
    """Check if a path segment looks like an ID or title that should be stripped."""
    from .constants import UUID_LENGTH

    if len(segment) == UUID_LENGTH and segment.count('-') == 4:
        return True
    # Numeric IDs
    if segment.isdigit():
        return True
    # Single word segments that don't look like resource types are likely IDs/titles
    # We check against known resource type patterns
    resource_types = {
        'characters', 'decisions', 'findings', 'inspect_links', 'inspect-links',
        'world_bible', 'world-bible', 'branches', 'branches', 'state-refs',
        'relationships', 'read', 'create', 'update', 'delete', 'status', 'logs',
        'steps', 'lineage', 'attempts', 'retry', 'start', 'run', 'list', 'manifest',
        'sequence', 'chapter-1', 'chapter-2', 'chapter-3', 'chapter-4', 'chapter-5',
        'draft-artifacts', 'revision-suggestions', 'manuscript-documents',
        'story-branches', 'branch-comparisons', 'merge-decisions', 'active',
        'stage-maps', 'candidates', 'selections', 'items', 'promotions', 'clusters',
        'plan', 'plans', 'scene-plans', 'chapter-plans', 'sequence-plans',
        'dependencies', 'chapter-packets', 'decisions', 'findings', 'inspect-links',
        'review', 'brainstorm', 'foundation', 'characters', 'world-bible', 'arcs',
        'branches', 'drafting', 'planning', 'review', 'inspect', 'inspects',
    }
    # Convert segment to check against resource types
    normalized = segment.replace('-', '_').replace('/', '')
    if normalized in resource_types:
        return False
    # If it's a short segment that's not a known resource type, it's likely an ID/title
    # Allow up to 3 hyphenated parts (e.g., "test-character-id" is an ID)
    if len(segment.split('-')) <= 3 and len(segment) < 50:
        return True
    return False


def _normalize_operation(method: str, path: str) -> str:
    """Normalize a method+path into a stable operation name.
    
    Examples:
    - POST /v1/jobs/create -> job.create
    - GET /v1/jobs/{job_id}/status -> job.status.read
    - GET /v1/story-development/drafting/draft-artifacts -> story_development.drafting.draft_artifacts.read
    """
    path_parts = path.split('/')
    
    # Handle /v1/projects routes (unversioned routes preserved for backward compatibility - compatibility handling for legacy audit entries)
    if len(path_parts) >= 3 and path_parts[2] == 'projects':
        if method == 'POST' and len(path_parts) >= 4 and path_parts[3] == 'create':
            return 'project.create'
        elif method == 'GET' and len(path_parts) == 3:
            return 'project.list'
        elif method == 'GET' and len(path_parts) >= 4:
            # For /v1/projects/{id}/{artifact}, extract just the artifact name
            if len(path_parts) == 5:
                artifact = path_parts[4]
            else:
                artifact = '/'.join(path_parts[3:])
            return f'project_artifact.{artifact.replace("-", "_")}.read'
        elif method == 'DELETE':
            return 'project.delete'
    
    # Handle /v1/jobs routes
    if len(path_parts) >= 3 and path_parts[2] == 'jobs':
        if method == 'POST' and len(path_parts) >= 4 and path_parts[3] == 'create':
            return 'job.create'
        elif method == 'GET' and len(path_parts) == 3:
            return 'job.list'
        elif len(path_parts) >= 5:
            subresource = path_parts[4] if len(path_parts) > 4 else ''
            op_map = {
                'status': 'job.status.read',
                'logs': 'job.logs.read',
                'steps': 'job.steps.read',
                'lineage': 'job.lineage.read',
                'attempts': 'job.attempts.read',
            }
            if subresource in op_map:
                return op_map[subresource]
            elif method == 'POST' and subresource == 'retry':
                return 'job.retry'
    
    # Handle /v1/role-model-checker routes
    if len(path_parts) >= 3 and path_parts[2] == 'role-model-checker':
        if method == 'POST' and len(path_parts) >= 4:
            action = path_parts[3]
            if action in ('start', 'run'):
                return 'role_model_check.create'
        elif len(path_parts) >= 5:
            subresource = path_parts[4] if len(path_parts) > 4 else ''
            op_map = {
                'status': 'role_model_check.status.read',
                'logs': 'role_model_check.logs.read',
                'steps': 'role_model_check.steps.read',
                'lineage': 'role_model_check.lineage.read',
                'attempts': 'role_model_check.attempts.read',
            }
            if subresource in op_map:
                return op_map[subresource]
            elif method == 'POST' and subresource == 'retry':
                return 'role_model_check.retry'
    
    # Handle /v1/story-development routes
    if len(path_parts) >= 3 and path_parts[1] == 'v1' and path_parts[2] == 'story-development':
        if len(path_parts) >= 4:
            subservice = path_parts[3]
            resource_parts = path_parts[4:]
            
            # Normalize subservice (replace hyphens with underscores)
            subservice_normalized = subservice.replace('-', '_')
            
            # Build resource name from remaining parts (strip IDs/titles for stable operations)
            if resource_parts and resource_parts[0]:
                # Map detail route resource types to stable names (strip IDs/titles)
                # The subservice itself is the resource type for story-development routes
                detail_resource_map = {
                    'characters': 'characters',
                    'decisions': 'decisions',
                    'findings': 'findings',
                    'inspect_links': 'inspect_links',
                    'inspect-links': 'inspect_links',
                    'world_bible': 'world_bible',
                    'world-bible': 'world_bible',
                    'branches': 'branches',
                }
                # Check if subservice or first resource part is in the map
                resource_type = resource_parts[0] if resource_parts else ''
                mapped_type = detail_resource_map.get(subservice) or detail_resource_map.get(resource_type)
                
                if mapped_type:
                    # For detail routes, use stable resource type name
                    # Strip any ID/title segments that follow
                    # Determine which part contains the resource type
                    if subservice in detail_resource_map:
                        # subservice is the resource type (e.g., 'characters')
                        # full_resource = characters
                        parts_to_check = resource_parts[1:] if len(resource_parts) > 1 else []
                    else:
                        # first resource part is the resource type (e.g., 'findings' under 'review')
                        # full_resource = review.findings
                        parts_to_check = resource_parts[1:] if len(resource_parts) > 1 else []
                    
                    # Filter out ID-like segments
                    filtered_sub_resources = []
                    for part in parts_to_check:
                        if not _is_id_or_title_segment(part):
                            filtered_sub_resources.append(part)
                    
                    if filtered_sub_resources:
                        resource_name = '_'.join(filtered_sub_resources).replace('-', '_').replace('/', '_')
                        # Rebuild full_resource with the filtered resource_name
                        if subservice in detail_resource_map:
                            full_resource = f"{mapped_type}.{resource_name}"
                        else:
                            full_resource = f"{subservice_normalized}.{mapped_type}.{resource_name}"
                    else:
                        resource_name = ''
                        if subservice in detail_resource_map:
                            full_resource = f"{mapped_type}"
                        else:
                            full_resource = f"{subservice_normalized}.{mapped_type}"
                else:
                    resource_name = '_'.join(resource_parts).replace('-', '_').replace('/', '_')
                    full_resource = f"{subservice_normalized}.{resource_name}"
            else:
                full_resource = subservice_normalized
            
            # Map HTTP method to operation suffix
            method_suffix_map = {
                'GET': 'read',
                'POST': 'create',
                'PATCH': 'update',
                'PUT': 'update',
                'DELETE': 'delete',
            }
            suffix = method_suffix_map.get(method, 'unknown')
            
            # Return stable operation name without IDs/titles
            return f'story_development.{full_resource}.{suffix}'
    
    # Handle /v1/models routes
    if len(path_parts) >= 3 and path_parts[2] == 'models':
        if method == 'GET':
            return 'model.list.read'
    
    # Fallback: return generic operation based on method
    method_suffix_map = {
        'GET': 'read',
        'POST': 'create',
        'PATCH': 'update',
        'PUT': 'update',
        'DELETE': 'delete',
    }
    suffix = method_suffix_map.get(method, 'unknown')
    return f'unknown.{suffix}'


def build_app(*, start_executor: bool = True) -> FastAPI:
    from .inference import build_inference_backend
    from .services.config_validator import validate_config_at_startup
    from .services.job_manager import JobManager
    from .services.local_executor import LocalExecutor
    from .services.scene_context import SceneContextService
    from .services.consistency_critic import ConsistencyCriticService
    from .services.chapter_summarizer import ChapterSummarizerService
    from .services.entity_intake import EntityIntakeService
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
    from .services.story_import import StoryImportService
    import_service = StoryImportService(
        project_service=project_service,
        repository=story_development_repository,
        inferencer=inferencer,
    )
    from .services.mythos_extraction import MythosExtractionService
    mythos_service = MythosExtractionService(
        project_service=project_service,
        repository=story_development_repository,
        inferencer=inferencer,
    )
    from .services.pattern_extraction import PatternExtractionService
    pattern_service = PatternExtractionService(
        project_service=project_service,
        repository=story_development_repository,
        inferencer=inferencer,
    )
    from .services.import_jobs import ImportJobManager
    import_job_manager = ImportJobManager(max_workers=4, ttl_seconds=300)
    from .services.extraction_jobs import ExtractionJobManager
    extraction_job_manager = ExtractionJobManager(max_workers=2, ttl_seconds=300)
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
        story_repository=story_development_repository,
        scene_context_service=SceneContextService(repository=story_development_repository),
        consistency_critic_service=ConsistencyCriticService(inferencer=inferencer),
        entity_intake_service=EntityIntakeService(inferencer=inferencer),
        chapter_summarizer_service=ChapterSummarizerService(inferencer=inferencer),
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if start_executor:
            local_executor.start()
        try:
            yield
        finally:
            if start_executor:
                local_executor.stop()
            import_job_manager.shutdown(wait=False)
            extraction_job_manager.shutdown(wait=False)

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
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
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
        - duration_ms
        - API key fingerprint (if authenticated)
        - target_resource
        - operation (stable semantic name)
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
        
        # Normalize operation name from method and path
        operation = _normalize_operation(request.method, request.url.path)
        audit_record["operation"] = operation
        
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
            if (
                request.url.path.startswith('/v1')
                or request.url.path == '/projects/import-story'
                or request.url.path.startswith('/projects/import/')
            ):
                api_key = request.headers.get('X-API-Key')
                if api_key is None:
                    return JSONResponse(
                        status_code=401,
                        content={'detail': 'Invalid or missing API key'},
                        headers={'WWW-Authenticate': 'Bearer'},
                    )
                if not hmac.compare_digest(
                    api_key.encode("utf-8"), settings.api_key.encode("utf-8")
                ):
                    return JSONResponse(
                        status_code=401,
                        content={'detail': 'Invalid or missing API key'},
                        headers={'WWW-Authenticate': 'Bearer'},
                    )
            return await call_next(request)

    @app.get('/projects', response_model=list[ProjectSummaryResponse])
    def list_projects() -> list[ProjectSummaryResponse]:
        return project_service.list_projects()

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
    app.include_router(build_projects_router(project_service, import_service=import_service, mythos_service=mythos_service, pattern_service=pattern_service, import_job_manager=import_job_manager, extraction_job_manager=extraction_job_manager))
    app.include_router(build_jobs_router(job_manager))
    app.include_router(build_jobs_router(job_manager, prefix='/v1/jobs'))
    app.include_router(build_models_router(model_registry))
    app.include_router(build_story_development_router(story_development_repository))
    app.include_router(build_story_development_router(story_development_repository, prefix='/v1/story-development'))
    app.include_router(build_story_generation_router(story_development_repository, project_service, job_manager))
    app.include_router(build_manuscript_assist_router(story_development_repository, job_manager))
    app.include_router(build_canon_customization_router(story_development_repository))
    app.include_router(build_mythos_library_router(story_development_repository))
    app.include_router(build_pattern_library_router(story_development_repository))
    app.include_router(build_role_model_checker_router(role_check_manager, role_check_service))
    app.include_router(build_role_model_checker_router(role_check_manager, role_check_service, prefix='/v1/role-model-checker'))

    @app.post('/projects/create/debug', include_in_schema=False)
    async def debug_create_project(request: Request) -> dict:
        body = await request.body()
        return {
            'path': str(request.url.path),
            'method': request.method,
            'body_len': len(body),
            'body': body.decode('utf-8')[:1000],
        }

    # Global 422 logger
    from fastapi.exceptions import RequestValidationError
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        import json as _json
        import logging
        logger = logging.getLogger(__name__)
        try:
            body = await request.body()
            logger.error(f"422 on {request.method} {request.url.path}: body={body.decode('utf-8')[:500]}")
        except Exception:
            logger.error(f"422 on {request.method} {request.url.path}")
        errors = exc.errors()
        for error in errors:
            ctx = error.get("ctx")
            if ctx and isinstance(ctx, dict):
                for k, v in list(ctx.items()):
                    if not isinstance(v, (str, int, float, bool, type(None))):
                        ctx[k] = str(v)
        return JSONResponse(status_code=422, content={"detail": errors})

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

        # Middleware for SPA client-side routing
        _frontend_skip_prefixes = (
            'api', 'v1', 'docs', 'openapi.json', 'redoc', 'swagger',
            'health', 'assets', 'static', 'favicon',
            'jobs', 'projects', 'models', 'role-model-checker',
            'story-development',
        )
        _frontend_skip_extensions = ('.css', '.js', '.svg', '.png', '.jpg', '.ico')

        async def spa_catch_all_middleware(request: Request, call_next):
            path = request.url.path.lstrip('/')
            first_segment = path.split('/')[0] if path else ''
            if first_segment in _frontend_skip_prefixes:
                return await call_next(request)
            for ext in _frontend_skip_extensions:
                if path.endswith(ext):
                    return await call_next(request)
            return FileResponse(frontend_index)

        app.middleware('http')(spa_catch_all_middleware)

    return app
