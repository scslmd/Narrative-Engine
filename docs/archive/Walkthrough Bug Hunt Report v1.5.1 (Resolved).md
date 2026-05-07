# Walkthrough Bug Hunt Report

> **STATUS: ALL BUGS RESOLVED** — Archived 2026-05-07. All 10 bugs fixed and verified (520 frontend tests, 1414 backend tests). See User Guide v1.6.0 changelog for summary.

**Date:** 2026-05-07
**Method:** MCP Playwright simulation of User Guide v1.5.1 end-to-end walkthrough
**Project ID:** 33670150-b7bf-47f0-b61b-fa172fadbcd0 ("MCP Walkthrough Test")
**Model:** Qwen3.6-27B-Q5_K_M-mtp.gguf (llama.cpp on port 8080)

---

## Resolution Summary

| # | Severity | Bug | Fix | File(s) Changed |
|---|----------|-----|-----|----------------|
| 1 | Critical | Manifest panel empty/N/A | Added `load_manifest()` to backend, endpoint returns parsed `Manifest` | `app/services/projects.py`, `app/api/projects.py` |
| 7 | Critical | No manuscript records after P-300 | Added `save_manuscript_document()` to single-chapter drafter path | `app/services/local_executor.py` |
| 4+5 | High | Silent job failure + no polling feedback | Fixed status enum mismatch: `QUEUED`/`RUNNING` → `PENDING`/`PROCESSING` | `frontend/src/types/job.ts`, `useJobs.ts`, `JobStatusIndicator.tsx`, tests |
| 6 | High | Sidebar navigation broken | Replaced fragile `matchPath` with store-based `projectId` | `frontend/src/components/Layout.tsx` |
| 2+9 | Medium | Canon 401 errors + request cascade | Added `retry: false` to auth-gated queries | `CanonView.tsx`, `useMythosLibrary.ts`, `usePatternLibrary.ts` |
| 8 | Medium | Brain Dump infinite loading | Reordered error check before loading state | `BrainDumpView.tsx` |
| 10+11 | Low | Wrong Run Kind + no steps shown | Reversed InspectMode resolution: jobs first, then checker fallback | `InspectMode.tsx` |

---

## Original Report (Archived)

| Severity | Count | IDs |
|----------|-------|-----|
| Critical | 2 | #1, #7 |
| High | 3 | #4, #5, #6 |
| Medium | 3 | #2, #8, #9 |
| Low | 2 | #10, #11 |

---

## Critical Bugs

### BUG #1: Manifest panel not displaying project metadata

**Severity:** Critical
**Location:** `frontend/src/` — Manifest display component (Planning view, default tab)
**Guide reference:** Step 1 — "You'll be taken to your project's workspace. The top navigation bar shows your project name and genre badge."

**Expected:** After creating a project with Genre="Science Fiction", Tone="Dark and Atmospheric", Structure="Three Act Structure", POV="Third Person Limited", Language="English" — the Project Manifest panel should display all these values.

**Actual:** Manifest panel shows:
- Project Name: **empty** (should be "MCP Walkthrough Test")
- Genre: **N/A** (should be "Science Fiction")
- Tone Profile: **N/A** (should be "Dark and Atmospheric")
- Point of View: **empty** (should be "Third Person Limited")
- Story Structure: **empty** (should be "Three Act Structure")
- Primary Language: **N/A** (should be "English")

**Evidence:** Header correctly shows "MCP Walkthrough Test • Science Fiction", so the data exists in state but isn't rendering in the manifest panel. The manifest JSON was written during project creation (verified on disk).

**Root cause hypothesis:** Manifest component reads from a stale source, doesn't re-fetch after project creation, or maps fields incorrectly. The backend `manifest.json` on disk has the correct values, so this is a frontend display issue.

---

### BUG #7: P-300 drafter output not registered in database (empty Writing view)

**Severity:** Critical
**Location:** `app/services/local_executor.py` (P-300 persistence), `app/services/drafting.py` (ManuscriptDocument creation)
**Guide reference:** Step 6 — "The Manuscripts section lists your generated chapters — click the generated chapter"

**Expected:** After P-300 Drafter completes successfully, the Writing view should show the generated chapter in either the Manuscripts list or Drafts list.

**Actual:**
- `GET /v1/story-development/drafting/manuscript-documents?project_id=...` returns `{"items": []}`
- `GET /v1/story-development/drafting/draft-artifacts?project_id=...` returns `{"items": []}`
- Writing view shows "No manuscript records yet" and "No drafts yet"
- File `data/projects/{id}/chapter.md` EXISTS on disk with valid generated content (verified: 20+ paragraphs of quality prose)

**Evidence:**
- Job `a1dcbd67-b4a5-442a-b902-b5b40bb6c14e` (P-300 Drafter) status: COMPLETED
- `chapter.md` on disk: 20+ paragraphs, correct characters (Elena Voss, CERES), correct setting (Station Meridian)
- Both drafting API endpoints return empty arrays

**Root cause hypothesis:** P-300 executor writes to disk (`chapter.md`) but doesn't call `DraftingService.save_manuscript_document()` or create a DraftArtifact DB record. The multi-chapter mode has auto-creation logic (`_run_multi_chapter_draft`), but single-chapter mode may be missing it.

**Impact:** User can never see, read, or edit generated content through the UI. Entire writing workflow is broken.

---

## High Severity Bugs

### BUG #4: Job failure not surfaced in Launch Job panel

**Severity:** High
**Location:** `frontend/src/` — Launch Job panel component, job status polling
**Guide reference:** Step 5 — "Watch the job status change from PENDING → PROCESSING → COMPLETED"

**Expected:** After launching a job, the panel should show current status. If the job fails, the error message should be visible.

**Actual:** Job `556379b4` (first Architect attempt without model configured) FAILED with `RUNTIME_CONFIGURATION_ERROR: "Inference request is missing a model and no default model is configured."` The Launch Job panel showed no status change, no error, no feedback. Play button remained the same.

**Evidence:**
- POST `/jobs/create` → 202 Accepted (job submitted)
- Backend job status: FAILED with clear error message
- Frontend: No visual change in Launch Job panel

**Root cause hypothesis:** Launch Job panel doesn't poll for job status after submission, or doesn't render FAILED state. No toast, no inline error, no status badge.

---

### BUG #5: No visual feedback during job execution (no pause/stop indicator)

**Severity:** High
**Location:** `frontend/src/` — Launch Job panel component
**Guide reference:** Step 5 — "Watch the job status change from PENDING → PROCESSING → COMPLETED"

**Expected:** Clicking the play button should:
1. Transform into a pause/stop icon to indicate the job is running
2. Show progress or status (PENDING → PROCESSING)
3. Allow user to cancel by clicking the pause/stop button

**Actual:** Play button remains unchanged after click. No visual indication that a job is processing. User has no way to cancel a running job or know it's still working.

**Evidence:**
- Job `99f0b92c` (Architect) ran for 13 seconds — play button showed no change during that time
- Job `a1dcbd67` (Drafter) ran for 100 seconds — same, no visual feedback
- No status text, no spinner, no progress bar, no cancel option

---

### BUG #6: Sidebar mode buttons don't navigate to target view

**Severity:** High
**Location:** `frontend/src/` — Sidebar navigation components, route synchronization
**Guide reference:** Step 6 — "In the left sidebar, click Writing mode" (also applies to Review, Inspect, Brain Dump)

**Expected:** Clicking a sidebar mode button (Writing, Review, Inspect, Brain Dump) should navigate to the corresponding route and render that view.

**Actual:** Clicking "Writing" sets the button to `[active]` state but:
- URL stays at `/workspace/{id}/plan` (doesn't change to `/write`)
- Main content area stays on the Planning/Manifest view
- No navigation occurs

**Evidence:** Repeatedly observed across all mode buttons. Writing, Review, Inspect — all stay on `/plan`.

**Note:** This is documented in the guide's troubleshooting section: "Sidebar mode buttons don't switch views — Known issue — Use direct URLs instead." However, it's not flagged as a known issue in the main walkthrough text, so users following Step 6 will be confused.

**Root cause hypothesis:** Sidebar buttons update local state (active class) but don't trigger route navigation via React Router. `useRouteSync` may not be wired to sidebar clicks.

---

## Medium Severity Bugs

### BUG #2: Canon annotations 401 errors on Characters tab

**Severity:** Medium
**Location:** `frontend/src/services/canonCustomization.ts`, Characters component
**Guide reference:** Step 3 — Characters tab

**Expected:** Opening the Characters tab should load character data without console errors. If canon annotations require auth, the error should be handled gracefully.

**Actual:** Two `GET /v1/canon/annotations?project_id=...` requests return 401 Unauthorized. Characters still render correctly, but errors pollute the console.

**Evidence:** Console shows 2 errors on every Characters tab load:
```
[ERROR] Failed to load resource: the server responded with a status of 401 (Unauthorized)
@ http://localhost:5173/v1/canon/annotations?project_id=...
```

**Root cause hypothesis:** Characters component fetches canon annotations as a side effect. When `NARRATIVE_API_KEY` is set on the server but not configured in the frontend, the 401 responses aren't caught and logged as errors. Should either: (a) skip the call if no auth key, (b) catch 401 silently, or (c) surface a user-friendly message.

---

### BUG #8: Brain Dump stuck on "Loading..." indefinitely (401)

**Severity:** Medium
**Location:** `frontend/src/` — BrainDump view, braindump service
**Guide reference:** Detailed Guides §Brain Dump

**Expected:** Brain Dump view should load and show the freeform canvas, or show an auth error if API key is required.

**Actual:** Page shows "Loading brain dump session..." forever. No content renders. Two 401 errors in console for `GET /v1/story-development/braindump/sessions`.

**Evidence:**
```
[ERROR] Failed to load resource: the server responded with a status of 401 (Unauthorized)
@ http://localhost:5173/v1/story-development/braindump/sessions?project_id=...
```

**Note:** Documented in troubleshooting: "Brain Dump stuck on 'Loading...' — 401 from API key gate." But there's no error message, no fallback, no way for the user to know what's wrong without checking the console.

**Root cause hypothesis:** BrainDump component fetches sessions on mount, gets 401, and never transitions out of loading state. Should show an auth error overlay (like Canon Workshop does) or gracefully degrade.

---

### BUG #9: Canon Workshop fires unnecessary 401 requests before showing auth message

**Severity:** Medium
**Location:** `frontend/src/` — Canon Workshop view, canon services
**Guide reference:** Detailed Guides §Canon Workshop

**Expected:** If API key is required, the view should check auth status first and show the "API key required" message without firing failed requests.

**Actual:** View fires 8 API calls (mythos entries x2, patterns entries x2, annotations x2, profiles x2), all return 401, then shows the auth error overlay. Console has 8 errors.

**Evidence:** Network log shows 8 sequential 401 responses before the "API key required" overlay renders.

**Root cause hypothesis:** Canon Workshop component fetches all data on mount without checking auth status first. Should check for a valid API key before making calls, or catch 401 at the service layer and short-circuit.

---

## Low Severity Bugs

### BUG #10: Inspect shows wrong Run Kind label

**Severity:** Low
**Location:** `frontend/src/` — InspectMode component, or backend inspect endpoint
**Guide reference:** Detailed Guides §Review and Quality Checks (Inspect Workspace)

**Expected:** Inspecting job `99f0b92c` (P-100 Architect) should show "Run Kind: job" or "Run Kind: P-100/architect".

**Actual:** Shows "Run Kind: role_model_check" for a P-100 Architect job.

**Evidence:** Deep link to `/workspace/{id}/inspect/99f0b92c-...` renders with "Run Kind: role_model_check" in the header metadata.

**Root cause hypothesis:** Inspect component hardcodes or incorrectly infers the run kind from the job data. May be reading from a field that defaults to `role_model_check`.

---

### BUG #11: Inspect shows "No execution steps" despite successful job completion

**Severity:** Low
**Location:** `frontend/src/` — InspectMode Steps tab, or backend step records endpoint
**Guide reference:** Detailed Guides §Review and Quality Checks (Inspect Workspace)

**Expected:** After a job completes successfully, the Steps tab should show execution steps with timing information.

**Actual:** "No execution steps found for this attempt. Steps are recorded when the job runs."

**Evidence:** Job `99f0b92c` completed with status COMPLETED and `current_step: architect`. Backend has step records (verified via direct DB query in other contexts). Frontend shows no steps.

**Root cause hypothesis:** Steps endpoint may require API key auth (returning empty on 401), or the frontend queries by a different ID than what the executor uses for step records.

---

## Guide Inconsistencies

### GC-1: Job status indicator doesn't exist
**Guide text (Step 5):** "Watch the job status change from PENDING → PROCESSING → COMPLETED."
**Reality:** No status indicator exists in the Launch Job panel. Related to BUG #4, #5.

### GC-2: Sidebar navigation broken but not flagged in walkthrough
**Guide text (Step 6):** "In the left sidebar, click Writing mode"
**Reality:** Sidebar buttons don't navigate (BUG #6). This is documented in troubleshooting but NOT mentioned as a known issue in the main walkthrough. Users following Step 6 will be stuck on the Planning view with no explanation.

### GC-3: NARRATIVE_INFERENCE_MODEL not mentioned as required
**Guide text (Setup):** Lists `NARRATIVE_INFERENCE_BACKEND`, `NARRATIVE_INFERENCE_BASE_URL`, `NARRATIVE_INFERENCE_API_KEY`, `NARRATIVE_INFERENCE_MODEL`, and `NARRATIVE_INFERENCE_TIMEOUT_SECONDS` in the env var table. However, `NARRATIVE_INFERENCE_MODEL` is marked as "Recommended" (not required), even though the job fails without it. The model name must match what llama.cpp has loaded.

### GC-4: Manuscript display doesn't work
**Guide text (Step 6):** "The Manuscripts section lists your manuscripts — click the generated chapter"
**Reality:** BUG #7 — no manuscripts ever appear. Entire Step 6 and Step 7 are blocked.

---

## Environment Notes

- Backend: FastAPI on port 8000, SQLite persistence
- Frontend: Vite dev server on port 5173
- Model: llama.cpp serving Qwen3.6-27B-Q5_K_M-mtp.gguf on port 8080
- Auth: `API_KEY=test-key-123` set in `.env`, but frontend doesn't have the key configured → many v1 endpoints return 401
- `.env` was missing `NARRATIVE_INFERENCE_MODEL` — had to add it during walkthrough
