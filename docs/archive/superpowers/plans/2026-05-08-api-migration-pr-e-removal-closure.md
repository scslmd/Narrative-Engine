# API Migration PR-E: Legacy Removal & Closure Implementation Plan
Status: Completed (2026-05-09)

Completion notes:
- Legacy unversioned wrappers targeted by the migration were removed from active frontend usage and backend canonical routing now serves `/v1/*` surfaces.
- Documentation now treats `/v1/*` as authoritative, with policy exceptions for health and internal UI/static routes.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all legacy (unversioned) API route wrappers, finalize documentation, and run the full merge-readiness verification suite to confirm the migration is complete.

**Architecture:** Two removal batches: Batch 1 removes low-risk wrappers (auth, backup — no business logic coupling). Batch 2 removes project artifact routes and cleans up the deprecation middleware. After removal, regenerate the route inventory to confirm legacy paths are gone. Update all documentation to reference canonical `/v1` endpoints. Run the full AGENTS.md verification suite.

**Tech Stack:** Python 3.12+, FastAPI, pytest, TypeScript.

**Cross-plan dependencies:** Depends on PR-C completing (parity + telemetry gates must pass) AND PR-D completing (frontend must be canonical-only). This is the final PR in the migration sequence.

---

## Task 019: Legacy Removal Batch 1 (Auth & Backup)

**Purpose:** Remove low-risk legacy wrappers for auth and backup endpoints after gate verification.

**Write scope:**
- `app/api/auth.py` (modify — remove legacy router registration or factory default)
- `app/api/backup.py` (modify — remove legacy router registration)
- `app/main.py` (modify — remove non-`/v1` router registrations for auth and backup)
- `tests/test_api_route_parity.py` (modify — update to reflect removal)

**Pre-flight gate check:**

- [ ] Verify parity tests pass: `python -m pytest -q -p no:cacheprovider tests/test_api_route_parity.py`
- [ ] Verify error semantics pass: `python -m pytest -q -p no:cacheprovider tests/test_api_error_semantics.py`

**Steps:**

- [ ] In `app/main.py`, remove the legacy (non-`/v1`) registrations for auth and backup:

```python
# BEFORE:
app.include_router(build_auth_router())           # Legacy /auth/*
app.include_router(build_auth_router(prefix="/v1/auth"))  # Canonical

app.include_router(build_backup_router())          # Legacy /backup/*
app.include_router(build_backup_router(prefix="/v1/backup"))  # Canonical

# AFTER (remove legacy registrations):
app.include_router(build_auth_router(prefix="/v1/auth"))
app.include_router(build_backup_router(prefix="/v1/backup"))
```

- [ ] In `app/api/auth.py`, remove the module-level `router = build_auth_router()` backward-compat export since it's no longer imported by `main.py`:

```python
# Remove this line:
# router = build_auth_router()
```

- [ ] In `app/api/backup.py`, remove the module-level `router = build_backup_router()` backward-compat export.

- [ ] Update `app/main.py` imports to use only the factory functions:

```python
# Before:
from .api.auth import router as auth_router
from .api.backup import router as backup_router

# After:
from .api.auth import build_auth_router
from .api.backup import build_backup_router
```

- [ ] Verify legacy routes are gone and canonical routes work:

```powershell
python -c "
from fastapi.testclient import TestClient
from app.main import build_app
client = TestClient(build_app())

# Legacy auth should be 404
resp = client.get('/auth/keys')
assert resp.status_code == 404, f'Expected 404 for /auth/keys, got {resp.status_code}'

# Canonical auth should work
resp = client.get('/v1/auth/keys')
assert resp.status_code == 200, f'Expected 200 for /v1/auth/keys, got {resp.status_code}'

# Legacy backup should be 404
resp = client.get('/backup/list')
assert resp.status_code == 404, f'Expected 404 for /backup/list, got {resp.status_code}'

# Canonical backup should work
resp = client.get('/v1/backup/list')
assert resp.status_code == 200, f'Expected 200 for /v1/backup/list, got {resp.status_code}'

print('Batch 1 removal verified - PASS')
"
```

- [ ] Run the full backend test suite to catch any tests that still reference legacy paths:

```powershell
python -m pytest -q -p no:cacheprovider tests/test_authentication.py tests/test_backup.py --tb=short
```

**Acceptance criteria:**
- `GET /auth/keys` returns 404 (legacy removed).
- `GET /v1/auth/keys` returns 200 (canonical works).
- `GET /backup/list` returns 404 (legacy removed).
- `GET /v1/backup/list` returns 200 (canonical works).
- Auth and backup test suites pass with 0 failures.
- No import errors from removed module-level `router` exports.

---

## Task 020: Legacy Removal Batch 2 (Projects & Final)

**Purpose:** Complete removal of all remaining legacy routes except policy exceptions (health, SPA routes).

**Write scope:**
- `app/api/project_artifacts.py` (modify — remove legacy prefix registration)
- `app/api/projects.py` (modify — remove legacy prefix default)
- `app/main.py` (modify — remove non-`/v1` project router registrations and inline route handlers)
- `app/api/deprecation.py` (can be removed or kept for future use)

**Steps:**

- [ ] In `app/main.py`, remove legacy project registrations:

```python
# BEFORE:
app.include_router(build_project_artifact_router(project_service, model_registry))  # Legacy
app.include_router(build_project_artifact_router(project_service, model_registry, prefix="/v1"))  # Canonical

app.include_router(build_projects_router(project_service, ...))  # Legacy /projects/*
app.include_router(build_projects_router(project_service, prefix="/v1/projects", ...))  # Canonical

# AFTER (canonical only):
app.include_router(build_project_artifact_router(project_service, model_registry, prefix="/v1"))
app.include_router(build_projects_router(project_service, prefix="/v1/projects", import_service=import_service, mythos_service=mythos_service, pattern_service=pattern_service, import_job_manager=import_job_manager, extraction_job_manager=extraction_job_manager, maintenance_service=maintenance_service))
```

- [ ] Remove the inline project routes from `app/main.py` (the `@app.get('/projects')`, `@app.get('/projects/{project_id}')`, etc. decorators at lines 459-486). These should have been moved to `project_artifacts.py` in PR-B Task 006.

- [ ] Remove the legacy dual-registration for other routers that already had `/v1` counterparts:
  - `build_jobs_router(job_manager)` (legacy) — keep only `build_jobs_router(job_manager, prefix='/v1/jobs')`
  - `build_models_router(model_registry)` (legacy) — remove if now in project_artifacts with `/v1` prefix
  - `build_story_development_router(story_development_repository)` (legacy) — keep only the `/v1` version
  - `build_role_model_checker_router(...)` (legacy) — keep only the `/v1` version

- [ ] Update the API key middleware gate in `app/main.py`. After removal, the gate should only check `/v1/*` paths (remove the special-case exceptions for `/projects/import-story`, etc.):

```python
# BEFORE:
if (
    request.url.path.startswith('/v1')
    or request.url.path == '/projects/import-story'
    or request.url.path.startswith('/projects/import/')
    # ... other legacy exceptions
):

# AFTER (simplified — all protected routes are under /v1):
if request.url.path.startswith('/v1'):
```

- [ ] Regenerate the route inventory and verify legacy paths are absent:

```powershell
python scripts/api_route_inventory.py; python -c "
import json
routes = json.load(open('docs/api-migration/route_inventory.json', 'r', encoding='utf-8'))
legacy = [r for r in routes if not r['path'].startswith('/v1') and not r['path'].startswith('/health') and r['path'] not in ('/', '/role-model-checker-ui', '/vite.svg') and not r['path'].startswith('/assets/') and not r['path'].startswith('/static/') and not r['path'].startswith('/docs') and r['path'] != '/openapi.json' and r['path'] != '/projects/create/debug']
if legacy:
    print(f'FAIL: {len(legacy)} legacy routes remain:')
    for r in legacy:
        print(f'  {r[\"method\"]} {r[\"path\"]}')
else:
    print('All non-essential routes are under /v1 - PASS')
"
```

- [ ] Run the full backend test suite:

```powershell
python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py --ignore=tests/test_smoke.py --ignore=tests/test_local_executor_manuscript_assist.py --ignore=tests/test_story_generation_e2e.py
```

**Acceptance criteria:**
- Regenerated route inventory shows no legacy routes (except health, SPA, and debug endpoints).
- API key middleware gate is simplified to `/v1/*` only.
- Full parallel test cluster passes with 0 new failures.
- All inline route handlers in `app/main.py` are removed or migrated to dedicated router modules.

---

## Task 021: Documentation Finalization

**Purpose:** Align all documentation to the canonical `/v1` contract and provide migration guidance for external consumers.

**Write scope:**
- `AGENTS.md` (modify — update API endpoint references)
- `README.md` (modify — update endpoint examples)
- `docs/api-migration/upgrade_guide.md` (new)

**Steps:**

- [ ] Update `AGENTS.md` API Patterns section. Replace all unversioned endpoint references with `/v1` paths:

```markdown
# Before:
#### Projects
- `GET /projects`
- `POST /projects/create`

# After:
#### Projects
- `GET /v1/projects`
- `POST /v1/projects/create`
```

Apply this pattern to all endpoint sections: Projects, Authentication, Backup, Health (exempted — keep as `/health/*`).

- [ ] Create `docs/api-migration/upgrade_guide.md`:

```markdown
# API Migration Upgrade Guide

## Breaking Changes

As of the `/v1` canonical migration, the following endpoints have moved:

| Legacy Path | New /v1 Path | Status |
|---|---|---|
| `GET /projects` | `GET /v1/projects` | Moved |
| `POST /projects/create` | `POST /v1/projects/create` | Moved |
| `GET /projects/{id}` | `GET /v1/projects/{id}` | Moved |
| `DELETE /projects/{id}` | `DELETE /v1/projects/{id}` | Moved |
| `GET /projects/{id}/manifest` | `GET /v1/projects/{id}/manifest` | Moved |
| `GET /projects/{id}/sequence` | `GET /v1/projects/{id}/sequence` | Moved |
| `POST /auth/keys` | `POST /v1/auth/keys` | Moved |
| `GET /auth/keys` | `GET /v1/auth/keys` | Moved |
| `DELETE /auth/keys/{prefix}` | `DELETE /v1/auth/keys/{prefix}` | Moved |
| `POST /backup/create` | `POST /v1/backup/create` | Moved |
| `GET /backup/list` | `GET /v1/backup/list` | Moved |
| `GET /backup/latest` | `GET /v1/backup/latest` | Moved |
| `DELETE /backup/{id}` | `DELETE /v1/backup/{id}` | Moved |
| `GET /models` | `GET /v1/models` | Moved |

## Unchanged Endpoints

The following endpoints remain unversioned by policy:

- `GET /health/` — Liveness probe
- `GET /health/ready` — Readiness probe
- `GET /health/metrics` — Metrics endpoint
- `GET /health/llm` — LLM connectivity check

## Migration Steps for External Clients

1. Update all API base URLs from `/` to `/v1/` for projects, auth, backup, and models endpoints.
2. Health endpoints remain at `/health/*`.
3. API key authentication (`X-API-Key` header) scope is unchanged — applies to all `/v1/*` paths.
4. Response schemas are identical — no payload changes required.

## Deprecation Timeline

- Legacy routes were deprecated with `Deprecation: true`, `Sunset`, and `Link` response headers.
- Legacy routes have been removed. Clients still using legacy paths will receive 404 responses.
```

- [ ] Verify documentation consistency:

```powershell
# Check for remaining unversioned endpoint references in docs (excluding health)
$files = @("AGENTS.md", "README.md"); foreach ($f in $files) { $content = Get-Content $f -Raw; $matches = [regex]::Matches($content, '(?<!/v1)(?<!/health)/(?:projects|auth|backup)(?![^`'"]*\bv1)'); if ($matches.Count -gt 0) { Write-Warning "$f may have unversioned references: $($matches.Count) potential matches" } else { Write-Host "$f - no obvious legacy references" } }
```

**Acceptance criteria:**
- `AGENTS.md` API Patterns section uses `/v1/*` for all versioned endpoints.
- Health endpoints in docs remain at `/health/*` (exempted).
- `docs/api-migration/upgrade_guide.md` exists with complete migration table.
- No unversioned endpoint references in AGENTS.md for projects, auth, backup, or models.

---

## Task 022: Full Verification & Closure Report

**Purpose:** Run the complete merge-readiness validation suite and produce an audit trail.

**Write scope:**
- `docs/api-migration/verification_report.md` (new — generated report)

**Steps:**

- [ ] Create a verification script that runs all checks and captures output:

```python
"""Run full API migration verification and generate report."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
report_path = project_root / "docs" / "api-migration" / "verification_report.md"


def run_check(name: str, command: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    """Run a command and return (passed, output)."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(cwd) if cwd else None,
        )
        passed = result.returncode == 0
        output = (result.stdout + "\n" + result.stderr).strip()
        return passed, output
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after 300s"


def main() -> None:
    checks = [
        (
            "Backend Parallel Cluster",
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-n", "auto", "--dist=loadfile", "--basetemp=.tmp_xdist",
             "--ignore=tests/test_audit_logging.py", "--ignore=tests/test_rate_limiting.py",
             "--ignore=tests/test_smoke.py", "--ignore=tests/test_local_executor_manuscript_assist.py",
             "--ignore=tests/test_story_generation_e2e.py"],
            None,
        ),
        (
            "Backend Serial Tests",
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-n", "0",
             "tests/test_audit_logging.py", "tests/test_rate_limiting.py",
             "tests/test_persistence.py::test_local_executor_persists_pipeline_step_records",
             "tests/test_smoke.py", "tests/test_local_executor_manuscript_assist.py",
             "tests/test_story_generation_e2e.py",
             "tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters"],
            None,
        ),
        (
            "Frontend Lint",
            ["npm", "run", "lint"],
            project_root / "frontend",
        ),
        (
            "Frontend TypeCheck",
            ["npm", "run", "typecheck"],
            project_root / "frontend",
        ),
        (
            "Frontend Build",
            ["npm", "run", "build"],
            project_root / "frontend",
        ),
        (
            "Frontend Tests",
            ["npm", "run", "test"],
            project_root / "frontend",
        ),
    ]

    results = []
    for name, cmd, cwd in checks:
        print(f"Running: {name}...")
        passed, output = run_check(name, cmd, cwd)
        results.append((name, passed, output))
        status = "PASS" if passed else "FAIL"
        print(f"  {status}")

    # Generate report
    timestamp = datetime.now(timezone.utc).isoformat()
    lines = [
        "# API Migration Verification Report",
        f"",
        f"**Generated:** {timestamp}",
        f"**Branch:** (fill in manually)",
        f"",
        "## Results",
        f"",
        "| # | Check | Status | Output Summary |",
        "|---|---|---|---|",
    ]

    for i, (name, passed, output) in enumerate(results, 1):
        status = "PASS" if passed else "FAIL"
        # Truncate output to first 200 chars
        summary = output[:200].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {i} | {name} | {status} | {summary} |")

    all_passed = all(r[1] for r in results)
    lines.extend([
        f"",
        "## Overall",
        f"",
        f"**Result:** {'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}",
        f"",
        "## Merge Readiness",
        f"",
    ])

    if all_passed:
        lines.append("This branch is ready for merge. All backend and frontend validation checks passed.")
    else:
        lines.append("This branch is NOT ready for merge. Fix the failing checks before proceeding.")
        failed = [r[0] for r in results if not r[1]]
        lines.append(f"\n**Failed checks:** {', '.join(failed)}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nReport written to {report_path}")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
```

- [ ] Run the verification script: `python scripts/api_migration_verify.py`
- [ ] Manually verify the report at `docs/api-migration/verification_report.md`:

```powershell
Get-Content docs/api-migration/verification_report.md | Select-String "PASS|FAIL|Result"
```

**Acceptance criteria:**
- All 6 verification checks pass (parallel cluster, serial tests, lint, typecheck, build, frontend tests).
- `docs/api-migration/verification_report.md` exists with all PASS status.
- Report includes timestamp and per-check output summary.
- Overall result states "ALL CHECKS PASSED" or clearly lists failures.
