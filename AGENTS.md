# Narrative Engine - Development Guidelines

## Current Truth

- The repo now uses a React + TypeScript frontend in `frontend/`.
- Frontend API calls should prefer the shared Axios client in `frontend/src/lib/api.ts`.
- The current verified validation baseline is:
  - `python -m pytest -q -p no:cacheprovider` -> `1031 passed, 9 skipped`
  - `cd frontend && npm run lint` -> passed
  - `cd frontend && npm run typecheck` -> passed
  - `cd frontend && npm run build` -> passed
- Frontend code quality: 0 TODO/FIXME in production, 0 console.log, 0 `as any` casts, 0 `@ts-ignore`, 0 mock data. 1973 modules in production bundle.
- Frontend services: 112 exported functions across 18 service files, 37 dead functions removed (42% reduction) in 2026-04-23 integration audit. All remaining exports are wired to components.
- Feature coverage: 13/13 backend-to-frontend feature areas fully linked. Story Import UI added in 2026-04-23. Multi-chapter generation completed in 2026-04-26 (summarization, prior context propagation, ManuscriptDocument auto-creation).
- Route-driven workspace state is the current frontend architecture:
  - `/workspace/:projectId/plan`
  - `/workspace/:projectId/write`
  - `/workspace/:projectId/write/:chapterId`
  - `/workspace/:projectId/review`
  - `/workspace/:projectId/inspect`
  - `/workspace/:projectId/inspect/:jobId`
  - `/workspace/:projectId/braindump`
- Inspect deep links are expected to render from the route, and review-driven "Jump to Source" should resolve an inspect run before navigation.

## Agent Guardrails

- Perform only the task that was explicitly requested or assigned.
- Do not expand scope with opportunistic refactors, adjacent feature work, or speculative cleanup unless that work is required to complete the task at hand.
- Do not "wonder" about broader improvements during execution. Verify the relevant code, make the bounded change, and stop.
- If you notice unrelated issues, document them only when they are true blockers. Do not edit unrelated files just because they are nearby.
- Prefer the smallest complete change that satisfies the requested contract and validation requirements.
- When a task is documentation or review only, keep code untouched unless the task explicitly calls for code changes.

## Quick Start Commands

### Frontend
```bash
cd frontend
npm run dev
npm run lint
npm run typecheck
npm run build
```

### Backend
```bash
# From project root
python -m pytest
python -m pytest tests/test_smoke.py
python -m pytest -k test_name
python -m pytest tests/test_story_branching_service.py::test_create_branch
python -m app.main
```

### Security and Reliability Focused Tests
```bash
python -m pytest tests/test_input_validation.py
python -m pytest tests/test_authentication.py
python -m pytest tests/test_authorization.py
python -m pytest tests/test_circuit_breaker.py
python -m pytest tests/test_idempotency.py
python -m pytest tests/test_backup.py
```

### Full Merge-Readiness Validation
```bash
python -m pytest -q -p no:cacheprovider
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
```

### Test Subsets (by marker)
```bash
python -m pytest -q -p no:cacheprovider -m "not integration"   # unit only (~31s, 487 tests)

  python -m pytest -q -p no:cacheprovider -m integration          # integration only (~120s, 391 tests)

  python -m pytest -q -p no:cacheprovider                        # full suite (~150s, 878 tests)

```

- Use `-m "not integration"` for fast feedback during development.
- Use the unmarked full suite for merge-readiness validation (unchanged).

### Quality Review Helper
```bash
python scripts/qc.py                   # review branch diff vs codex/main
python scripts/qc.py --latest-commit   # review files changed in HEAD
python scripts/qc.py app/main.py       # review one specific file
python scripts/qc.py file1.py file2.ts # review multiple specific files
python scripts/qc.py --verbose         # show review steps and analyzer results
python scripts/qc.py --allow-directories app   # expand coding files under a directory target
```

- `scripts/qc.py` is the portable implementation (compatibility wrapper).
- `scripts/qc.py` defaults to branch-diff review against `codex/main`, then falls back to `HEAD`, then to recent modified coding files if no git-derived targets are found.
- Direct file targets override auto-detection and only review the files you pass.
- Directory targets require `--allow-directories`; otherwise `scripts/qc.py` fails clearly instead of silently skipping them.
- Missing or unsupported explicit targets fail clearly instead of degrading into a generic run.
- `--verbose` prints the selection path, review steps, and per-file analyzer summary before the full report.
- The adverse review output should include concrete file-aware findings from the analyzed files, not just a generic checklist.

## Project Structure

```text
narrative-engine/
|-- app/                    # FastAPI backend
|   |-- api/               # Routers
|   |-- persistence/       # Database access and SQLite integration
|   |-- schemas/           # Pydantic models
|   |-- services/          # Business logic
|   `-- main.py            # App entry point
|-- frontend/              # Vite + React frontend
|   |-- package.json
|   |-- index.html
|   `-- src/
|       |-- components/
|       |-- hooks/
|       |-- lib/
|       |-- services/
|       |-- stores/
|       |-- types/
|       `-- views/
|-- tests/                 # Pytest suite
`-- data/                  # Runtime data (gitignored)
```

## Frontend Guidelines

### Imports

Use relative imports. Prefer this grouping order:
1. React
2. external libraries
3. local types
4. local services/lib/hooks
5. local components

Example:
```tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { StoryBranch } from '../../types/branches';
import { getBranches } from '../../services/branches';
import { BranchCard } from './BranchCard';
```

### Types

- Prefer `interface` for object-shaped props and API contracts.
- Prefer `type` for unions and string enums.
- Keep backend field names in snake_case at the service/type boundary.
- Do not rename backend fields in service responses just to make them camelCase.

Example:
```tsx
export interface StoryBranch {
  branch_id: string;
  project_id: string;
  parent_branch_id: string | null;
  state: 'active' | 'merged' | 'archived';
}
```

### Components

- Use functional components with explicit prop types.
- Export named components unless the file already follows a default-export convention.
- Prevent invalid actions in the UI instead of relying on backend errors or warning toasts.
- Do not leave user-facing placeholder actions behind.

Example:
```tsx
interface BranchListProps {
  projectId: string;
}

export function BranchList({ projectId }: BranchListProps) {
  // implementation
}
```

### State Management

- Use React Query for server state.
- Use Zustand for client/UI state.
- Invalidate queries after successful mutations.
- Treat the route as the source of truth for workspace mode and selected route entities.

Example:
```tsx
const mutation = useMutation({
  mutationFn: (id: string) => updateBranch(id),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['branches'] }),
});
```

### Error Handling

- Keep HTTP classification in the shared API layer and service layer.
- Keep presentation decisions in components.
- Distinguish meaningful statuses when the UX depends on them:
  - `401` authentication
  - `403` authorization
  - `404` not found
  - `409` conflict
  - `5xx` server failure
- Do not swallow Axios `404` responses by checking `response.status` after `api.get()` unless you are explicitly catching `ApiError`.

### Frontend Service Pattern

Use the shared client from `frontend/src/lib/api.ts`:
```tsx
import api from '../lib/api';

export async function getComparison(
  comparisonId: string,
  projectId?: string,
): Promise<BranchComparisonRecord> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;

  const response = await api.get(
    `/story-development/branches/comparisons/${comparisonId}`,
    { params },
  );

  return response.data;
}
```

Avoid:
- file-local `API_BASE`
- mixed `fetch` and Axios patterns for the same API family
- ad hoc host concatenation

### Routing and Inspect Flow

- `useRouteSync` is the current route-to-store sync pattern.
- `InspectMode` should be able to render directly from `/workspace/:projectId/inspect/:jobId`.
- Review-driven inspect navigation should resolve a real inspect run before routing.
- Do not navigate to dead-end inspect shells that cannot render the target state.

## Backend Guidelines

### Imports

Follow:
1. `from __future__ import annotations`
2. stdlib
3. third-party
4. local imports

Example:
```python
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import httpx

from app.schemas import StoryBranch
from app.persistence import Repository
```

### Type Hints

- Use modern syntax such as `list[str]`, `dict[str, str]`, and `str | None`.
- Use explicit return types.

Example:
```python
def list_branches(self, project_id: str) -> tuple[StoryBranch, ...]:
    ...
```

### Exceptions

- Use specific service exception classes.
- Wrap lower-level exceptions with domain-specific errors.

Example:
```python
class StoryBranchingNotFoundError(StoryBranchingServiceError):
    pass

try:
    record = self.repository.get_branch(branch_id)
except KeyError as exc:
    raise StoryBranchingNotFoundError(branch_id) from exc
```

### Pydantic Models

- Use `StrictModel` for API schemas that should reject extra fields.
- Match field names exactly to the public contract.

Example:
```python
class BranchCreateRequest(StrictModel):
    project_id: str
    branch_name: str
```

## Testing Patterns

### Backend Tests

- Use `tmp_path` for isolated runtime paths.
- Use `TestClient(build_app())` for API tests.
- Name tests `test_<component>_<action>_<expected_result>`.

Example:
```python
def test_create_branch(tmp_path):
    client = TestClient(build_app())
    response = client.post('/branches', json={...})
    assert response.status_code == 201
```

### Parallel vs Serial Tests (pytest-xdist)

**Default**: Sequential (`-n 0`). Parallel is opt-in via:
```bash
pytest -n auto --dist=loadfile --basetemp=.tmp_xdist
```

**Write parallel-safe tests** when possible. A test is parallel-safe if it:
- Uses `tmp_path` for all file/db paths (isolated per test)
- Does NOT read/write shared global state (`settings.structured_log_filename`, env vars, singleton caches)
- Does NOT start long-lived threads or daemons without cleanup

**Mark serial tests** when they depend on shared mutable state:
```python
import pytest

# Option A: Mark a single test
@pytest.mark.xdist_group(name="serial-my-group")
def test_needs_serial_execution(tmp_path):
    ...

# Option B: Mark an entire file (add at module level)
pytestmark = [pytest.mark.integration, pytest.mark.xdist_group(name="serial-my-file")]
```

**Known serial-only tests**:
- `tests/test_audit_logging.py` — shares `settings.structured_log_filename` log file across all TestClient requests. Run with `-n 0`.
- `tests/test_persistence.py::test_local_executor_persists_pipeline_step_records` — starts/stops executor threads

**When adding new tests**: If your test writes to a global path (log, cache, singleton DB), either isolate the path via `tmp_path` or mark it `xdist_group`.
```

### Frontend Checks

- `npm run lint` catches unsafe patterns and dead code.
- `npm run typecheck` catches contract drift.
- `npm run build` catches integration and bundling issues that lint can miss.

## Build Verification

### Always Run After Changes

1. Frontend: `cd frontend && npm run build`
2. Frontend: `cd frontend && npm run lint`
3. Frontend: `cd frontend && npm run typecheck`
4. Backend: `python -m pytest -q -p no:cacheprovider`

### Merge-Ready Means

Do not call the repo merge-ready unless all four of these are green:

- `python -m pytest -q -p no:cacheprovider`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| Frontend import errors | Check actual folder structure and use correct relative imports |
| Axios `404` handling never runs | Catch `ApiError` instead of checking `response.status` after `api.get()` |
| Frontend-backend parameter mismatch | Backend expects snake_case such as `project_id`; convert from camelCase in services |
| Wrong HTTP status code on endpoint | Use `201` for create routes, `200` for updates/select operations, and verify against tests |
| Invalid inspect navigation | Only route to inspect screens that can render the resolved run/job id |
| Dead CTA buttons | Hide, disable, or complete the action; never leave no-op production buttons |
| Test temp directory conflicts | Use `tmp_path`; do not hardcode runtime paths |
| `node_modules` in git | Add to `.gitignore` and unstage before commit |
| Idempotency conflicts | Same key must have the same payload; otherwise create a new key |
| Backup restore failures | Verify disk space and backup existence before restore |
| `input_payload` vs `input_hash` parameter drift | `StepRecordService.create_step_record()` uses `input_hash`/`output_hash`/`prompt_hash`, not `input_payload`/`output_payload`/`prompt_payload` |

## API Patterns

### Versioning

- The current HTTP surface is mixed.
- The shared frontend client points at `/v1` for jobs, models, story-development, and checker routes.
- Projects, auth, backup, and health routes still exist as unversioned server routes and should be verified before assuming a versioned alias.

### Representative Endpoints

#### Projects
- `GET /projects`
- `POST /projects/create`
- `GET /projects/{project_id}`
- `DELETE /projects/{project_id}`
- `POST /projects/import-story` (201 Created, synchronous - parses existing stories and creates full project structure)
- `POST /projects/import-patterns` (201 Created, synchronous - extracts narrative patterns from text, creates or updates project)
- `POST /projects/{project_id}/extract-patterns` (201 Created, synchronous - extracts narrative patterns for an existing project)
- `GET /projects/{project_id}/manifest`
- `GET /projects/{project_id}/sequence`
- `GET /projects/{project_id}/chapter-1`

#### Authentication
- `POST /auth/keys`
- `GET /auth/keys`
- `DELETE /auth/keys/{prefix}`

#### Backup
- `POST /backup/create`
- `POST /backup/restore/{backup_id}`
- `GET /backup/list`
- `GET /backup/latest`
- `DELETE /backup/{backup_id}`

#### Role Model Checker
- `POST /v1/role-model-checker/run`
- `POST /v1/role-model-checker/start`
- `GET /v1/role-model-checker/{run_id}/status`
- `GET /v1/role-model-checker/{run_id}/steps`
- `GET /v1/role-model-checker/{run_id}/lineage`
- `GET /v1/role-model-checker/{run_id}/attempts`
- `POST /v1/role-model-checker/{run_id}/retry`

#### Story Development - Branching
- `GET /v1/story-development/branches?project_id={id}`
- `POST /v1/story-development/branches`
- `GET /v1/story-development/branches/active?project_id={id}`
- `POST /v1/story-development/branches/active`
- `POST /v1/story-development/branches/comparisons`
- `GET /v1/story-development/branches/comparisons?project_id={id}`
- `POST /v1/story-development/branches/merge-decisions`

#### Story Development - Flow
- `GET /v1/story-development/flow/stages?project_id={id}`
- `POST /v1/story-development/flow/stages`
- `PATCH /v1/story-development/flow/stages/{stage_id}?project_id={id}`
- `DELETE /v1/story-development/flow/stages/{stage_id}?project_id={id}`
- `POST /v1/story-development/flow/stages/reorder?project_id={id}`

#### Story Development - Decisions & Review
- `GET /v1/story-development/decisions?project_id={id}`
- `GET /v1/story-development/decisions/{node_id}?project_id={id}`
- `GET /v1/story-development/review/findings?project_id={id}`
- `GET /v1/story-development/review/decisions?project_id={id}`
- `POST /v1/story-development/review/decisions`
- `GET /v1/story-development/review/inspect-links?project_id={id}`

#### Story Development - Planning
- `GET /v1/story-development/planning/sequence-plans?project_id={id}`
- `POST /v1/story-development/planning/sequence-plans`
- `PATCH /v1/story-development/planning/sequence-plans/{sequence_id}?project_id={id}`
- `GET /v1/story-development/planning/chapter-plans?project_id={id}`
- `POST /v1/story-development/planning/chapter-plans`
- `PATCH /v1/story-development/planning/chapter-plans/{chapter_id}?project_id={id}`
- `GET /v1/story-development/planning/scene-plans?project_id={id}`
- `POST /v1/story-development/planning/scene-plans`
- `PATCH /v1/story-development/planning/scene-plans/{scene_id}?project_id={id}`
- `GET /v1/story-development/planning/beat-plans?project_id={id}`
- `POST /v1/story-development/planning/beat-plans`
- `PATCH /v1/story-development/planning/beat-plans/{beat_id}?project_id={id}`
- `GET /v1/story-development/planning/dependencies?project_id={id}`
- `GET /v1/story-development/planning/chapter-packets?project_id={id}`
- `POST /v1/story-development/planning/chapter-packets`
- `PATCH /v1/story-development/planning/chapter-packets/{packet_id}?project_id={id}`
- `POST /v1/story-development/planning/reorder?project_id={id}`

#### Story Development - Drafting
- `GET /v1/story-development/drafting/draft-artifacts?project_id={id}`
- `GET /v1/story-development/drafting/draft-artifacts/{artifact_id}?project_id={id}`
- `POST /v1/story-development/drafting/draft-artifacts/continue`
- `POST /v1/story-development/drafting/draft-artifacts/alternate-variant`
- `GET /v1/story-development/drafting/manuscript-documents?project_id={id}`
- `GET /v1/story-development/drafting/manuscript-documents/{document_id}?project_id={id}`
- `POST /v1/story-development/drafting/manuscript-documents`
- `PATCH /v1/story-development/drafting/manuscript-documents/{document_id}?project_id={id}`
- `POST /v1/story-development/drafting/manuscript-documents/{document_id}/review?project_id={id}`
- `GET /v1/story-development/drafting/revision-suggestions?project_id={id}`
- `GET /v1/story-development/drafting/revision-suggestions/{suggestion_id}?project_id={id}`
- `POST /v1/story-development/drafting/revision-suggestions`
- `POST /v1/story-development/drafting/promote-draft`

#### Story Development - Brainstorm
- `GET /v1/story-development/brainstorm/items?project_id={id}`
- `POST /v1/story-development/brainstorm/items`
- `POST /v1/story-development/brainstorm/items/cluster`
- `POST /v1/story-development/brainstorm/items/promote`
- `GET /v1/story-development/brainstorm/promotions?project_id={id}`

#### Story Development - Braindump
- `POST /v1/story-development/braindump/sessions`
- `GET /v1/story-development/braindump/sessions?project_id={id}`
- `GET /v1/story-development/braindump/sessions/{session_id}?project_id={id}`
- `PATCH /v1/story-development/braindump/sessions/{session_id}?project_id={id}`
- `DELETE /v1/story-development/braindump/sessions/{session_id}?project_id={id}`
- `POST /v1/story-development/braindump/sessions/{session_id}/organize?project_id={id}`

#### Story Development - Foundation
- `GET /v1/story-development/foundation?project_id={id}`
- `POST /v1/story-development/foundation`
- `PATCH /v1/story-development/foundation?project_id={id}`
- `GET /v1/story-development/foundation/revisions?project_id={id}`
- `GET /v1/story-development/foundation/review-cues?project_id={id}`

#### Story Development - Characters
- `GET /v1/story-development/characters?project_id={id}`
- `GET /v1/story-development/characters/{character_id}?project_id={id}`
- `POST /v1/story-development/characters`
- `PATCH /v1/story-development/characters/{character_id}?project_id={id}`
- `GET /v1/story-development/characters/{character_id}/relationships?project_id={id}`
- `POST /v1/story-development/relationships`

#### Story Development - World Bible
- `GET /v1/story-development/world-bible?project_id={id}`
- `GET /v1/story-development/world-bible/{entry_type}/{title}?project_id={id}`
- `POST /v1/story-development/world-bible`
- `PATCH /v1/story-development/world-bible/{entry_type}/{title}?project_id={id}`

#### Story Development - Arcs
- `GET /v1/story-development/arcs/candidates?project_id={id}`
- `POST /v1/story-development/arcs/candidates`
- `GET /v1/story-development/arcs/selections?project_id={id}`
- `POST /v1/story-development/arcs/selections`
- `PATCH /v1/story-development/arcs/selections/{selection_id}?project_id={id}`
- `DELETE /v1/story-development/arcs/selections/{selection_id}?project_id={id}`
- `GET /v1/story-development/arcs/stage-maps?project_id={id}`
- `POST /v1/story-development/arcs/stage-maps`
- `POST /v1/story-development/arcs/comparisons`

#### Story Development - Storyboard Cards
- `GET /v1/story-development/storyboard/cards?project_id={id}`
- `GET /v1/story-development/storyboard/cards/{card_id}?project_id={id}`
- `POST /v1/story-development/storyboard/cards`
- `PATCH /v1/story-development/storyboard/cards/{card_id}?project_id={id}`
- `DELETE /v1/story-development/storyboard/cards/{card_id}?project_id={id}`
- `PUT /v1/story-development/storyboard/cards/{column_id}/reindex?project_id={id}`

#### Story Development - Relationships
- `GET /v1/story-development/relationships?project_id={id}`
- `PATCH /v1/story-development/relationships/{edge_id}?project_id={id}`
- `DELETE /v1/story-development/relationships/{edge_id}?project_id={id}`

#### Jobs
- `POST /v1/jobs/create`
- `GET /v1/jobs/{job_id}/status`
- `GET /v1/jobs/{job_id}/attempts`
- `GET /v1/jobs/{job_id}/logs`
- `GET /v1/jobs/{job_id}/steps`
- `GET /v1/jobs/{job_id}/lineage`
- `POST /v1/jobs/{job_id}/retry`

#### Health & Metrics
- `GET /health/`
- `GET /health/ready`
- `GET /health/metrics`

### Status Code Semantics

- `201 Created`: creates a new resource
- `200 OK`: reads, updates, selections, or non-create mutations

Example:
- `/story-development/branches/active` is a selection/update operation -> `200`
- `/story-development/branches` creates a branch -> `201`

### Contract Alignment Rules

When modifying API or service code:

1. Check the router signature and request schema.
2. Check the frontend service call.
3. Check the component or hook call site.
4. Check existing tests before changing status codes or parameter requirements.

## Security and Reliability Features

### SEC-01: Input Validation
`app/utils/input_validation.py`
```python
from app.utils.input_validation import sanitize_string, validate_filename, limit_size

safe_text = sanitize_string(user_input)
validate_filename(filename, max_length=255)
limit_size(payload_dict, max_bytes=5_242_880)
```

### SEC-04: Path Traversal Protection
`app/middleware/path_traversal.py`
```python
from app.middleware.path_traversal import PathTraversalMiddleware
```

### SEC-05: Rate Limiting
`app/middleware/rate_limit.py`
```python
from app.middleware.rate_limit import RateLimitMiddleware
```

### REL-03: Thread Safety
All service layer operations are thread-safe through SQLite's built-in journaling and the lease-claim mechanism.

### SEC-02: Authentication
`app/services/authentication.py`
```python
from app.services.authentication import get_auth_service

auth = get_auth_service()
api_key, full_key = auth.create_key(
    name="My App",
    permissions=["read", "write"],
    expires_in_days=365,
)
validated_key = auth.validate_key("abcd.xYz123...")
auth.revoke_key("abcd")
```

### SEC-03: Authorization
`app/services/authorization.py`
```python
from app.services.authorization import get_authorization_service, PERMISSION_READ

authz = get_authorization_service()
authz.require_permission(user_permissions, "write")
authz.check_resource_access(
    user_permissions=["read"],
    user_owner_id="user123",
    resource_owner_id="user123",
    required_permission="read",
)
```

### REL-01: Circuit Breaker
`app/services/circuit_breaker.py`
```python
from app.services.circuit_breaker import get_circuit_breaker

circuit = get_circuit_breaker("llama.cpp")
```

### REL-02: Idempotency
`app/services/idempotency.py`
```python
from app.services.idempotency import check_idempotency, store_response
```

### REL-04: Backup
`app/services/backup.py`
```python
from app.services.backup import get_backup_service

backup = get_backup_service()
```

### REL-05: Latency Telemetry
`app/api/health.py` -- `/health/metrics` endpoint provides average, min, and max latency for jobs and role-model-checker runs.

### REL-06: CORS
CORS middleware configured for `localhost:5173` and `localhost:3000` in `app/main.py`.

### REL-07: Config Validation
`app/services/config_validator.py::validate_config_at_startup()` validates all settings at application startup (database paths, inference URLs, API keys).

### REL-08: Request Size Limits
`MAX_BODY_SIZE` constant in `app/utils/constants.py` limits request body size to prevent oversized payloads.

### REL-09: File Permission Validation
`app/services/file_permissions.py::FilePermissionValidator` validates directory permissions, rejects world-writable directories, and performs directory-safety checks.

### REL-10: Audit Logging
Operation field normalization in audit logging middleware with stable semantic names like `job.create`, `project_artifact.manifest.read`, `story_development.drafting.draft_artifacts.read`. Key fingerprinting via `fingerprint_api_key()` in `app/services/authentication.py`.

## Frontend Quality Gate Notes

These repo-level guardrails apply to merged frontend work:

- Services should use one shared API client pattern.
- Route state must survive refreshes and deep links.
- Review and inspect flows must resolve real targets.
- No user-visible prototype seams should remain in merged flows.
- Loading, empty, and error states should be explicit.
- Tailwind classes should be statically analyzable.

## Merge Readiness Lessons

### 1. Route Changes Must Be Validated Across All Callers

- Do not rename or version routes in only one layer.
- Verify frontend services, tests, and compatibility aliases together.

### 2. Persisted Execution Records Are Part of the Contract

- A run is not "working" if inspect, lineage, or status projections are wrong.

### 3. Test Isolation Matters

- Shared runtime state can create false failures.
- Use deterministic per-test runtime paths where required.

### 4. Frontend Route State Must Follow the URL

- Route segments are the source of truth for workspace mode and inspect targets.

### 5. Lightweight Test Routers Must Preserve Exact Error Semantics

- Tests may depend on exact detail strings, not just status codes.

### 6. Completion Ordering Matters for Async Persistence

- Persist inspectable metadata before final terminal state when tests and UI depend on it.

### 7. Warning Cleanup Matters

- Once blockers are fixed, remove warnings that indicate real drift.

### 8. Documentation Drift Reintroduces Bugs

- Update docs right after architecture or contract changes.

### 9. Root-Level Clutter Causes Confusion

- Archive historical notes under `docs/archive/`.
- Keep root-level docs focused on active guidance.

### 10. Merge-Ready Means Validated, Not Just Plausible

- The four core validation commands are the final gate.

### 11. Service-Executor Signature Alignment Is Critical

- When modifying executor call sites, update service layer signatures simultaneously.
- `StepRecordService.create_step_record()` uses pre-computed `input_hash`, `output_hash`, `prompt_hash` (not `input_payload`).
- `StepRecordService.create_lineage_record()` uses `content_hash` (not `content_hash_source`).
- Parameter name mismatches cause silent `TypeError` failures that pass individual test runs but fail in the full suite due to test ordering.
- Always verify the full call chain: `local_executor.py` → `StepRecordService` → repository layer.
- See `docs/Test Failure Analysis v0.1.md` for the full catalog of known test failures (29 pre-existing).

## API Parameter Alignment Guidelines

When updating service contracts:

- Keep backend field names exact in API payloads and query params.
- Optional backend params should stay optional on the frontend.
- Do not assume similar endpoints accept the same params.
- Check the call chain from component -> hook -> service -> router.

Example:
```typescript
export async function getComparison(
  comparisonId: string,
  projectId?: string,
): Promise<BranchComparisonRecord> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;

  const response = await api.get(
    `/story-development/branches/comparisons/${comparisonId}`,
    { params },
  );
  return response.data;
}
```

## Database Module Pattern

When health checks or utilities need raw DB access without pulling in the full persistence layer, prefer a small shared utility module such as `app/database.py`.

Example:
```python
from __future__ import annotations

import sqlite3
from pathlib import Path

from app.persistence.sqlite import connect as _connect
from app.settings import settings


def get_db_connection(db_path: Path | None = None) -> sqlite3.Connection:
    target_path = db_path or settings.operations_db_path
    return _connect(target_path)
```

## Story Import Feature

> Full research documented in `docs/Story Import Research & Architecture.md`

### Goal

Allow users to paste/upload an existing completed story, then have the LLM review it, classify it, and "fill out all the blanks" (create the full project structure including foundation, characters, world bible, arcs, planning, and drafts) in one automated workflow.

### Project Creation Flow

**Entry**: `POST /projects/create` -> `app/services/projects.py::ProjectService.create_project()`
- Creates `data/projects/{project_id}/` with: `manifest.json`, `bible.db`, `sequences.json`, `chapter.md`, `exports/`, `.telemetry`, `.structured_log`
- Registers in operations DB: `projects` and `project_artifacts` tables
- Bootstrap via `app/services/project_bootstrap.py::bootstrap_project()`

**Config schemas**: `app/schemas/manifest.py`
- `ManifestConfig`: genre, tone_profile, pov (enum), primary_language, secondary_language, story_structure (enum)
- `Manifest`: project_id, project_name, config, constraints, premise_text

**Enums** (`app/schemas/enums.py`):
- `StoryStructure`: SAVE_THE_CAT, THREE_ACT, HERO_JOURNEY, FREYTAGS_PYRAMID, KISHOTENKETSU, FICHTEAN_CURVE, SEVEN_POINT_STRUCTURE, SEVEN_KEY_STEPS, SNOWFLAKE_METHOD, BRAINDUMP, OTHER
- `PovMode`: FIRST, SECOND, THIRD_LIMITED, THIRD_OMNI, THIRD_OBJECTIVE, THIRD_MULTIPLE, OTHER

### Key Entity Schemas (via StoryDevelopmentRepository)

**FoundationProfile** (`app/schemas/story_development.py:194`):
- premise, logline, thematic_spine, emotional_promise, tone_and_voice_direction, target_audience, narrative_constraints, complexity_level, success_definition, version

**CharacterProfile** (`app/schemas/story_development.py:288`):
- character_id, project_id, display_name, role_in_story, archetype, external_goal, internal_need, misbelief_or_wound, core_fear, primary_strength, fatal_flaw_or_limitation, contradictions, backstory_summary, voice_notes, secrets, values, taboos, change_axis, arc_stage_notes, continuity_facts, writer_notes
- `relationship_edges` auto-populated from separate table

**WorldBibleEntry** (`app/schemas/story_development.py:344`):
- entry_id, project_id, entry_type, title, summary, canonical_facts, related_character_ids, visibility_scope, continuity_warnings, writer_notes
- Unique key: (project_id, entry_type, title)

**Arcs**: Three tables - arc_candidates, arc_stage_maps, arc_selections
**Planning**: sequence_plans, chapter_plans, scene_plans, beat_plans
**Drafting**: draft_artifacts, manuscript_documents

### Database Architecture

Two SQLite databases:
- **Operations DB** (`settings.operations_db_path`): Central registry, 40+ tables, full rebuild migration pattern
- **Project DB** (`data/projects/{project_id}/bible.db`): Project-local metadata

`app/persistence/story_development.py::StoryDevelopmentRepository` -- all methods are single-row operations. **No bulk insert**. Each call opens its own connection and commits. Creating N entities = N separate calls.

### LLM Inference System

**Architecture**:
```
InferenceBackend (ABC) -> app/inference/base.py
    +-- OpenAICompatibleInferenceBackend -> app/inference/openai_compatible.py (production)
    +-- StubInferenceBackend -> app/inference/stub.py (testing)
Factory: app/inference/factory.py::build_inference_backend()
```

**Supported providers** (all use OpenAICompatibleInferenceBackend):
- `llama.cpp` (default: `http://127.0.0.1:8080`), `lmstudio` (default: `http://127.0.0.1:1234`), `vllm` (default: `http://127.0.0.1:8000`), `openai_compatible`, `stub`

**Inference contract** (`app/schemas/inference.py`):
```python
class InferenceRequest: model, system_prompt, user_prompt, temperature=0.2, max_tokens=1200, metadata
class InferenceResponse: model, content, backend, finish_reason, usage, metadata
```

**Executor pattern** (`app/services/local_executor.py`):
1. Build inference request via `runtime_prompts.py` helpers
2. Call `self._inferencer.generate_text(inference_request)` (with circuit breaker)
3. Write response to staged file, atomic replace to output
4. Create step record + artifact lineage, update job to COMPLETED

**Settings** (`app/settings.py`):
- `NARRATIVE_INFERENCE_BACKEND`, `NARRATIVE_INFERENCE_BASE_URL`, `NARRATIVE_INFERENCE_API_KEY`, `NARRATIVE_INFERENCE_MODEL`, `NARRATIVE_INFERENCE_TIMEOUT_SECONDS`

**Existing prompt builders** (`app/services/runtime_prompts.py`):
- P-100 Architect (markdown output), P-200 Sequencer (JSON output), P-300 Drafter (markdown), P-400 Compiler (JSON)
- P-300 default max_tokens: 8000 (supports full-chapter drafts, overridable via payload)

### Multi-Chapter Generation

**Architecture**: P-300 drafter accepts `chapter_id` in job payload. Output path becomes `chapters/{chapter_id}.md`. Artifact role becomes `chapter_{chapter_id}`. Backward compatible: without chapter_id, outputs flat `chapter.md` with artifact role `chapter_1`.

**Batch mode**: P-300 also accepts `chapter_ids` list in job payload. `_run_multi_chapter_draft` in local_executor.py enters sequential loop: draft → summarize → create ManuscriptDocument → propagate summary as prior context for next chapter. Single job, per-chapter step records.

**Components**:
- `app/services/runtime_prompts.py` - `chapter_output_path(project_dir, chapter_id)` parameterized path; `build_chapter_summarize_request()` prompt builder
- `app/services/scene_context.py` - `SceneContext.prior_chapters` injects last 3 prior chapter summaries into LLM prompt
- `app/services/chapter_summarizer.py` - `ChapterSummarizerService.summarize()` extracts PriorChapterSummary via LLM (key_events, character_states, unresolved_threads). Error-tolerant: never blocks pipeline.
- `app/services/local_executor.py` - `_run_multi_chapter_draft` detects `chapter_ids` list, runs sequential loop with prior context propagation and ManuscriptDocument auto-creation
- `app/schemas/story_development.py` - `PriorChapterSummary` dataclass for cross-chapter continuity context

**Context Injection**: SceneContextService assembles character anchors + world constraints + prior chapter summaries. Prior chapters capped at last 3 to avoid prompt bloat. Each summary includes key events (max 10), character states (max 10), unresolved threads (max 5).

**Active Character Filtering**: When `chapter_id` is provided, P-300 queries `ChapterPlan.active_character_ids` and passes to SceneContextService. Only active characters are injected into the prompt. Falls back to all characters if no chapter plan exists.

**ManuscriptDocument Auto-Creation**: After each successful chapter draft in batch mode, ManuscriptDocument is auto-created via DraftingService.save_manuscript_document() with document_id `ms-{chapter_id}`, title from ChapterPlan (or "Chapter {id}"), and chapter content.

**Security**: `chapter_id` is sanitized via `sanitize_filename()` before use in file paths to prevent path traversal attacks.

**Only P-100 to P-400 phases exist** (`app/schemas/enums.py::JobPhase`). No custom phases allowed.
- `PENDING -> PROCESSING -> COMPLETED` or `FAILED`
- Worker: `app/services/local_executor.py` runs two daemon threads (`_job_loop`, `_checker_loop`)

### Story Import Feature

**Workflow**: User pastes story -> LLM analyzes and extracts structured JSON -> Service validates -> Creates project + all entities in single transaction.

**Entry**: `POST /projects/import-story` returns **201 Created** with `status: "completed"` or `status: "failed"`. Synchronous — HTTP request blocks.

**Service**: `StoryImportService` in `app/services/story_import.py`
- `import_story(request)` — main entry point
- `_create_project(request)` — creates new project or validates existing `project_id`
- `_analyze_story(text, genre_hint, tone_hint)` — calls LLM via `InferenceBackend` directly
- `_parse_llm_json(content)` — robust extraction: direct JSON, markdown fences, trailing/leading text
- `_transactional_import(project_id, analysis)` — single raw SQLite connection with `BEGIN`, direct parameterized SQL (NOT repo wrapper methods)

**Transaction Safety**: Uses a single `sqlite3.connect()` with `BEGIN` (not `BEGIN IMMEDIATE`), executes raw SQL directly without repo methods. All inserts use `ON CONFLICT DO UPDATE` for idempotent retries. Foundation revisions also use `ON CONFLICT(project_id, revision_number) DO UPDATE`.

**Entity ID Generation**: Characters and arcs use SHA-256 hash-based IDs (`import-{prefix}-{hash[:12]}`) for stable, order-independent identity. Same input always produces the same ID regardless of list ordering, enabling deduplication.

**Manifest Update**: After successful entity creation, `_update_manifest()` writes LLM-extracted `genre`, `tone`, `pov`, `story_structure`, `premise_text`, and `constraints` to `manifest.json`. Invalid enum values are silently skipped with a warning log.

**API Key Protection**: The `/projects/import-story` endpoint is included in the `versioned_api_key_gate` middleware (gate applies to both `/v1/*` and `/projects/import-story` paths).

**Error Handling**: `_create_project` catches `FileNotFoundError` specifically (not bare `Exception`) to distinguish missing projects from database errors.

**LLM Request**: `build_import_analysis_request()` in `app/services/runtime_prompts.py`
- `temperature=0.1`, `max_tokens=16000` for deterministic JSON output
- Story text truncated to 24,000 chars for single-pass analysis
- Returns JSON matching `StoryImportAnalysis` schema

**Error Handling**:
- `StoryImportError(ValueError)` — caught, returns `status="failed"` response
- `InferenceBackendError` — caught, returns `status="failed"` with error code
- `pydantic.ValidationError` — caught, wrapped as `StoryImportError`

**Components**:
- `app/services/story_import.py` — `StoryImportService` class (with `_update_manifest()`, `_hash_id()`, `_to_none()`)
- `app/schemas/story_import.py` — `StoryImportRequest`, `StoryImportResponse`, `StoryImportAnalysis` (with POV/structure validators)
- `app/api/projects.py` — `POST /projects/import-story` endpoint (guarded by API key middleware)
- `app/services/runtime_prompts.py` — `build_import_analysis_request()` prompt builder
- `app/main.py` — imports StoryImportService, wires into router, includes `/projects/import-story` in auth gate
- `tests/test_story_import_service.py` — 18 test functions

### Pattern Extraction Feature

**Workflow**: User pastes text -> LLM extracts archetypal patterns, narrative structure, voice profile, and entities -> Service persists extracted patterns to project DB -> Patterns can be injected into P-100/P-300 prompts for guided generation.

**Entry Points**:
- `POST /projects/import-patterns` (201 Created) — standalone: provides text, extracts patterns, creates or updates project with results
- `POST /projects/{project_id}/extract-patterns` (201 Created) — targeted: extracts patterns for an existing project

**Service**: `PatternExtractionService` in `app/services/pattern_extraction.py`
- `extract_patterns(request)` — main entry point, dispatches to LLM analysis then persistence
- `_analyze_text(text, genre_hint, tone_hint)` — calls LLM via `InferenceBackend` directly
- `_parse_llm_json(content)` — robust JSON extraction: direct JSON, markdown fences, trailing/leading text
- `_persist_patterns(project_id, analysis)` — persists extracted patterns to project's bible.db

**Generalization of MythosExtractionService**: `PatternExtractionService` is the generalized version of `MythosExtractionService`. Mythos extraction now delegates through `PatternExtractionService` with a `mode="mythos_extraction"` parameter. Shared LLM prompt builder: `build_pattern_extraction_request()` in `runtime_prompts.py`. Mythos-specific builder `build_mythos_analysis_request()` wraps the same infrastructure with mythos-tuned system prompt.

**Schema**: `app/schemas/pattern_extraction.py`
- `PatternExtractionAnalysis` — LLM output: archetypal_patterns, narrative_structure, voice_profile, world_rules, character_archetypes, symbolic_motifs
- `PatternExtractionRequest(StrictSchemaModel)` — input: text (required), project_id (optional), genre_hint, tone_hint
- `PatternExtractionResponse(StrictSchemaModel)` — output: status, extraction (summary), error
- `PatternExtractionSummary(StrictSchemaModel)` — condensed extraction result

**SceneContext Extension**: `app/services/scene_context.py` — `SceneContext` dataclass extended with:
- `pattern_guidance: PatternGuidance | None` — injects extracted archetypal patterns into P-100/P-300 prompts
- `author_prompt: str | None` — freeform author guidance injected before character/world context

**P-100/P-300 Prompt Builders**: `app/services/runtime_prompts.py` — adapted for pattern context injection:
- `_build_pattern_context_block(pc)` — formats PatternExtractionAnalysis into prompt block
- P-100 architect prompts accept optional `pattern_context` parameter; when present, appends pattern mapping instructions
- P-300 drafter prompts accept `pattern_guidance` via SceneContext; patterns influence tone, structure, and character voice
- `build_pattern_extraction_request()` — LLM request builder: `temperature=0.1`, `max_tokens=16000`
- `build_mythos_analysis_request()` — mythos-specific variant with cosmic/mythological framing

**Error Handling**:
- `PatternExtractionError(ValueError)` — caught, returns `status="failed"` response
- `InferenceBackendError` — caught, returns `status="failed"` with error code
- `pydantic.ValidationError` — caught, wrapped as `PatternExtractionError`

**Components**:
- `app/services/pattern_extraction.py` — `PatternExtractionService` class
- `app/schemas/pattern_extraction.py` — request/response/analysis schemas
- `app/api/projects.py` — `/import-patterns` and `/{project_id}/extract-patterns` endpoints (guarded by API key middleware)
- `app/services/runtime_prompts.py` — `build_pattern_extraction_request()`, `_build_pattern_context_block()`
- `app/services/scene_context.py` — extended `SceneContext` with `pattern_guidance` and `author_prompt`
- `tests/test_pattern_extraction.py` — 87 test functions

## Implementation Workflow for Next Phases/Tasks

When asked to implement the next phases or tasks from the backlog, follow this workflow:

1. **PRE-FLIGHT**: Run `python scripts/qc.py --adverse-only` on current branch state to establish a clean baseline. Any new regression introduced during the session is immediately visible.

2. **REVIEW**: Research the target scope — read existing contracts, schemas, persistence tables, service boundaries, and related tests. Understand the full call chain from API endpoint down to database queries. Identify blocking dependencies before writing any code.

3. **PLAN**: Generate atomic, deterministic tasks with detailed instructions. Each task card must include:
   - One bounded scope (one feature, one service slice, one API endpoint)
   - Schema definitions (Pydantic models, DB columns, JSON shapes)
   - Expected file paths and function signatures
   - Acceptance criteria and verification commands
   - Explicit dependencies on other tasks

4. **BRANCH**: Create a feature branch (e.g., `codex/<feature-name>`). Never work directly on `codex/main`.

5. **TEST-DRIVEN**: Write failing unit tests first, generate test fixtures and mocks. Tests must be written before implementation code. Use `tmp_path` for isolated runtime paths. Test names follow `test_<component>_<action>_<expected_result>`.

6. **IMPLEMENT**: Execute tasks one at a time. Run tests after each task to verify incremental progress. Do not batch multiple tasks without intermediate verification.

7. **VALIDATE**: After completing each task group, run the full suite:
   - `python -m pytest -q -p no:cacheprovider`
   - `cd frontend && npm run lint`
   - `cd frontend && npm run typecheck`
   - `cd frontend && npm run build`
   Do not proceed to the next task group until all four pass.

8. **ADVERSARIAL**: Run `python scripts/qc.py --adverse-only` on changed files. Address all Critical and High severity findings before continuing. Do not ship known defects.

9. **DOCUMENT**: Update `AGENTS.md` test baseline (pytest count and frontend commands). Update `TODO.md` with completion status. Write or update docs for any new APIs, patterns, or contracts.

10. **MERGE**: Squash-merge the feature branch into `codex/main` with a comprehensive commit message that documents what changed, why, and what the new validation baseline is.
