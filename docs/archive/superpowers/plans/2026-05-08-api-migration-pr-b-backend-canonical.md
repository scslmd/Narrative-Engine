# API Migration PR-B: Backend Canonical Routes Implementation Plan
Status: Planned

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Canonicalize all projects/auth/backup endpoints under `/v1`, make the health versioning decision, add legacy compatibility wrappers with deprecation headers, and update OpenAPI metadata.

**Architecture:** Each router module in `app/api/` gains `/v1` route registrations alongside existing unversioned routes. The pattern follows the existing dual-registration already used for `jobs`, `story-development`, and `role-model-checker` in `app/main.py` (e.g., `build_jobs_router(job_manager)` + `build_jobs_router(job_manager, prefix='/v1/jobs')`). Legacy routes become thin wrappers that forward to canonical handlers and inject deprecation headers. Health endpoints are explicitly exempted from versioning per policy.

**Tech Stack:** FastAPI, Python 3.12+, Pydantic, pytest.

**Cross-plan dependencies:** Depends on PR-A completing (needs `v1_gap_checklist.md` and `legacy_to_v1_mapping.md`). Can run before PR-C and PR-D.

---

## Task 006: Canonicalize Projects Endpoints

**Purpose:** Add/confirm `/v1/projects/*` canonical surface with full parity.

**Write scope:**
- `app/api/projects.py` (modify — add `/v1` prefix support to router builder)
- `app/main.py` (modify — add dual registration for projects router)
- `tests/test_projects_api.py` (modify or create route-level tests)

**Steps:**

- [ ] Update `build_projects_router` in `app/api/projects.py` to accept an optional `prefix` parameter. The current router uses `APIRouter(prefix="/projects", ...)`. Change to:

```python
def build_projects_router(
    project_service,
    *,
    prefix: str = "/projects",
    import_service=None,
    mythos_service=None,
    pattern_service=None,
    import_job_manager=None,
    extraction_job_manager=None,
    maintenance_service=None,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["projects"])
    # ... existing route definitions unchanged
```

- [ ] Update `app/main.py` to dual-register the projects router:

```python
# In build_app(), replace the single registration:
#   app.include_router(build_projects_router(project_service, ...))
# With:
app.include_router(build_projects_router(project_service, import_service=import_service, mythos_service=mythos_service, pattern_service=pattern_service, import_job_manager=import_job_manager, extraction_job_manager=extraction_job_manager, maintenance_service=maintenance_service))
app.include_router(build_projects_router(project_service, prefix="/v1/projects", import_service=import_service, mythos_service=mythos_service, pattern_service=pattern_service, import_job_manager=import_job_manager, extraction_job_manager=extraction_job_manager, maintenance_service=maintenance_service))
```

- [ ] Also dual-register the inline project routes in `app/main.py` (lines 459-486). Move `list_projects`, `get_project`, `get_sequence`, `get_chapter`, and `get_models` into a dedicated router or register them under both `/projects` and `/v1/projects`. The cleanest approach is to create a small `app/api/project_artifacts.py` module:

```python
"""Project artifact endpoints (list, get, sequence, chapter)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["project-artifacts"])


def build_project_artifact_router(project_service, model_registry, *, prefix: str = "") -> APIRouter:
    rtr = APIRouter(prefix=prefix, tags=["project-artifacts"])

    from app.schemas.projects import ProjectSummaryResponse, ProjectDetailResponse, ProjectArtifactResponse
    from app.schemas.models import ModelCatalogResponse

    @rtr.get("/projects", response_model=list[ProjectSummaryResponse])
    def list_projects() -> list[ProjectSummaryResponse]:
        return project_service.list_projects()

    @rtr.get("/projects/{project_id}", response_model=ProjectDetailResponse)
    def get_project(project_id: str) -> ProjectDetailResponse:
        try:
            return project_service.get_project(project_id)
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @rtr.get("/projects/{project_id}/sequence", response_model=ProjectArtifactResponse)
    def get_sequence(project_id: str) -> ProjectArtifactResponse:
        try:
            return project_service.read_artifact(project_id, "sequence")
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @rtr.get("/projects/{project_id}/chapter-1", response_model=ProjectArtifactResponse)
    def get_chapter(project_id: str) -> ProjectArtifactResponse:
        try:
            return project_service.read_artifact(project_id, "chapter-1")
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @rtr.get("/models", response_model=ModelCatalogResponse)
    def get_models() -> ModelCatalogResponse:
        return model_registry.build_catalog()

    return rtr
```

- [ ] In `app/main.py`, register both versions and remove the inline decorators:

```python
from app.api.project_artifacts import build_project_artifact_router
# ... inside build_app():
app.include_router(build_project_artifact_router(project_service, model_registry))
app.include_router(build_project_artifact_router(project_service, model_registry, prefix="/v1"))
```

- [ ] Verify: `python -m pytest -q -p no:cacheprovider tests/test_projects_api.py` (if test file exists) or run the full parallel cluster to verify no regressions.

**Acceptance criteria:**
- All project endpoints accessible at both `/projects/*` and `/v1/projects/*`.
- Response payloads are identical for both paths.
- Full backend test suite passes with 0 new failures.

---

## Task 007: Canonicalize Auth Endpoints

**Purpose:** Add/confirm `/v1/auth/*` canonical routes.

**Write scope:**
- `app/api/auth.py` (modify — add prefix parameter to router)
- `app/main.py` (modify — dual-register auth router)
- `tests/test_authentication.py` (existing tests should cover both paths)

**Steps:**

- [ ] Update `app/api/auth.py` router definition. Change:

```python
# Current:
router = APIRouter(prefix="/auth", tags=["authentication"])
```

To a factory pattern matching other routers:

```python
def build_auth_router(*, prefix: str = "/auth") -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["authentication"])
    # Move all existing route decorators from module-level @router to @router inside this function
    return router
```

- [ ] Refactor `app/api/auth.py` to use the factory:

```python
"""Authentication API endpoints (SEC-02)."""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException, status

from ..services.authentication import AuthenticationError, get_auth_service


@dataclass
class CreateAPIKeyRequest:
    name: str
    owner_id: str | None = None
    permissions: list[str] = field(default_factory=lambda: ["read", "write"])
    expires_in_days: int | None = None


@dataclass
class CreateAPIKeyResponse:
    key_id: str
    prefix: str
    full_key: str
    name: str
    permissions: list[str]
    created_at: str
    expires_at: str | None


def build_auth_router(*, prefix: str = "/auth") -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["authentication"])

    @router.post("/keys", response_model=CreateAPIKeyResponse, status_code=status.HTTP_201_CREATED)
    async def create_api_key(request: CreateAPIKeyRequest) -> CreateAPIKeyResponse:
        # ... existing implementation unchanged
        pass

    @router.get("/keys")
    async def list_api_keys(owner_id: str | None = None) -> dict:
        # ... existing implementation unchanged
        pass

    @router.delete("/keys/{prefix}")
    async def revoke_api_key(prefix: str) -> dict:
        # ... existing implementation unchanged
        pass

    return router


# Keep backward-compatible module-level import
router = build_auth_router()
```

- [ ] Update `app/main.py` auth registration:

```python
from app.api.auth import build_auth_router
# Replace:
#   app.include_router(auth_router)
# With:
app.include_router(build_auth_router())
app.include_router(build_auth_router(prefix="/v1/auth"))
```

- [ ] Verify: `python -m pytest -q -p no:cacheprovider tests/test_authentication.py`

**Acceptance criteria:**
- All auth endpoints accessible at both `/auth/*` and `/v1/auth/*`.
- Status codes (`201`, `400`, `404`, `500`) are identical for both paths.
- Auth test suite passes with 0 new failures.

---

## Task 008: Canonicalize Backup Endpoints

**Purpose:** Add/confirm `/v1/backup/*` canonical routes.

**Write scope:**
- `app/api/backup.py` (modify — factory pattern with prefix parameter)
- `app/main.py` (modify — dual-register backup router)
- `tests/test_backup.py` (existing tests should cover both paths)

**Steps:**

- [ ] Refactor `app/api/backup.py` to use a factory:

```python
"""Backup API endpoints (REL-04)."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..services.backup import BackupError, get_backup_service


def build_backup_router(*, prefix: str = "/backup") -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["backup"])

    @router.post("/create")
    async def create_backup(description: str | None = None) -> dict:
        try:
            service = get_backup_service()
            result = service.create_backup(description=description)
            return result
        except BackupError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.post("/restore/{backup_id}")
    async def restore_backup(backup_id: str) -> dict:
        try:
            service = get_backup_service()
            result = service.restore_backup(backup_id)
            return result
        except BackupError as e:
            raise HTTPException(status_code=404 if "not found" in str(e).lower() else 500, detail=str(e)) from e

    @router.get("/list")
    async def list_backups() -> dict:
        try:
            service = get_backup_service()
            backups = service.list_backups()
            return {"backups": backups, "count": len(backups)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.get("/latest")
    async def get_latest_backup() -> dict | None:
        try:
            service = get_backup_service()
            latest = service.get_latest_backup()
            return latest
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.delete("/{backup_id}")
    async def delete_backup(backup_id: str) -> dict:
        try:
            service = get_backup_service()
            deleted = service.delete_backup(backup_id)
            if not deleted:
                raise HTTPException(status_code=404, detail=f"Backup not found: {backup_id}")
            return {"deleted": backup_id, "status": "success"}
        except BackupError as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=str(e)) from e
            raise HTTPException(status_code=500, detail=str(e)) from e

    return router


# Keep backward-compatible module-level import
router = build_backup_router()
```

- [ ] Update `app/main.py` backup registration:

```python
from app.api.backup import build_backup_router
# Replace:
#   app.include_router(backup_router)
# With:
app.include_router(build_backup_router())
app.include_router(build_backup_router(prefix="/v1/backup"))
```

- [ ] Verify: `python -m pytest -q -p no:cacheprovider tests/test_backup.py`

**Acceptance criteria:**
- All backup endpoints accessible at both `/backup/*` and `/v1/backup/*`.
- Status codes are identical for both paths.
- Backup test suite passes with 0 new failures.

---

## Task 009: Health Versioning Decision & Implementation

**Purpose:** Make health route policy explicit and enforce it. Per compatibility policy, health endpoints are explicitly exempted from versioning.

**Write scope:**
- `app/api/health.py` (modify — add `deprecated=False` explicit metadata)
- `docs/api-migration/compatibility_policy.md` (already written in PR-A Task 004)
- No new tests required (health tests are part of the smoke suite).

**Steps:**

- [ ] Add explicit OpenAPI metadata to health router to document the exemption:

```python
# In app/api/health.py, update the router creation:
router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={999: {"description": "Health endpoints are intentionally unversioned per compatibility policy. See docs/api-migration/compatibility_policy.md"}},
)
```

- [ ] Add docstring comments to each health endpoint noting the exemption:

```python
@router.get("/", deprecated=False, summary="Liveness probe (unversioned by policy)")
async def health_check() -> dict:
    """Basic liveness probe. Unversioned per compatibility policy."""
    return {"status": "ok"}
```

- [ ] Verify no health routes appear in the `v1_gap_checklist.md` as missing. The gap checklist should classify `/health/*` as `internal` (handled by Task 002's classification script).

**Acceptance criteria:**
- Health endpoints remain at `/health/*` only (no `/v1/health` duplicates).
- OpenAPI docs explicitly mark health as unversioned by policy.
- No health routes in the gap checklist's "missing" section.
- `python -m pytest -q -p no:cacheprovider tests/test_smoke.py` passes.

---

## Task 010: Legacy Compatibility Wrappers with Deprecation Headers

**Purpose:** Inject deprecation headers on all legacy (unversioned) wrapper routes that have a `/v1` counterpart.

**Write scope:**
- `app/api/deprecation.py` (new — shared helper module)
- All legacy router modules in `app/api/` (modify — wrap legacy routes)

**Steps:**

- [ ] Create `app/api/deprecation.py`:

```python
"""Shared deprecation header injection for legacy API routes."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from email.utils import format_datetime

from fastapi import Request, Response


# Default sunset date: 30 days from deployment
DEFAULT_SUNSET_DAYS = 30


def add_deprecation_headers(
    response: Response,
    request: Request,
    sunset_days: int = DEFAULT_SUNSET_DAYS,
) -> None:
    """Add Deprecation, Sunset, and Link headers to a legacy route response.

    Args:
        response: The FastAPI response object to modify.
        request: The current request (used to compute successor path).
        sunset_days: Days until removal (default 30).
    """
    now = datetime.now(timezone.utc)
    sunset_date = now + timedelta(days=sunset_days)
    sunset_http = format_datetime(sunset_date)

    # Compute successor path: prepend /v1 to current path
    legacy_path = request.url.path
    if legacy_path.startswith("/"):
        successor_path = "/v1" + legacy_path
    else:
        successor_path = "/v1/" + legacy_path

    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = sunset_http
    response.headers["Link"] = f'<{successor_path}>; rel="successor-version"'


```

- [ ] Apply deprecation headers to legacy project artifact routes. In `app/api/project_artifacts.py`, add a middleware-style wrapper for the non-`/v1` registration:

```python
# In app/api/project_artifacts.py, for the legacy prefix="":
from fastapi import Response
from app.api.deprecation import add_deprecation_headers

@rtr.get("/projects", response_model=list[ProjectSummaryResponse])
async def list_projects(response: Response, request: Request) -> list[ProjectSummaryResponse]:
    add_deprecation_headers(response, request)
    return project_service.list_projects()
```

- [ ] Apply the same pattern to auth and backup legacy routes. Each legacy handler adds `response: Response` and `request: Request` parameters and calls `add_deprecation_headers(response, request)` before returning.

- [ ] Verify deprecation headers are present on legacy routes:

```powershell
python -c "
from fastapi.testclient import TestClient
from app.main import build_app
client = TestClient(build_app())
# Test a legacy route (e.g., GET /health/ is exempted, so test /auth/keys)
resp = client.get('/auth/keys')
assert 'Deprecation' in resp.headers, f'Missing Deprecation header: {dict(resp.headers)}'
assert 'Sunset' in resp.headers, f'Missing Sunset header: {dict(resp.headers)}'
assert 'Link' in resp.headers, f'Missing Link header: {dict(resp.headers)}'
assert resp.headers['Link'].startswith('</v1/auth/keys>'), f'Wrong successor: {resp.headers[\"Link\"]}'
print('Deprecation headers present on legacy routes - PASS')
"
```

**Acceptance criteria:**
- All legacy (non-`/v1`) routes with a `/v1` counterpart return `Deprecation`, `Sunset`, and `Link` headers.
- Health endpoints do NOT have deprecation headers (exempted).
- Successor `Link` header points to the correct `/v1` path.
- Full backend test suite passes.

---

## Task 011: OpenAPI Canonicalization

**Purpose:** Mark legacy endpoints as deprecated in OpenAPI docs and ensure canonical `/v1` endpoints are primary.

**Write scope:**
- Route decorators in `app/api/*.py` (modify — add `deprecated=True` to legacy routes)
- `app/main.py` (modify — optional OpenAPI config)

**Steps:**

- [ ] Add `deprecated=True` to all legacy route decorators. For example, in `app/api/auth.py`:

```python
# Legacy router (prefix="/auth"):
@router.get("/keys", deprecated=True)
async def list_api_keys(owner_id: str | None = None) -> dict:
    ...
```

- [ ] Ensure `/v1` routes have `deprecated=False` (default, but explicit for clarity):

```python
# Canonical router (prefix="/v1/auth"):
@router.get("/keys", deprecated=False)
async def list_api_keys(owner_id: str | None = None) -> dict:
    ...
```

- [ ] Verify OpenAPI output:

```powershell
python -c "
from app.main import build_app
app = build_app()
o = app.openapi()
paths = o.get('paths', {})
print(f'Total paths in OpenAPI: {len(paths)}')

# Check that legacy routes have deprecated=True
legacy_deprecated = 0
v1_present = 0
for path, methods in paths.items():
    if '/v1/' in path:
        v1_present += 1
    elif path.startswith('/auth') or path.startswith('/backup') or path.startswith('/projects'):
        for method_spec in methods.values():
            if isinstance(method_spec, dict) and method_spec.get('deprecated', False):
                legacy_deprecated += 1

print(f'Legacy routes marked deprecated: {legacy_deprecated}')
print(f'/v1 routes present: {v1_present}')
assert v1_present > 0, 'No /v1 routes in OpenAPI'
print('OpenAPI canonicalization - PASS')
"
```

**Acceptance criteria:**
- All legacy routes show `deprecated: true` in OpenAPI JSON.
- All `/v1` routes show `deprecated: false` (or no deprecated field).
- OpenAPI schema is valid and loadable.
- `python -m pytest -q -p no:cacheprovider` passes with 0 new failures.
