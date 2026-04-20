# Narrative Engine - Development Guidelines

## Current Truth

- The repo now uses a React + TypeScript frontend in `frontend/`.
- Frontend API calls should prefer the shared Axios client in `frontend/src/lib/api.ts`.
- The current verified validation baseline is:
  - `python -m pytest -q -p no:cacheprovider` -> `554 passed, 9 skipped` (20 new tests from manuscript word processor feature)
  - `cd frontend && npm run lint` -> passed
  - `cd frontend && npm run typecheck` -> passed
  - `cd frontend && npm run build` -> passed
- Route-driven workspace state is the current frontend architecture:
  - `/workspace/:projectId/plan`
  - `/workspace/:projectId/write`
  - `/workspace/:projectId/write/:chapterId`
  - `/workspace/:projectId/review`
  - `/workspace/:projectId/inspect`
  - `/workspace/:projectId/inspect/:jobId`
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
- `GET /v1/story-development/planning/chapter-plans?project_id={id}`
- `GET /v1/story-development/planning/scene-plans?project_id={id}`
- `GET /v1/story-development/planning/dependencies?project_id={id}`
- `GET /v1/story-development/planning/chapter-packets?project_id={id}`

#### Story Development - Drafting
- `GET /v1/story-development/drafting/draft-artifacts?project_id={id}`
- `GET /v1/story-development/drafting/manuscript-documents?project_id={id}`
- `POST /v1/story-development/drafting/manuscript-documents`
- `POST /v1/story-development/drafting/promote-draft`
- `GET /v1/story-development/drafting/revision-suggestions?project_id={id}`
- `POST /v1/story-development/drafting/revision-suggestions`

#### Story Development - Brainstorm
- `GET /v1/story-development/brainstorm/items?project_id={id}`
- `POST /v1/story-development/brainstorm/items`
- `POST /v1/story-development/brainstorm/items/cluster`
- `POST /v1/story-development/brainstorm/items/promote`
- `GET /v1/story-development/brainstorm/promotions?project_id={id}`

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
- `GET /v1/story-development/arcs/selections?project_id={id}`
- `GET /v1/story-development/arcs/stage-maps?project_id={id}`

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

### Job System

**Only P-100 to P-400 phases exist** (`app/schemas/enums.py::JobPhase`). No custom phases allowed.
- `PENDING -> PROCESSING -> COMPLETED` or `FAILED`
- Worker: `app/services/local_executor.py` runs two daemon threads (`_job_loop`, `_checker_loop`)

### Story Import Design

**Workflow**: User pastes story -> [LLM] Analyze -> [Service] Parse JSON -> Create project -> Create foundation -> Create characters -> Create world bible -> Create arcs -> Create planning -> Create manuscript

**Key decisions**:
1. One API call to start, async processing (`POST /projects/import-story` returns 202)
2. Reuse existing `InferenceBackend` directly (like `ManuscriptReviewService`), no new job phase needed
3. Single LLM call for stories under ~50K tokens, multi-step for larger texts
4. Validate LLM output with Pydantic models
5. **Transaction safety**: Each repo method commits individually. Solution: wrap in manual transaction or allow partial imports with recovery
6. **Token management**: Need chunking for large stories. Consider first pass for metadata summary, second pass for detailed extraction

**New components needed**:
- `app/services/story_import.py` - `StoryImportService` class
- `app/schemas/story_import.py` - request/response schemas
- `app/api/projects.py` - `POST /projects/import-story` endpoint
- `runtime_prompts.py` - `build_import_analysis_request()` prompt builder
