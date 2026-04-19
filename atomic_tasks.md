# Narrative Engine - Atomic Deterministic Task List

**Generated:** 2026-04-19
**Purpose:** Bring the repo to a fully working state (tests pass, clean build, no dead code)
**Scope:** Fix blockers, remove dead code, wire stubs -- no new features

---

## Summary

| # | Task | Priority | Effort | Impact |
|---|------|----------|--------|--------|
| 1 | Fix `datetime.UTC` → `timezone.utc` (18 files) | Critical | 15 min | Unblocks all pytest tests |
| 2 | Remove 10 dead mock service files | High | 5 min | Clean repo, reduce confusion |
| 3 | Remove unused `VITE_USE_MOCKS` env var | High | 5 min | Remove dead code path |
| 4 | Remove dead `SequenceViewer` component | High | 2 min | Eliminate dead code |
| 5 | Remove dead `Storyboard` component tree | High | 5 min | `Storyboard` + `useStoryboard` unused |
| 6 | Remove dead routes in `SceneCardList.tsx` | High | 5 min | Remove broken `navigate('/project/scene/...')` |
| 7 | Wire `disableStage`/`archiveStage` to PATCH | High | 15 min | Remove "not yet implemented" errors |
| 8 | Fix Vite proxy to include `/v1` | High | 5 min | Dev API calls reach backend |
| 9 | Align `JobStatus` type (remove `normalizeJobStatus`) | Medium | 10 min | Remove duplicate type definitions |
| 10 | Run full validation suite | Critical | 30 min | Verify all 4 checks pass |

**Total estimated effort:** ~67 minutes

---

## TASK-001: Fix `datetime.UTC` → `timezone.utc` for Python 3.10 Compatibility

**Priority:** Critical (blocker)
**Affected files:** 18 files (4 source, 14 test)
**Root cause:** `datetime.UTC` was introduced in Python 3.11. The local runtime is Python 3.10.

### Affected files

**Source (4):**
1. `app/schemas/story_development.py` (line 3, 44)
2. `app/persistence/story_development.py` (line 5, 26, 4130-4131, 4209-4210, 4229-4230, 4346-4347, 4364-4365)
3. `app/persistence/projects.py` (line 5, 14)
4. `app/services/projects.py` (line 4, 209)

**Tests (14):**
5. `tests/test_brainstorm_service.py` (line 3, 16)
6. `tests/test_drafting_service.py` (line 3)
7. `tests/test_editable_flow_service.py` (line 5)
8. `tests/test_foundation_service.py` (line 3)
9. `tests/test_planning_service.py` (line 3)
10. `tests/test_review_routing_service.py` (line 3)
11. `tests/test_story_branching_service.py` (line 3)
12. `tests/test_story_branching_lifecycle_integration.py` (line 3)
13. `tests/test_story_decision_review_service.py` (line 3)
14. `tests/test_story_development_api.py` (line 3)
15. `tests/test_story_development_branches.py` (line 3)
16. `tests/test_story_development_integration_flow.py` (line 3)
17. `tests/test_story_development_persistence.py` (line 3)
18. `tests/test_story_knowledge_service.py` (line 3)
19. `tests/test_storyboard_cards.py` (line 5)

### Acceptance criteria

- All 18 files change `from datetime import UTC, datetime` → `from datetime import datetime, timezone`
- All calls change `datetime.now(UTC)` → `datetime.now(timezone.utc)`
- All calls change `tz=UTC` → `tz=timezone.utc`
- No other files are modified
- `python -c "from app.schemas.story_development import now_utc"` succeeds

### Verification command

```bash
python -c "from app.schemas.story_development import now_utc; from app.persistence.projects import find_project_path"
```

---

## TASK-002: Remove 10 Dead Mock Service Files

**Priority:** High
**Root cause:** All 10 mock service files in `frontend/src/services/mocks/` are never imported from any source file (verified by grep). They are dead code.

### Files to delete

1. `frontend/src/services/mocks/arcsMock.ts`
2. `frontend/src/services/mocks/brainstormMock.ts`
3. `frontend/src/services/mocks/charactersMock.ts`
4. `frontend/src/services/mocks/checkerMock.ts`
5. `frontend/src/services/mocks/draftingMock.ts`
6. `frontend/src/services/mocks/flowMock.ts`
7. `frontend/src/services/mocks/foundationMock.ts`
8. `frontend/src/services/mocks/manuscriptAidsMock.ts`
9. `frontend/src/services/mocks/reviewMock.ts`
10. `frontend/src/services/mocks/worldBibleMock.ts`

### Acceptance criteria

- All 10 files are deleted
- The `frontend/src/services/mocks/` directory is deleted (becomes empty)
- `cd frontend && npm run lint` still passes
- `cd frontend && npm run typecheck` still passes
- `cd frontend && npm run build` still passes

---

## TASK-003: Remove Unused `VITE_USE_MOCKS` Env Var

**Priority:** High
**Root cause:** `VITE_USE_MOCKS` is declared in `frontend/src/vite-env.d.ts` but never referenced in any source file.

### Files to modify

1. `frontend/src/vite-env.d.ts` -- remove `VITE_USE_MOCKS` declaration

### Acceptance criteria

- `VITE_USE_MOCKS` is removed from `vite-env.d.ts`
- `cd frontend && npm run typecheck` still passes
- `cd frontend && npm run build` still passes

---

## TASK-004: Remove Dead `SequenceViewer` Component

**Priority:** High
**Root cause:** `SequenceViewer` is exported but never imported by any component or view.

### Files to delete

1. `frontend/src/components/SequenceViewer.tsx`

### Acceptance criteria

- File is deleted
- `cd frontend && npm run typecheck` still passes
- `cd frontend && npm run build` still passes

---

## TASK-005: Remove Dead `Storyboard` Component Tree

**Priority:** High
**Root cause:** The entire `Storyboard` component tree (`Storyboard.tsx`, `useStoryboard.ts`, `SceneCardList.tsx`, `SceneCard.tsx`) is never imported by any view or layout component.

### Files to delete

1. `frontend/src/components/storyboard/Storyboard.tsx`
2. `frontend/src/components/storyboard/SceneCardList.tsx`
3. `frontend/src/components/storyboard/SceneCard.tsx`
4. `frontend/src/components/storyboard/index.ts`
5. `frontend/src/hooks/useStoryboard.ts`
6. `frontend/src/types/scene.ts`

Also remove the `scene` export from `frontend/src/types/index.ts`.

### Acceptance criteria

- All 6 files are deleted
- The `frontend/src/components/storyboard/` directory is deleted (becomes empty)
- `frontend/src/types/index.ts` no longer exports `Scene`
- `cd frontend && npm run lint` still passes
- `cd frontend && npm run typecheck` still passes
- `cd frontend && npm run build` still passes

---

## TASK-006: Fix Dead Routes in SceneCardList (Remove Or Fix)

**Priority:** High
**Root cause:** `SceneCardList.tsx` calls `navigate('/project/scene/${scene.id}')` and `navigate('/planning')` but neither route exists in `App.tsx`. Since TASK-005 removes the entire storyboard component tree, this is handled by TASK-005. If storyboard components are kept, this task is needed separately.

**Dependency:** This task is superseded by TASK-005 (which deletes the file). No separate action needed.

---

## TASK-007: Wire `disableStage`/`archiveStage` to PATCH Endpoint

**Priority:** High
**Root cause:** `frontend/src/services/flow.ts` lines 91-103 throw "not yet implemented" errors for `disableStage` and `archiveStage`. The backend does support stage updates via PATCH -- these should call the same endpoint as `updateStageWithProject` with the appropriate `stage_configuration_state` field.

### Files to modify

1. `frontend/src/services/flow.ts` -- replace stub implementations with real API calls

### Changes

Replace lines 91-103:

```typescript
  async disableStage(projectId: string, stageId: string): Promise<StoryFlowStage> {
    const response = await api.patch(
      `/story-development/flow/stages/${stageId}?project_id=${projectId}`,
      { stage_configuration_state: 'disabled' }
    );
    if (response.status !== 200) {
      throw new Error(`Failed to disable flow stage ${stageId}: ${response.status}`);
    }
    return response.data;
  },

  async archiveStage(projectId: string, stageId: string): Promise<StoryFlowStage> {
    const response = await api.patch(
      `/story-development/flow/stages/${stageId}?project_id=${projectId}`,
      { stage_configuration_state: 'archived' }
    );
    if (response.status !== 200) {
      throw new Error(`Failed to archive flow stage ${stageId}: ${response.status}`);
    }
    return response.data;
  },
```

### Acceptance criteria

- `disableStage` and `archiveStage` make real PATCH calls to the backend
- No more "not yet implemented" errors thrown
- Both methods return `StoryFlowStage` on success
- `cd frontend && npm run typecheck` still passes
- `cd frontend && npm run build` still passes

---

## TASK-008: Fix Vite Proxy to Include `/v1` Path

**Priority:** High
**Root cause:** `frontend/src/lib/api.ts` uses `baseURL: '/v1'` but `vite.config.ts` only proxies `/api`. During dev, requests to `/v1/story-development/...` are not proxied to the backend.

### Files to modify

1. `frontend/vite.config.ts` -- add `/v1` to proxy configuration

### Changes

Replace the proxy block:

```typescript
server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
```

### Acceptance criteria

- Vite dev server proxies `/v1/*`, `/api/*`, and `/health/*` to the backend
- Frontend API calls reach the backend during development
- `cd frontend && npm run dev` starts without proxy errors
- `cd frontend && npm run build` still passes

---

## TASK-009: Align `JobStatus` Type (Remove Duplicate Definitions)

**Priority:** Medium
**Root cause:** `JobStatus` is defined as `'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'` in `lib/jobsApi.ts` but the backend returns `'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED'`. The `normalizeJobStatus()` function maps between them, but consumers of `types/job.ts` expect backend status strings while consumers of `lib/jobsApi.ts` get frontend-normalized strings. This creates confusion and type drift.

### Files to modify

1. `frontend/src/lib/jobsApi.ts` -- remove `JobStatus` type, `normalizeJobStatus()` function, and all status normalization. Use backend-native status strings directly.

### Changes

- Remove line 11: `export type JobStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';`
- Remove lines 13-25: the `normalizeJobStatus` function
- Change `JobSummary.status` and `JobDetail.status` fields to use the backend-native string type: `status: string`
- Remove all calls to `normalizeJobStatus()` -- use the raw backend status directly

### Acceptance criteria

- No duplicate `JobStatus` type (only one definition exists in `types/job.ts`)
- `normalizeJobStatus()` is removed
- `jobsApi.ts` exports no duplicate types
- `cd frontend && npm run lint` still passes (no unused import warnings)
- `cd frontend && npm run typecheck` still passes
- `cd frontend && npm run build` still passes

---

## TASK-010: Run Full Validation Suite

**Priority:** Critical (gate)
**Purpose:** Verify all four quality checks pass after previous tasks.

### Verification commands (run in order)

```bash
# 1. Backend tests
python -m pytest -q -p no:cacheprovider

# 2. Frontend lint
cd frontend && npm run lint

# 3. Frontend typecheck
cd frontend && npm run typecheck

# 4. Frontend build
cd frontend && npm run build
```

### Acceptance criteria

- `python -m pytest -q -p no:cacheprovider` → all tests pass (no errors)
- `cd frontend && npm run lint` → no ESLint errors
- `cd frontend && npm run typecheck` → no TypeScript errors
- `cd frontend && npm run build` → production build succeeds

---

## Execution Order (Dependencies)

```
TASK-001 (datetime.UTC fix)
    └── TASK-010 (validation gate)

TASK-002 (delete mocks) ──┐
TASK-003 (remove env var) ├──→ TASK-004 (delete SequenceViewer) ──┐
TASK-005 (delete storyboard) ──┤                                   ├──→ TASK-010 (validation gate)
TASK-006 (dead routes)    ──┘ (superseded by TASK-005)            │
TASK-007 (flow stubs)   ───┘                                      │
TASK-008 (Vite proxy)   ───┼──→ TASK-009 (type alignment) ────────┘
```

All tasks are independent of each other except TASK-010 which must run last.

---

## Notes

- **No new features.** This task list is strictly: fix blockers, remove dead code, wire stubs.
- **No scope expansion.** Do not refactor `local_executor.py`, `PlanningView.tsx`, or add Docker/Migrations during this pass.
- **One task at a time.** Each task is atomic and self-contained with clear acceptance criteria.
- **Re-run validation** after each task if you want early feedback, but TASK-010 is the final gate.
