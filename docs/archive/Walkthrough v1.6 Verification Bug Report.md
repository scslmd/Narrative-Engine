# Walkthrough v1.6 Verification Bug Report

> **Date:** 2026-05-07
> **Method:** MCP Playwright simulation of User Guide v1.6.0 end-to-end walkthrough
> **Project ID:** 0a53cb6b-3faa-46ba-b2cf-2bf3675aec81 ("Walkthrough v1.6 Verification")
> **Model:** Qwen3.6-27B-Q5_K_M-mtp.gguf (llama.cpp on port 8080)
> **Predecessor:** Walkthrough Bug Hunt Report v1.5.1 (archived — 10 bugs resolved)

This report documents bugs discovered during the v1.6 verification walkthrough that were NOT fixed by the previous session's changes, requiring additional fixes beyond what was committed for v1.6.0.

---

## Summary

| # | Severity | Bug | Root Cause | Fix Applied | File(s) Changed |
|---|----------|-----|------------|-------------|-----------------|
| V1.6-#1 | Critical | Manifest panel still shows empty/N/A despite v1.5.1 fix | Duplicate `/manifest` route in `main.py` shadows the correct `load_manifest()` endpoint in `build_projects_router` | Removed duplicate route from `main.py` | `app/main.py:470-475` |
| V1.6-#6 | High | Sidebar mode buttons still don't navigate despite v1.5.1 fix | Previous fix updated `Layout.tsx` but sidebar is rendered by `WorkspaceShell.tsx`, which only calls `setMode()` without navigating | Added `useNavigate()` + `handleNavClick()` to WorkspaceShell | `frontend/src/components/WorkspaceShell.tsx` |
| V1.6-#7 | Critical | Manuscript still not created after P-300 despite v1.5.1 fix | `save_manuscript_document()` called with `chapter_id="1"`, which triggers `KeyError('1')` in `upsert_manuscript_document` when validating against non-existent ChapterPlan | Only pass `chapter_id` if a valid ChapterPlan exists; fall back to `None` | `app/services/local_executor.py:1160-1181` |
| V1.6-#8 | Medium | Brain Dump shows "Loading..." forever when no sessions exist | Loading check `isLoading \|\| !activeSession` fires for both "still fetching" and "loaded but empty"; no differentiation between loading state and empty state | Split into two conditions: `isLoading` shows spinner, `!activeSession` shows "No sessions yet" with create button | `frontend/src/views/BrainDumpView.tsx:172-195` |

---

## Detailed Bug Reports

### V1.6-#1: Manifest panel still empty despite v1.5.1 fix (Critical)

**Severity:** Critical
**Location:** `app/main.py`, `app/api/projects.py`
**Guide reference:** Step 1 — Project creation and manifest display

**Expected:** After creating a project, the Manifest panel should display all project metadata (name, genre, tone, POV, structure, language, premise).

**Actual:** Manifest panel shows empty/N/A for all fields despite:
- Header correctly displaying "Walkthrough v1.6 Verification • Science Fiction"
- `load_manifest()` method existing in `ProjectService` (added by v1.5.1 fix)
- Correct endpoint in `app/api/projects.py` using `load_manifest()`

**Evidence:**
```
GET /projects/{id}/manifest returns:
{
  "project_id": "...",
  "artifact_name": "manifest",
  "content": "{\"config\": {...}, \"project_name\": \"Walkthrough v1.6 Verification\", ...}",
  "updated_at": "...",
  "lineage_id": null,
  "run_id": null,
  "step_name": null
}
```

Response is `ProjectArtifactResponse` (raw artifact blob), not the parsed `Manifest` dict.

**Root Cause:** Route conflict in `app/main.py`. Line 470-475 defines:
```python
@app.get('/projects/{project_id}/manifest', response_model=ProjectArtifactResponse)
def get_manifest(project_id: str) -> ProjectArtifactResponse:
    return project_service.read_artifact(project_id, 'manifest')
```

This route is registered at line 463, BEFORE `build_projects_router` is included at line 498. FastAPI matches the first registered route, so the old `read_artifact` version intercepts all requests and returns the raw artifact blob instead of the parsed manifest.

The v1.5.1 fix correctly added `load_manifest()` to `ProjectService` and updated the endpoint in `app/api/projects.py`, but didn't remove the duplicate route from `main.py`.

**Fix:** Remove lines 470-475 from `app/main.py` so the correct endpoint in `build_projects_router` takes over.

---

### V1.6-#6: Sidebar navigation still broken despite v1.5.1 fix (High)

**Severity:** High
**Location:** `frontend/src/components/WorkspaceShell.tsx`, `frontend/src/components/Layout.tsx`
**Guide reference:** Step 6 — "In the left sidebar, click Writing mode"

**Expected:** Clicking a sidebar mode button (Writing, Review, Inspect, Brain Dump) should navigate to the corresponding route and render that view.

**Actual:** Clicking "Writing" from `/workspace/{id}/plan`:
- URL stays at `/plan` (doesn't change to `/write`)
- Main content area stays on the Planning/Manifest view
- Sidebar button shows `[active]` state but no navigation occurs

**Evidence:** Repeated clicks on Writing, Review, Inspect — all stay on `/plan`. Direct URL navigation (`/workspace/{id}/write`) works correctly, confirming the route and view are functional.

**Root Cause:** The v1.5.1 fix updated `Layout.tsx`'s `handleModeChange` to use store-based `projectId` instead of fragile `matchPath`. However, the sidebar buttons are NOT rendered by `Layout.tsx` — they're rendered by `WorkspaceShell.tsx`, which has its own click handler:

```tsx
// WorkspaceShell.tsx line 43 (before fix)
onClick={() => setMode(item.key as typeof mode)}
```

This only updates the Zustand store's `mode` state but does NOT call `navigate()`. The Layout header buttons work correctly (they use `handleModeChange`), but the sidebar doesn't.

**Fix:** Add `useNavigate()` import and a `handleNavClick` function to `WorkspaceShell.tsx` that calls both `setMode()` and `navigate()`:

```tsx
const handleNavClick = (key: string) => {
    setMode(key as typeof mode)
    if (projectId) {
        navigate(`/workspace/${projectId}/${key}`)
    }
}
```

---

### V1.6-#7: Manuscript still not created after P-300 despite v1.5.1 fix (Critical)

**Severity:** Critical
**Location:** `app/services/local_executor.py`, `app/persistence/story_development.py`
**Guide reference:** Step 6 — "The Manuscripts section lists your generated chapters"

**Expected:** After P-300 Drafter completes, a ManuscriptDocument should be auto-created in the database and visible in the Writing view.

**Actual:**
- P-300 job completes with status COMPLETED
- `GET /v1/story-development/drafting/manuscript-documents` returns `{"items": []}`
- Writing view shows "No manuscript records yet"
- Server log: `ManuscriptDocument creation failed for single-chapter draft: '1'`

**Evidence:** The error message `'1'` is the string representation of a `KeyError('1')`.

**Root Cause:** The v1.5.1 fix added the `save_manuscript_document()` call but passed `chapter_id=effective_chapter_id` (which is `"1"` for single-chapter mode):

```python
_ms_drafting.save_manuscript_document(
    project_id=project_id,
    document_id=f"ms-{effective_chapter_id}",
    content=output_text,
    title=chapter_title,
    chapter_id=effective_chapter_id,  # <-- "1" triggers KeyError
)
```

This calls `DraftingService.save_manuscript_document()`, which calls `StoryDevelopmentRepository.upsert_manuscript_document()`. At line 4135 of the repository:

```python
if chapter_id is not None:
    chapter = self.get_chapter_plan(chapter_id)  # <-- KeyError('1') — no ChapterPlan with ID "1"
```

The repository validates `chapter_id` by looking up the ChapterPlan, but single-chapter P-300 mode doesn't have a ChapterPlan — it just uses chapter ID `"1"` as a convention. The validation fails before the INSERT.

**Fix:** Only pass `chapter_id` if a valid ChapterPlan exists for it:

```python
linked_chapter_id = None
if _repo and chapter_id:
    try:
        _cp = _repo.get_chapter_plan(chapter_id)
        chapter_title = _cp.title or chapter_title
        linked_chapter_id = chapter_id  # Only set if lookup succeeds
    except KeyError:
        pass

_ms_drafting.save_manuscript_document(
    project_id=project_id,
    document_id=f"ms-{effective_chapter_id}",
    content=output_text,
    title=chapter_title,
    chapter_id=linked_chapter_id,  # None for single-chapter mode
)
```

---

### V1.6-#8: Brain Dump infinite spinner when no sessions exist (Medium)

**Severity:** Medium
**Location:** `frontend/src/views/BrainDumpView.tsx`
**Guide reference:** Detailed Guides §Brain Dump

**Expected:** When no brain dump sessions exist, the view should show a "No sessions yet" message with a "Create new session" button.

**Actual:** Page shows "Loading brain dump session..." indefinitely. No content renders.

**Evidence:**
- API returns 200 with `{"sessions": []}` (empty but successful)
- `isLoading` is `false` (data has loaded)
- `activeSession` is `undefined` (no sessions to select)
- Loading text never goes away

**Root Cause:** The v1.5.1 fix reordered the error check before the loading state check, which fixed the 401 auth error case. However, the loading condition still conflates two states:

```tsx
// BrainDumpView.tsx line 172 (before fix)
if (isLoading || !activeSession) {
    return <p>Loading brain dump session...</p>;
}
```

When `isLoading` is `false` but `!activeSession` is `true` (loaded, no sessions), the component still shows "Loading..." forever. The condition needs to differentiate:
- `isLoading === true` → show spinner (data fetching in progress)
- `isLoading === false && !activeSession` → show empty state with create button

**Fix:** Split into two conditions:

```tsx
if (isLoading) {
    return <p>Loading brain dump session...</p>;
}

if (!activeSession) {
    return (
        <div>
            <p>No brain dump sessions yet.</p>
            <button onClick={() => createMutation.mutate({ project_id })}>+ New Session</button>
        </div>
    );
}
```

---

## Previously Fixed Bugs (Verified Working)

The following bugs from the v1.5.1 report were verified as working during this walkthrough:

| Bug | Verification | Notes |
|-----|-------------|-------|
| #2 (Canon 401s) | PASS | `retry: false` prevents cascading errors; exactly 2 errors when auth disabled, 0 when enabled |
| #4+5 (Job status polling) | PASS | P-100 job: `PENDING` → `PROCESSING` → `COMPLETED` in 13s with correct enum names |
| #9 (Mythos/Pattern 401s) | PASS | No 401 errors on Characters tab when auth is properly configured |
| #10 (Run Kind label) | PASS | Inspect shows `pipeline_job` for P-300 jobs (not `role_model_checker`) |
| #11 (Steps display) | PASS | Inspect displays: drafter, COMPLETED, 63.19s, Qwen3.6 model info |

---

## Validation Results

| Check | Result |
|-------|--------|
| Frontend lint | 0 errors, 2 warnings (pre-existing) |
| Frontend typecheck | Pass |
| Frontend tests | 520 passed |
| Frontend build | 2029 modules |
| Backend parallel cluster | 1414 passed, 10 skipped, 1 pre-existing failure (`test_local_executor_runs_generation_phases`) |
| Backend serial tests | 51 passed |

---

## Environment Notes

- Backend: FastAPI on port 8000, SQLite persistence
- Frontend: Vite dev server on port 5173
- Model: llama.cpp serving Qwen3.6-27B-Q5_K_M-mtp.gguf on port 8080
- Auth: `API_KEY=test-key-123` in `.env` (temporarily disabled during walkthrough for full pipeline testing)
- All fixes verified against live server with real model inference
