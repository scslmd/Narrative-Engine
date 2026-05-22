# Idempotent Job Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent duplicate job launches from accidental double-clicks by generating scoped idempotency keys on the frontend and sending them to the backend, which already has idempotency infrastructure ready.

**Architecture:** A shared `idempotencyKey(scope: string, ttlMs: number)` utility generates a short-lived key stored in sessionStorage. Each scoped key is reused within its TTL window (default 30s), so double-clicks within 30s return the existing job. After TTL expires, a fresh key is generated, allowing legitimate re-submissions. The 4 service functions (`jobsApi.create`, `createGenerationRun`, `runChecker`, `submitManuscriptAssist`) are updated to attach the key. The RoleModelChecker's UI guard is strengthened with a `disabled` state.

**Tech Stack:** TypeScript, React, Axios, FastAPI, SQLite (existing backend idempotency indexes).

---

## File Structure

| File | Change | Responsibility |
|------|--------|---------------|
| `frontend/src/lib/idempotencyKey.ts` | **Create** | Shared utility: generates scoped, TTL-based idempotency keys using sessionStorage |
| `frontend/src/lib/jobsApi.ts` | Modify (line 77-85) | Attach `Idempotency-Key` header to `jobsApi.create()` |
| `frontend/src/services/storyGeneration.ts` | Modify (line 10-15) | Attach `idempotency_key` to `createGenerationRun()` |
| `frontend/src/services/checker.ts` | Modify (line 41-49) | Attach `Idempotency-Key` header to `runChecker()` |
| `frontend/src/services/manuscriptAssist.ts` | Modify (line 11-16) | Attach `idempotency_key` to `submitManuscriptAssist()` |
| `frontend/src/components/checker/RoleModelChecker.tsx` | Modify (line 71-78, 139-146) | Add `isRunning` state and `disabled` attribute to "Run Checker" button |
| `frontend/src/__tests__/idempotencyKey.test.ts` | **Create** | Unit tests for the idempotency key utility |
| `frontend/src/__tests__/jobsApi-idempotency.test.ts` | **Create** | Unit test: jobsApi.create sends Idempotency-Key header |
| `frontend/src/__tests__/storyGeneration-idempotency.test.ts` | **Create** | Unit test: createGenerationRun sends idempotency_key |
| `tests/test_idempotent_job_launch.py` | **Create** | Backend integration test: double-click dedup via idempotency key |

---

## Task 1: Create Idempotency Key Utility

**Files:**
- Create: `frontend/src/lib/idempotencyKey.ts`
- Test: `frontend/src/__tests__/idempotencyKey.test.ts`

**responsible_file:** `frontend/src/lib/idempotencyKey.ts`

**Background:** The backend already has idempotency key handling for all 4 submission paths:
- `POST /v1/jobs/create` — accepts `Idempotency-Key` header (see `app/api/jobs.py:32`)
- `POST /v1/story-generation/runs` — accepts `idempotency_key` in request body (see `app/schemas/generation.py:252`)
- `POST /v1/role-model-checker/run` — accepts `Idempotency-Key` header (see `app/api/role_model_checker.py:46`)
- `POST /v1/manuscript-assist/runs` — accepts `idempotency_key` in request body (see `app/schemas/manuscript_assist.py:98`)

None of these are currently sent by the frontend. This utility fills that gap.

### Design

The function `idempotencyKey(scope: string, ttlMs?: number)` uses sessionStorage to store a key per scope. The scope is a string like `"job:P-100:project-abc"` or `"gen:project-xyz"`. Within the TTL window, the same key is returned. After TTL expires, a new key is generated.

```typescript
// frontend/src/lib/idempotencyKey.ts

const STORAGE_PREFIX = 'idem:';
const DEFAULT_TTL_MS = 30_000; // 30 seconds

/**
 * Generate or retrieve a scoped idempotency key with TTL.
 * Within the TTL window, the same key is returned for the same scope.
 * After TTL expires, a fresh key is generated.
 *
 * @param scope - Unique scope string (e.g., "job:P-100:project-abc")
 * @param ttlMs - Time-to-live in milliseconds (default 30s)
 * @returns Idempotency key string
 */
export function idempotencyKey(scope: string, ttlMs: number = DEFAULT_TTL_MS): string {
  const storageKey = `${STORAGE_PREFIX}${scope}`;

  try {
    const stored = sessionStorage.getItem(storageKey);
    if (stored) {
      const [key, timestamp] = stored.split(':');
      if (Date.now() - Number(timestamp) < ttlMs) {
        return key;
      }
      // TTL expired — will generate new key below
    }
  } catch {
    // sessionStorage unavailable (e.g., test environment) — fall through to generate
  }

  const newKey = `${scope}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  try {
    sessionStorage.setItem(storageKey, `${newKey}:${Date.now()}`);
  } catch {
    // sessionStorage unavailable — return key without persistence
  }

  return newKey;
}
```

- [ ] **Step 1: Write the failing test**

Create `frontend/src/__tests__/idempotencyKey.test.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { idempotencyKey } from '../lib/idempotencyKey';

describe('idempotencyKey', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('returns same key within TTL for same scope', () => {
    const key1 = idempotencyKey('test-scope');
    const key2 = idempotencyKey('test-scope');
    expect(key1).toBe(key2);
  });

  it('returns different key for different scopes', () => {
    const key1 = idempotencyKey('scope-a');
    const key2 = idempotencyKey('scope-b');
    expect(key1).not.toBe(key2);
  });

  it('returns new key after TTL expires', () => {
    vi.useFakeTimers();
    const key1 = idempotencyKey('ttl-scope');
    vi.advanceTimersByTime(31_000);
    const key2 = idempotencyKey('ttl-scope');
    expect(key2).not.toBe(key1);
    vi.useRealTimers();
  });

  it('includes scope prefix in key', () => {
    const key = idempotencyKey('my-scope');
    expect(key.startsWith('my-scope-')).toBe(true);
  });

  it('handles missing sessionStorage gracefully', () => {
    const orig = globalThis.sessionStorage;
    // @ts-expect-error — simulating unavailable sessionStorage
    delete globalThis.sessionStorage;
    expect(() => idempotencyKey('graceful')).not.toThrow();
    globalThis.sessionStorage = orig;
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- src/__tests__/idempotencyKey.test.ts`
Expected: FAIL with "idempotencyKey is not defined" or module not found

- [ ] **Step 3: Write the implementation**

Create `frontend/src/lib/idempotencyKey.ts` with the code from the Design section above.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/__tests__/idempotencyKey.test.ts`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/idempotencyKey.ts frontend/src/__tests__/idempotencyKey.test.ts
git commit -m "feat: add scoped idempotency key utility with TTL"
```

---

## Task 2: Wire Idempotency Key to jobsApi.create()

**Files:**
- Modify: `frontend/src/lib/jobsApi.ts:77-85`
- Test: `frontend/src/__tests__/jobsApi-idempotency.test.ts`

**responsible_file:** `frontend/src/lib/jobsApi.ts`

**serial_dependencies:** Task 1 (idempotencyKey.ts must exist)

**Background:** `jobsApi.create()` currently sends no idempotency header. The backend `POST /v1/jobs/create` already accepts `Idempotency-Key` via FastAPI's `Header(default=None, alias='Idempotency-Key')` at `app/api/jobs.py:32`. The scope should be `"job:{phase}:{project_id}"` so that each phase per project gets its own key.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/__tests__/jobsApi-idempotency.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { jobsApi } from '../lib/jobsApi';

// Mock the api module
vi.mock('../lib/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

import { default as api } from '../lib/api';

describe('jobsApi.create idempotency', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it('sends Idempotency-Key header on create', async () => {
    (api.post as any).mockResolvedValue({
      status: 202,
      data: { id: 'job-1', phase: 'P-100', status: 'PENDING' },
    });

    await jobsApi.create({ project_id: 'proj-1', phase: 'P-100' });

    expect(api.post).toHaveBeenCalledWith(
      '/v1/jobs/create',
      expect.any(Object),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Idempotency-Key': expect.stringContaining('job:P-100:proj-1-'),
        }),
      }),
    );
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- src/__tests__/jobsApi-idempotency.test.ts`
Expected: FAIL — header not present in current implementation

- [ ] **Step 3: Modify jobsApi.create() to attach Idempotency-Key header**

In `frontend/src/lib/jobsApi.ts`, at the top of the file, add import:

```typescript
import { idempotencyKey } from './idempotencyKey';
```

Replace the `create` function (lines 77-85) with:

```typescript
  create: async (request: JobCreateRequest): Promise<JobDetail> => {
    const idemKey = idempotencyKey(`job:${request.phase}:${request.project_id}`);
    const response = await api.post('/v1/jobs/create', {
      phase: request.phase,
      payload: {
        project_id: request.project_id,
        ...(request.payload ?? {}),
      },
    }, {
      headers: { 'Idempotency-Key': idemKey },
    });
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/__tests__/jobsApi-idempotency.test.ts`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/jobsApi.ts frontend/src/__tests__/jobsApi-idempotency.test.ts
git commit -m "feat: attach idempotency key to jobsApi.create()"
```

---

## Task 3: Wire Idempotency Key to createGenerationRun()

**Files:**
- Modify: `frontend/src/services/storyGeneration.ts:10-15`
- Test: `frontend/src/__tests__/storyGeneration-idempotency.test.ts`

**responsible_file:** `frontend/src/services/storyGeneration.ts`

**serial_dependencies:** Task 1

**Background:** `createGenerationRun()` posts to `POST /v1/story-generation/runs`. The backend accepts `idempotency_key` as a field in `CanonGenerationRequest` (see `app/schemas/generation.py`). The scope should be `"gen:{source_project_id}"` so that only one generation run per source project can be in-flight at a time.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/__tests__/storyGeneration-idempotency.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createGenerationRun } from '../services/storyGeneration';

vi.mock('../lib/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

import { default as api } from '../lib/api';

describe('createGenerationRun idempotency', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it('sends idempotency_key in request body', async () => {
    (api.post as any).mockResolvedValue({
      status: 201,
      data: { generation_id: 'gen-1', status: 'queued' },
    });

    await createGenerationRun({
      source_project_id: 'proj-1',
      mode: 'same_project_side_story',
      destination: { destination_kind: 'same_project', target_project_id: 'proj-1' },
      canon_scope: { source_project_id: 'proj-1', character_ids: [], world_bible_refs: [], continuity_thread_ids: [], arc_ids: [], mythos_ids: [], pattern_ids: [], include_relationships: true, include_unresolved_questions: true, include_contradictions_as_forbidden: true },
      generation_brief: 'test',
      target_chapter_count: 3,
      canon_policy: { locked_character_fields: [], locked_world_fields: [], allowed_character_changes: [], allowed_world_changes: [], forbidden_contradictions: [], continuity_strictness: 'repair_once' },
    });

    const body = (api.post as any).mock.calls[0][1];
    expect(body.idempotency_key).toBeDefined();
    expect(body.idempotency_key).toContain('gen:proj-1-');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- src/__tests__/storyGeneration-idempotency.test.ts`
Expected: FAIL — `idempotency_key` not in request body

- [ ] **Step 3: Modify createGenerationRun() to attach idempotency_key**

In `frontend/src/services/storyGeneration.ts`, add import at top:

```typescript
import { idempotencyKey } from '../lib/idempotencyKey';
```

Replace the `createGenerationRun` function (lines 10-15) with:

```typescript
export async function createGenerationRun(
  request: CanonGenerationRequest,
): Promise<GenerationRunResponse> {
  const idemKey = idempotencyKey(`gen:${request.source_project_id}`);
  const response = await api.post('/v1/story-generation/runs', {
    ...request,
    idempotency_key: idemKey,
  });
  return response.data;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/__tests__/storyGeneration-idempotency.test.ts`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/storyGeneration.ts frontend/src/__tests__/storyGeneration-idempotency.test.ts
git commit -m "feat: attach idempotency key to createGenerationRun()"
```

---

## Task 4: Wire Idempotency Key to runChecker()

**Files:**
- Modify: `frontend/src/services/checker.ts:41-49`

**responsible_file:** `frontend/src/services/checker.ts`

**serial_dependencies:** Task 1

**Background:** `runChecker()` posts to `POST /v1/role-model-checker/run`. The backend accepts `Idempotency-Key` header (see `app/api/role_model_checker.py:46`). The scope should be `"checker:{project_id}"` so only one checker run per project can be in-flight.

- [ ] **Step 1: Add import**

In `frontend/src/services/checker.ts`, add at top:

```typescript
import { idempotencyKey } from '../lib/idempotencyKey';
```

- [ ] **Step 2: Modify runChecker() to attach Idempotency-Key header**

Replace the `runChecker` function (lines 41-49) with:

```typescript
export async function runChecker(request: RoleModelCheckRequest): Promise<RoleModelCheckStatus> {
  const idemKey = idempotencyKey(`checker:${request.project_id}`);
  const response = await api.post('/v1/role-model-checker/run', request, {
    headers: { 'Idempotency-Key': idemKey },
  });

  if (response.status !== 202 && response.status !== 200) {
    throw new Error(`Failed to run checker: ${response.status}`);
  }

  return response.data;
}
```

- [ ] **Step 3: Run lint + typecheck to verify no errors**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: No new errors (only 2 pre-existing)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/services/checker.ts
git commit -m "feat: attach idempotency key to runChecker()"
```

---

## Task 5: Wire Idempotency Key to submitManuscriptAssist()

**Files:**
- Modify: `frontend/src/services/manuscriptAssist.ts:11-16`

**responsible_file:** `frontend/src/services/manuscriptAssist.ts`

**serial_dependencies:** Task 1

**Background:** `submitManuscriptAssist()` posts to `POST /v1/manuscript-assist/runs`. The backend accepts `idempotency_key` as a field in `ManuscriptAssistRequest` (see `app/schemas/manuscript_assist.py:98`). The scope should be `"assist:{project_id}:{document_id}:{assist_kind}"` so each assist kind per document gets its own key, preventing duplicate "developmental review" runs while allowing a "canon check" to run concurrently.

- [ ] **Step 1: Add import**

In `frontend/src/services/manuscriptAssist.ts`, add at top:

```typescript
import { idempotencyKey } from '../lib/idempotencyKey';
```

- [ ] **Step 2: Modify submitManuscriptAssist() to attach idempotency_key**

Replace the `submitManuscriptAssist` function (lines 11-16) with:

```typescript
export async function submitManuscriptAssist(
  request: ManuscriptAssistRequest,
): Promise<ManuscriptAssistResult> {
  const idemKey = idempotencyKey(`assist:${request.project_id}:${request.document_id}:${request.assist_kind}`);
  const response = await api.post('/v1/manuscript-assist/runs', {
    ...request,
    idempotency_key: idemKey,
  });
  return response.data;
}
```

- [ ] **Step 3: Run lint + typecheck to verify no errors**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: No new errors (only 2 pre-existing)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/services/manuscriptAssist.ts
git commit -m "feat: attach idempotency key to submitManuscriptAssist()"
```

---

## Task 6: Strengthen RoleModelChecker UI Guard

**Files:**
- Modify: `frontend/src/components/checker/RoleModelChecker.tsx:71-78, 139-146`

**responsible_file:** `frontend/src/components/checker/RoleModelChecker.tsx`

**serial_dependencies:** Task 4

**Background:** The current RoleModelChecker button (line 139-146) uses `{!checkStatus && <button>}` — it simply hides the button after the first run. There's no `disabled` state, no loading feedback, and no guard against double-clicks before `checkStatus` is set. The `handleRunCheck` function (line 71-78) is async, so there's a race window between the click and the state update.

- [ ] **Step 1: Add isRunning state**

After line 16 (`const [polling, setPolling] = useState(false);`), add:

```typescript
  const [isRunning, setIsRunning] = useState(false);
```

- [ ] **Step 2: Modify handleRunCheck to set isRunning**

Replace the `handleRunCheck` function (lines 71-78) with:

```typescript
  const handleRunCheck = async () => {
    if (isRunning) return;
    setIsRunning(true);
    try {
      const status = await runChecker({ project_id: projectId, models: selectedModels });
      setCheckStatus(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run checker');
    } finally {
      setIsRunning(false);
    }
  };
```

- [ ] **Step 3: Add disabled state and loading feedback to button**

Replace the button (lines 139-146) with:

```typescript
      {!checkStatus && (
        <button
          onClick={handleRunCheck}
          disabled={isRunning}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRunning ? 'Running...' : 'Run Checker'}
        </button>
      )}
```

- [ ] **Step 4: Run lint + typecheck to verify no errors**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: No new errors (only 2 pre-existing)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/checker/RoleModelChecker.tsx
git commit -m "feat: add disabled state and loading feedback to RoleModelChecker button"
```

---

## Task 7: Backend Integration Test for Double-Click Dedup

**Files:**
- Create: `tests/test_idempotent_job_launch.py`

**responsible_file:** `tests/test_idempotent_job_launch.py`

**serial_dependencies:** Task 2, Task 3

**Background:** The backend idempotency mechanism is already implemented and tested individually. This test verifies the end-to-end behavior: sending the same idempotency key twice with the same payload returns the existing job rather than creating a duplicate.

- [ ] **Step 1: Write the test**

Create `tests/test_idempotent_job_launch.py`:

```python
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import build_app
from app.settings import settings


@pytest.fixture
def client(tmp_path):
    original_ops = settings.operations_db_path
    original_proj = settings.projects_dir
    settings.operations_db_path = tmp_path / "ops.db"
    settings.projects_dir = tmp_path / "projects"
    client = TestClient(build_app())
    yield client
    settings.operations_db_path = original_ops
    settings.projects_dir = original_proj


def test_job_create_deduplicates_with_idempotency_key(client: TestClient):
    """Two identical job creates with same idempotency key return same job."""
    payload = {
        "phase": "P-100",
        "payload": {"project_id": "test-proj"},
    }
    headers = {"Idempotency-Key": "idem-test-1"}

    r1 = client.post("/jobs/create", json=payload, headers=headers)
    assert r1.status_code == 202, f"First create failed: {r1.status_code}"
    job_id_1 = r1.json()["id"]

    r2 = client.post("/jobs/create", json=payload, headers=headers)
    assert r2.status_code in (200, 202), f"Second create failed: {r2.status_code}"
    job_id_2 = r2.json()["id"]

    assert job_id_1 == job_id_2, "Duplicate job created despite idempotency key"


def test_job_create_allows_different_idempotency_keys(client: TestClient):
    """Two creates with different idempotency keys create separate jobs."""
    payload = {
        "phase": "P-100",
        "payload": {"project_id": "test-proj"},
    }

    r1 = client.post("/jobs/create", json=payload, headers={"Idempotency-Key": "key-a"})
    assert r1.status_code == 202
    job_id_1 = r1.json()["id"]

    r2 = client.post("/jobs/create", json=payload, headers={"Idempotency-Key": "key-b"})
    assert r2.status_code == 202
    job_id_2 = r2.json()["id"]

    assert job_id_1 != job_id_2, "Different idempotency keys should create different jobs"


def test_job_create_conflicts_on_different_payload(client: TestClient):
    """Same idempotency key with different payload returns 409."""
    headers = {"Idempotency-Key": "idem-conflict"}

    r1 = client.post("/jobs/create", json={
        "phase": "P-100",
        "payload": {"project_id": "proj-a"},
    }, headers=headers)
    assert r1.status_code == 202

    r2 = client.post("/jobs/create", json={
        "phase": "P-100",
        "payload": {"project_id": "proj-b"},
    }, headers=headers)
    assert r2.status_code == 409, "Different payloads with same key should conflict"


def test_job_create_without_key_always_creates_new(client: TestClient):
    """Requests without idempotency key always create new jobs."""
    payload = {
        "phase": "P-100",
        "payload": {"project_id": "test-proj"},
    }

    r1 = client.post("/jobs/create", json=payload)
    assert r1.status_code == 202
    job_id_1 = r1.json()["id"]

    r2 = client.post("/jobs/create", json=payload)
    assert r2.status_code == 202
    job_id_2 = r2.json()["id"]

    assert job_id_1 != job_id_2
```

- [ ] **Step 2: Run the tests to verify they pass**

Run: `python -m pytest tests/test_idempotent_job_launch.py -v`
Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_idempotent_job_launch.py
git commit -m "test: verify backend idempotency deduplication for job creation"
```

---

## Task 8: Full Validation

**responsible_file:** N/A (validation gate)

**serial_dependencies:** Tasks 1-7

- [ ] **Step 1: Frontend tests**

Run: `cd frontend && npm run test`
Expected: All pass (previous baseline + 6 new tests)

- [ ] **Step 2: Frontend lint**

Run: `cd frontend && npm run lint`
Expected: 0 new errors (2 pre-existing only)

- [ ] **Step 3: Frontend typecheck**

Run: `cd frontend && npm run typecheck`
Expected: Pass

- [ ] **Step 4: Frontend build**

Run: `cd frontend && npm run build`
Expected: Pass, 2070+ modules

- [ ] **Step 5: Backend parallel cluster**

Run: `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py --ignore=tests/test_smoke.py --ignore=tests/test_local_executor_manuscript_assist.py --ignore=tests/test_story_generation_e2e.py`
Expected: 1473+ passed, 7 skipped

- [ ] **Step 6: Backend serial tests**

Run: `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records tests/test_smoke.py tests/test_local_executor_manuscript_assist.py tests/test_story_generation_e2e.py tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters`
Expected: 51+ passed

- [ ] **Step 7: Adversarial review**

Run: `python scripts/qc.py --adverse-only`
Expected: 0 Critical/High findings

---

## Self-Review

### 1. Spec Coverage
- [x] Prevent duplicate job launches from double-clicks — Tasks 2-5 attach idempotency keys to all 4 submission paths
- [x] Backend deduplication — Task 7 tests the existing backend mechanism works end-to-end
- [x] UI guard strengthening — Task 6 fixes the weakest guard (RoleModelChecker)
- [x] No changes to backend code — the backend infrastructure already exists

### 2. Placeholder Scan
- No "TBD", "TODO", or vague language found
- All code blocks contain complete, compilable code
- All test files contain actual test code with assertions

### 3. Type Consistency
- `idempotencyKey` function signature consistent across all imports
- Scope naming convention consistent: `{type}:{identifier}` (e.g., `job:P-100:proj-1`, `gen:proj-1`, `checker:proj-1`, `assist:proj-1:doc-1:kind`)
- `idempotency_key` field name matches backend schema exactly (snake_case)
- `Idempotency-Key` header name matches FastAPI `alias` parameter exactly

### 4. File Ownership
- Each task modifies exactly one responsible file
- No parallel tasks share a responsible file
- Task 1 has no dependencies (creates new file)
- Tasks 2-5 depend only on Task 1 (can run in parallel with each other)
- Task 6 depends on Task 4 (same file chain: checker.ts -> RoleModelChecker.tsx)
- Task 7 depends on Tasks 2-3 (tests backend, not frontend)

---

## Parallel Execution Groups

| Group | Tasks | Can Run In Parallel? |
|-------|-------|---------------------|
| Setup | Task 1 | No dependencies — runs first |
| Services | Tasks 2, 3, 4, 5 | Yes — all depend only on Task 1, each modifies a different file |
| UI Guard | Task 6 | After Task 4 (different file, but follows checker flow) |
| Tests | Task 7 | After Tasks 2-3 (tests backend, independent of frontend) |
| Validation | Task 8 | After all other tasks |
