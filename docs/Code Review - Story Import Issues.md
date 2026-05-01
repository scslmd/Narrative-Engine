# Story Import — Code Review Issues

> **Date:** 2026-05-01
> **Branch:** (to be created)
> **Audit source:** Full codebase review of story import pipeline

---

## High Severity

### H-1: Zero test coverage for MultiPassImportService

**File:** `app/services/multi_pass_import.py` (1176 lines)
**Impact:** Entire multi-pass pipeline is untested. Bugs in fallback paths, retry logic, character consolidation, and planning synthesis will go undetected.

**Current state:** 0 dedicated tests. Tests only exercise the single-pass path through `StoryImportService`.

**Untested areas:**
- `_retry_with_backoff()` — exponential backoff for LLM calls
- `_fallback_structure()` — fixed-size chunking when LLM fails
- `_consolidate_characters()` / `_build_fallback_characters()` — character consolidation and fallback
- `_consolidate_world_bible()` / `_build_fallback_world_bible()` — world bible dedup
- `_detect_arcs()` / `_build_fallback_arcs()` — arc detection and fallback
- `_synthesize_planning()` — Phase 3d planning synthesis
- `_normalize_sequences()` — sequence normalization
- `_find_or_create_name()` — character name matching/dedup
- `analyze_large_story()` — full multi-pass orchestration

**Fix:** Add dedicated test file `tests/test_multi_pass_import.py` with stubbed LLM backend.

---

### H-2: Zero test coverage for ImportJobManager

**File:** `app/services/import_jobs.py` (125 lines)
**Impact:** Async job management, thread safety, TTL cleanup, and error handling are unverified.

**Untested areas:**
- `submit()` — job creation and thread pool submission
- `get_status()` — polling endpoint response
- `update_progress()` — progress state mutation
- `complete()` / `fail()` — terminal state transitions
- `_worker()` — worker thread error handling
- `cleanup_expired()` — TTL-based job removal
- Thread safety under concurrent access

**Fix:** Add dedicated test file `tests/test_import_jobs.py` with mock workers.

---

### H-3: Progress callback path untested

**File:** `app/services/story_import.py` — `import_story_with_progress()` (line 189)
**Impact:** Progress updates during multi-pass analysis are not verified. Client polling may show stale or incorrect phase/chapter counts.

**Fix:** Add tests that verify progress callback invocations with expected phase names and data.

---

## Medium Severity

### M-1: Redundant `import sqlite3` inside method

**File:** `app/services/story_import.py:286`
**Line:**
```python
def _create_project(self, request: StoryImportRequest) -> str:
    import sqlite3  # <-- already imported at module level (line 6)
```
**Impact:** Dead code. Module-level import shadows this local import.

**Fix:** Remove line 286.

---

### M-2: Duplicate `logger` assignment

**File:** `app/api/projects.py`
**Lines:** 9 and 83
```python
# Line 9
logger = logging.getLogger(__name__)

# Line 83 (inside build_projects_router)
logger = logging.getLogger(__name__)
```
**Impact:** Second assignment is redundant. Both resolve to the same logger name.

**Fix:** Remove line 83.

---

### M-3: Dead import `RequestValidationError`

**File:** `app/api/projects.py:8`
**Line:**
```python
from fastapi.exceptions import RequestValidationError
```
**Impact:** Imported but never referenced anywhere in the file. Will fail if `no-unused-imports` lint rule is enabled.

**Fix:** Remove line 8.

---

### M-4: Dead parameter `story_text` in ImportJobManager.submit()

**File:** `app/services/import_jobs.py:42-43`
**Line:**
```python
def submit(
    self, story_text: str, worker_fn: Callable[..., Any] | None = None, **worker_kwargs: Any
) -> str:
```
**Impact:** `story_text` is accepted as a positional argument but never consumed inside the method. The story text is already inside the `request` object passed via `worker_kwargs`. This parameter exists only for backward compatibility with the call site at `projects.py:183-184`:
```python
import_id = import_job_manager.submit(
    text,  # <-- passed but unused
    _run_import_worker,
    ...
)
```

**Fix:** Either remove the parameter and update call sites, or add a `deprecated` warning. Breaking change if removed without migration path.

---

### M-5: Dead schema field `raw_story_text`

**File:** `app/schemas/story_import.py:215`
**Line:**
```python
class StoryImportAnalysis(StrictModel):
    ...
    raw_story_text: str = Field(default="", max_length=5_000_000)
```
**Impact:** This field is never populated. The single-pass prompt explicitly sets `"raw_story_text": ""`. Multi-pass doesn't include this field in its output. Dead schema field adds validation overhead for no purpose.

**Fix:** Remove from `StoryImportAnalysis` schema. Verify no downstream code references it.

---

### M-6: `insert_character_profile` has 37 parameters

**File:** `app/utils/db_inserts.py:163`
**Line:**
```python
def insert_character_profile(
    conn, character_id, project_id,
    display_name, role_in_story, archetype,
    # ... 34 more parameters
) -> int:
```
**Impact:** Extremely wide function signature. DB column names and parameter order must be kept in perfect sync (39 values in tuple at line 260). Adding a new column requires touching both the function signature and the INSERT statement, with high risk of ordering mistakes.

**Fix:** Refactor to accept a dataclass or dict. Use `**kwargs` with explicit column mapping. Low priority — works correctly but is fragile for maintenance.

---

## Low Severity

### L-1: `time.sleep` in retry logic not mockable

**File:** `app/services/multi_pass_import.py:7,108`
**Line:**
```python
import time
...
time.sleep(wait)
```
**Impact:** Tests that exercise retry paths will block on real sleeps. Requires `patch("time.sleep")` to avoid delays.

**Fix:** Accept a `sleep_fn` parameter or use a configurable clock. Low impact — retry tests can patch `time.sleep`.

---

### L-2: Total chunks calculation is O(n*m) for large texts

**File:** `app/services/multi_pass_import.py:148-152`
**Line:**
```python
total_chunks = sum(
    len(self._split_into_chunks(story_text[chapter.start_pos:chapter.end_pos]))
    for chapter in structure.chapters
    if story_text[chapter.start_pos:chapter.end_pos].strip()
)
```
**Impact:** Slices story text once per chapter to calculate total chunk count upfront. For very large stories with many chapters, this is O(n*m) where n = total chars, m = number of chapters. Could be expensive for 100K+ char texts.

**Fix:** Estimate total chunks from character counts instead of actual splitting. Or calculate lazily during iteration.

---

## Full Codebase Review Issues (2026-05-01)

### H-4: Zero test coverage for MultiPassImportService fallback paths

**File:** `app/services/multi_pass_import.py`
**Impact:** All fallback paths (`_fallback_structure`, `_build_fallback_characters`, `_build_fallback_world_bible`, `_build_fallback_arcs`) are untested. These are critical resilience paths that activate when LLM calls fail — if they're broken, the entire multi-pass pipeline crashes on transient errors.

**Fix:** Add tests in `tests/test_multi_pass_import.py` that stub the LLM backend to force fallback activation on each phase.

---

### M-7: Bare `raise Exception` in async worker functions (3 occurrences)

**File:** `app/api/projects.py:224,271,301`

| Line | Worker | Message |
|------|--------|---------|
| 224 | `_run_mythos_worker` | `"Mythos extraction failed"` |
| 271 | `_run_pattern_worker` | `"Pattern extraction failed"` |
| 301 | `_run_project_pattern_worker` | `"Pattern extraction from project failed"` |

**Impact:** These bare `raise Exception` calls violate the codebase convention of using domain-specific exception classes. The rest of the codebase has 53 well-structured exception classes (`MythosExtractionError`, `PatternExtractionError`, etc.). Worker exceptions are caught by `ImportJobManager._worker()` and logged as generic failures, losing type information.

**Fix:** Replace with respective domain-specific exceptions:
- Line 224: `raise MythosExtractionError(response.error or "Mythos extraction failed")`
- Line 271: `raise PatternExtractionError(response.error or "Pattern extraction failed")`
- Line 301: `raise PatternExtractionError(response.error or "Pattern extraction from project failed")`

---

### L-3: Dead toast component files (4 files)

**Files:**
- `frontend/src/components/toast/Toast.tsx` — old toast component, superseded by `components/ui/Toast.tsx`
- `frontend/src/components/toast/ToastContainer.tsx` — old container, not imported anywhere
- `frontend/src/components/ToastContainer.tsx` — uses old Zustand toastStore pattern, not imported
- `frontend/src/components/ToastItem.tsx` — only imported by dead `ToastContainer.tsx` above

**Impact:** Dead code increases bundle analysis noise and developer confusion. Not included in production build (tree-shaken) but clutters the component directory.

**Fix:** Delete all 4 files after verifying no imports remain.

---

### L-4: Dead service exports (2 functions)

**Files:**
- `frontend/src/services/patternExtraction.ts:10` — `submitProjectPatternExtraction` only used in tests
- `frontend/src/services/storyImport.ts:36` — `importStory` only used in tests

**Impact:** Exposed in service module but no production component imports them. Will trigger dead-code warnings if ESLint rule is enabled.

**Fix:** Either wire to components or remove exports (keep internal functions for test mocking).

---

### L-5: Dual toast system coexistence

**Files:** `src/hooks/useToast.tsx` (context-based) + `src/stores/toastStore.ts` (Zustand-based)
**Impact:** Two toast systems coexist. Context-based is used by 3 components (App, StoryImportModal, useHealthCheck). Zustand-based is used by 10+ components (BranchList, JobLaunchForm, FindingCard, etc.). Not a bug — both work correctly. Technical debt from migration.

**Fix:** Long-term consolidation to single system. Low priority — not blocking.

---

## Summary

| Severity | Count | Files Affected |
|----------|-------|----------------|
| High | 4 | multi_pass_import.py, import_jobs.py, story_import.py |
| Medium | 7 | story_import.py, projects.py, import_jobs.py, story_import.py (schema), db_inserts.py |
| Low | 5 | multi_pass_import.py, frontend toast files, service exports |

**Recommended order of fix:**
1. M-1, M-2, M-3 — quick cleanup (redundant import, duplicate logger, dead import)
2. M-7 — bare `raise Exception` → domain-specific exceptions (3 lines)
3. H-1, H-2, H-3, H-4 — test coverage for untested modules and fallback paths
4. M-4, M-5 — dead code removal (dead parameter, dead schema field)
5. L-3, L-4 — frontend dead file/export cleanup
6. M-6, L-1, L-2, L-5 — refactoring (low priority, works correctly)
