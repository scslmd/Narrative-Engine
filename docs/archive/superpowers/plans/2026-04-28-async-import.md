# Async Story Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert story import from synchronous blocking endpoint to async submit/poll pattern with progress tracking, file upload support, Phase 1 crash fix, and retry logic.

**Architecture:** ImportJobManager holds in-memory jobs with thread-safe dict. POST submits job to thread pool and returns 202. GET polls for progress/result. MultiPassImportService accepts progress callback. Frontend polls every 2s and shows phase + chapter count.

**Tech Stack:** Python (FastAPI, threading, concurrent.futures), TypeScript (React, Axios)

---

## File Structure

| File | Responsibility |
|------|----------------|
| `app/services/import_jobs.py` | NEW — ImportJob dataclass, ImportJobManager, worker function |
| `app/schemas/story_import.py` | Modify — add ImportSubmitResponse, ImportProgressResponse schemas |
| `app/services/multi_pass_import.py` | Modify — Phase 1 fallback, retry helper, progress callback parameter |
| `app/services/story_import.py` | Modify — accept progress callback, wire to job manager |
| `app/api/projects.py` | Modify — async POST (202), new GET polling endpoint, file upload |
| `app/main.py` | Modify — wire ImportJobManager into router |
| `frontend/src/types/storyImport.ts` | Modify — add ImportProgress, extend StoryImportResponse |
| `frontend/src/services/storyImport.ts` | Modify — add getImportStatus, file upload via FormData |
| `frontend/src/components/projects/StoryImportModal.tsx` | Modify — async flow, progress display, file drop zone |
| `tests/test_import_jobs.py` | NEW — ImportJobManager, retry, Phase 1 fallback, endpoints |

---

## Task Group A: Backend Foundation

### Task 1: Import Job Schemas

**Files:**
- Modify: `app/schemas/story_import.py`

- [ ] **Step 1: Add response schemas to story_import.py**

Add these schemas after `StoryImportResponse`:

```python
class ImportSubmitResponse(StrictModel):
    """Response when import job is submitted (202 Accepted)."""
    import_id: str
    status: str = "pending"


class ImportProgressResponse(StrictModel):
    """Response from polling endpoint — progress or final result."""
    import_id: str
    status: str  # pending | running | completed | failed
    phase: str = ""
    chapters_processed: int = 0
    total_estimated_chapters: int = 0
    result: StoryImportResponse | None = None
    error: str | None = None
```

- [ ] **Step 2: Commit**

```bash
git add app/schemas/story_import.py
git commit -m "feat: add import job response schemas"
```

---

### Task 2: ImportJobManager Core

**Files:**
- Create: `app/services/import_jobs.py`
- Create: `tests/test_import_jobs.py`

- [ ] **Step 1: Write failing test — job creation and status retrieval**

```python
# tests/test_import_jobs.py
from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.schemas.story_import import StoryImportResponse
from app.services.import_jobs import ImportJob, ImportJobManager


def test_create_and_get_job():
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)
    job_id = manager.submit("test-text")

    status = manager.get_status(job_id)
    assert status.import_id == job_id
    assert status.status == "pending"
    assert status.phase == ""
    assert status.chapters_processed == 0
    assert status.result is None


def test_get_nonexistent_job_raises():
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)
    with pytest.raises(KeyError):
        manager.get_status("nonexistent-id")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_import_jobs.py::test_create_and_get_job -v`
Expected: FAIL — ImportJobManager not defined

- [ ] **Step 3: Write minimal implementation**

```python
# app/services/import_jobs.py
from __future__ import annotations

import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable

from ..schemas.story_import import ImportProgressResponse, ImportSubmitResponse

logger = logging.getLogger(__name__)


@dataclass
class ImportJob:
    import_id: str
    status: str = "pending"  # pending | running | completed | failed
    phase: str = ""
    chapters_processed: int = 0
    total_estimated_chapters: int = 0
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)


class ImportJobManager:
    """Manages async story import jobs with in-memory storage.

    Jobs are stored in a thread-safe dict. Completed jobs expire after TTL.
    """

    def __init__(self, max_workers: int = 2, ttl_seconds: int = 300) -> None:
        self._jobs: dict[str, ImportJob] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="import-worker")
        self._ttl_seconds = ttl_seconds

    def submit(self, story_text: str, worker_fn: Callable[..., Any], **worker_kwargs: Any) -> str:
        """Create a job and submit work to thread pool. Returns import_id."""
        import_id = str(uuid.uuid4())

        with self._lock:
            job = ImportJob(import_id=import_id)
            self._jobs[import_id] = job

        self._executor.submit(self._worker, import_id, worker_fn, worker_kwargs)
        return import_id

    def get_status(self, import_id: str) -> ImportProgressResponse:
        """Get current job status for polling."""
        with self._lock:
            job = self._jobs.get(import_id)
            if job is None:
                raise KeyError(f"Import job {import_id} not found or expired")

        return ImportProgressResponse(
            import_id=job.import_id,
            status=job.status,
            phase=job.phase,
            chapters_processed=job.chapters_processed,
            total_estimated_chapters=job.total_estimated_chapters,
            result=job.result,
            error=job.error,
        )

    def update_progress(self, import_id: str, **kwargs: Any) -> None:
        """Update job progress from worker thread."""
        with self._lock:
            job = self._jobs.get(import_id)
            if job is None:
                return
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)

    def complete(self, import_id: str, result: Any) -> None:
        """Mark job as completed with result."""
        self.update_progress(import_id, status="completed", result=result)

    def fail(self, import_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        self.update_progress(import_id, status="failed", error=error)

    def _worker(self, import_id: str, worker_fn: Callable[..., Any], kwargs: dict[str, Any]) -> None:
        """Thread pool worker: run function and update job status."""
        self.update_progress(import_id, status="running")
        try:
            result = worker_fn(**kwargs)
            self.complete(import_id, result)
        except Exception as exc:
            logger.exception("Import job %s failed", import_id)
            self.fail(import_id, str(exc))

    def cleanup_expired(self) -> int:
        """Remove completed jobs older than TTL. Returns count removed."""
        now = time.time()
        removed = 0
        with self._lock:
            expired_ids = [
               jid for jid, job in self._jobs.items()
                if job.status in ("completed", "failed") and (now - job.created_at) > self._ttl_seconds
            ]
            for jid in expired_ids:
                del self._jobs[jid]
                removed += 1
        return removed

    def shutdown(self, wait: bool = True) -> None:
        """Shut down thread pool."""
        self._executor.shutdown(wait=wait)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_import_jobs.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/services/import_jobs.py tests/test_import_jobs.py
git commit -m "feat: add ImportJobManager with thread-safe job tracking"
```

---

### Task 3: ImportJobManager TTL Cleanup Tests

**Files:**
- Modify: `tests/test_import_jobs.py`

- [ ] **Step 1: Add TTL cleanup tests**

```python
def test_cleanup_removes_expired_completed_jobs():
    manager = ImportJobManager(max_workers=2, ttl_seconds=0)
    job_id = manager.submit("test")
    manager.complete(job_id, StoryImportResponse(project_id="p1", status="completed", message="ok"))

    removed = manager.cleanup_expired()
    assert removed == 1

    with pytest.raises(KeyError):
        manager.get_status(job_id)


def test_cleanup_keeps_running_jobs():
    manager = ImportJobManager(max_workers=2, ttl_seconds=0)
    job_id = manager.submit("test")
    manager.update_progress(job_id, status="running", phase="analysis")

    removed = manager.cleanup_expired()
    assert removed == 0
    status = manager.get_status(job_id)
    assert status.status == "running"


def test_update_progress_sets_fields():
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)
    job_id = manager.submit("test")

    manager.update_progress(
        job_id,
        status="running",
        phase="chapter_analysis",
        chapters_processed=5,
        total_estimated_chapters=12,
    )

    status = manager.get_status(job_id)
    assert status.status == "running"
    assert status.phase == "chapter_analysis"
    assert status.chapters_processed == 5
    assert status.total_estimated_chapters == 12


def test_fail_sets_error_message():
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)
    job_id = manager.submit("test")

    manager.fail(job_id, "LLM unavailable")

    status = manager.get_status(job_id)
    assert status.status == "failed"
    assert status.error == "LLM unavailable"


def test_worker_runs_function_and_updates_status(tmp_path):
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)

    def my_worker(text: str):
        return StoryImportResponse(project_id="p1", status="completed", message="ok")

    job_id = manager.submit("test-text", my_worker, text="test-text")
    time.sleep(0.5)  # wait for worker thread

    status = manager.get_status(job_id)
    assert status.status == "completed"
    assert status.result.status == "completed"

    manager.shutdown(wait=False)


def test_worker_catches_exception_and_marks_failed(tmp_path):
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)

    def failing_worker(text: str):
        raise RuntimeError("boom")

    job_id = manager.submit("test-text", failing_worker, text="test-text")
    time.sleep(0.5)

    status = manager.get_status(job_id)
    assert status.status == "failed"
    assert "boom" in (status.error or "")

    manager.shutdown(wait=False)
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `python -m pytest tests/test_import_jobs.py -v`
Expected: 8 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_import_jobs.py
git commit -m "test: add ImportJobManager TTL cleanup and worker tests"
```

---

## Task Group B: Error Handling Improvements

### Task 4: Phase 1 Fallback Fix

**Files:**
- Modify: `app/services/multi_pass_import.py`
- Modify: `tests/test_multi_pass_import.py`

- [ ] **Step 1: Write failing test — Phase 1 LLM failure triggers fallback**

Add to `tests/test_multi_pass_import.py`:

```python
def test_detect_structure_falls_back_on_llm_error():
    """Phase 1 should fall back to _fallback_structure on LLM failure, not crash."""
    error_backend = ErrorInferenceBackend()
    service = MultiPassImportService(error_backend)

    story_text = "A" * 50_000  # large enough to need structure detection
    result = service._detect_structure(story_text)

    # Should return fallback, not raise
    assert result is not None
    assert len(result.chapters) >= 1


class ErrorInferenceBackend(InferenceBackend):
    """Always raises InferenceBackendError."""

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return InferenceProviderDescriptor(
            backend="stub",
            display_name="Error Backend",
            transport="stub",
            base_url="http://localhost:9000/v1",
            default_model="error-model",
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["error"],
        )

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        raise InferenceBackendError("Connection refused", code="connection_error")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_multi_pass_import.py::test_detect_structure_falls_back_on_llm_error -v`
Expected: FAIL — current code raises InferenceBackendError

- [ ] **Step 3: Fix _detect_structure to catch exceptions and fall back**

Current code at line ~181:
```python
def _detect_structure(self, story_text: str) -> StoryStructureDetection:
    # ... builds request, calls LLM, parses response
    # If LLM raises, exception propagates — this is the bug
```

Change to wrap in try/except:

```python
def _detect_structure(self, story_text: str) -> StoryStructureDetection:
    try:
        from .runtime_prompts import build_structure_detection_request
        request = build_structure_detection_request(
            story_text=story_text[:STRUCTURE_SCAN_LIMIT],
            default_model=self._inferencer.descriptor.default_model,
        )
        response = self._inferencer.generate_text(request)
        data = extract_json(response.content)
        return StoryStructureDetection(**data)
    except (InferenceBackendError, ValueError, ValidationError) as exc:
        logger.warning("Structure detection failed, using fallback: %s", exc)
        return self._fallback_structure(story_text)
```

Read the current `_detect_structure` at line 181 to see exact code to replace. The key change is wrapping the LLM call and JSON parsing in try/except and returning `self._fallback_structure(story_text)` on any exception.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_multi_pass_import.py::test_detect_structure_falls_back_on_llm_error -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/multi_pass_import.py tests/test_multi_pass_import.py
git commit -m "fix: Phase 1 structure detection falls back on LLM failure"
```

---

### Task 5: Retry with Backoff Helper

**Files:**
- Modify: `app/services/multi_pass_import.py`
- Modify: `tests/test_multi_pass_import.py`

- [ ] **Step 1: Write failing test — retry succeeds after transient failures**

Add to `tests/test_multi_pass_import.py`:

```python
def test_retry_with_backoff_succeeds_after_failures():
    service = MultiPassImportService(MultiPhaseInferenceBackend(responses=["{}"]))

    call_count = [0]
    def flaky_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise InferenceBackendError("timeout", code="timeout")
        return "success"

    result = service._retry_with_backoff(flaky_func, (), {}, max_retries=3)
    assert result == "success"
    assert call_count[0] == 3


def test_retry_with_backoff_raises_after_max_retries():
    service = MultiPassImportService(MultiPhaseInferenceBackend(responses=["{}"]))

    def always_fails():
        raise InferenceBackendError("error", code="error")

    with pytest.raises(InferenceBackendError):
        service._retry_with_backoff(always_fails, (), {}, max_retries=2)


def test_retry_with_backoff_no_retry_on_first_success():
    call_count = [0]
    def succeeds_immediately():
        call_count[0] += 1
        return "ok"

    service = MultiPhaseInferenceBackend(responses=["{}"])
    result = MultiPassImportService(service)._retry_with_backoff(succeeds_immediately, (), {}, max_retries=3)
    assert result == "ok"
    assert call_count[0] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_multi_pass_import.py::test_retry_with_backoff_succeeds_after_failures -v`
Expected: FAIL — _retry_with_backoff not defined

- [ ] **Step 3: Add retry helper to MultiPassImportService**

Add as a method on the class (after `__init__`):

```python
import time as _time

def _retry_with_backoff(
    self,
    func: Callable[..., Any],
    args: tuple = (),
    kwargs: dict[str, Any] | None = None,
    max_retries: int = 2,
) -> Any:
    """Call func with exponential backoff on LLM/transient errors."""
    if kwargs is None:
        kwargs = {}
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except (InferenceBackendError, ValueError, ValidationError) as exc:
            if attempt == max_retries:
                raise
            wait = min(0.5 * (2 ** attempt), 5.0)
            logger.warning(
                "Retry %d/%d after %.1fs: %s",
                attempt + 1, max_retries, wait, exc,
            )
            _time.sleep(wait)
    # unreachable but satisfies type checker
    raise RuntimeError("Retry loop exited unexpectedly")
```

Add `from typing import Callable` to imports if not already present.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_multi_pass_import.py -k "retry_with_backoff" -v`
Expected: 3 passed

- [ ] **Step 5: Wire retry into critical LLM calls**

Apply `_retry_with_backoff` to Phase 1 (already wrapped in try/except from Task 4), Phase 3a, 3b, 3c. Change these call sites:

In `_consolidate_characters` — wrap the `generate_text` call:
```python
# Before:
response = self._inferencer.generate_text(request)

# After:
response = self._retry_with_backoff(
    self._inferencer.generate_text, (request,), {}, max_retries=2
)
```

Same pattern for `_consolidate_world_bible` and `_detect_arcs`.

- [ ] **Step 6: Run full multi-pass test suite**

Run: `python -m pytest tests/test_multi_pass_import.py -v`
Expected: All pass (including existing 38 tests)

- [ ] **Step 7: Commit**

```bash
git add app/services/multi_pass_import.py tests/test_multi_pass_import.py
git commit -m "feat: add retry with backoff for critical LLM calls"
```

---

### Task 6: Progress Callbacks in MultiPassImportService

**Files:**
- Modify: `app/services/multi_pass_import.py`

- [ ] **Step 1: Add progress callback parameter to analyze_large_story**

Change method signature:
```python
def analyze_large_story(
    self,
    story_text: str,
    genre_hint: str | None = None,
    tone_hint: str | None = None,
    on_progress: Callable[[str, dict[str, Any]], None] | None = None,
) -> StoryImportAnalysis:
```

Add `Callable` to imports: `from typing import Any, Callable`

- [ ] **Step 2: Wire progress calls at each phase**

In the method body, add callback invocations:

After Phase 1 (line ~100):
```python
structure = self._detect_structure(story_text)
total_chapters = len(structure.chapters) if structure.chapters else 1
if on_progress:
    on_progress("structure_detection", {
        "chapters_processed": 0,
        "total_estimated_chapters": total_chapters,
    })

if not structure.chapters:
    structure = self._fallback_structure(story_text)
    total_chapters = 1
```

In Phase 2 loop (after each chapter, around line ~149):
```python
            chapters_processed += 1
            if on_progress:
                on_progress("chapter_analysis", {
                    "chapters_processed": chapters_processed,
                    "total_estimated_chapters": total_chapters,
                })
```

After Phase 3a:
```python
if on_progress:
    on_progress("consolidation_characters", {
        "chapters_processed": chapters_processed,
        "total_estimated_chapters": total_chapters,
    })
```

After Phase 3b:
```python
if on_progress:
    on_progress("consolidation_world", {
        "chapters_processed": chapters_processed,
        "total_estimated_chapters": total_chapters,
    })
```

After Phase 3c:
```python
if on_progress:
    on_progress("consolidation_arcs", {
        "chapters_processed": chapters_processed,
        "total_estimated_chapters": total_chapters,
    })
```

- [ ] **Step 3: Add test for progress callback**

Add to `tests/test_multi_pass_import.py`:

```python
def test_analyze_large_story_calls_progress_callback():
    """Progress callback should be invoked at each phase."""
    progress_log: list[tuple[str, dict]] = []

    def on_progress(phase: str, data: dict):
        progress_log.append((phase, data))

    responses = [
        json.dumps({
            "project_name": "Test",
            "total_estimated_words": 50000,
            "structure_type": "traditional_novel",
            "chapters": [
                {"id": "chapter-1", "title": "Chapter 1", "section_type": "chapter",
                 "start_line": 1, "end_line": 50, "start_pos": 0, "end_pos": 5000},
                {"id": "chapter-2", "title": "Chapter 2", "section_type": "chapter",
                 "start_line": 51, "end_line": 100, "start_pos": 5000, "end_pos": 10000},
            ],
            "hints": {},
        }),
        json.dumps({
            "chapter_id": "chapter-1", "characters": [], "world_details": [],
            "plot_events": [{"summary": "Event 1", "significance": "development"}],
        }),
        json.dumps({
            "chapter_id": "chapter-2", "characters": [], "world_details": [],
            "plot_events": [{"summary": "Event 2", "significance": "development"}],
        }),
        json.dumps([]),  # character consolidation
        json.dumps([]),  # world bible consolidation
        json.dumps({
            "premise": "Test story", "logline": "ll", "thematic_spine": "theme",
            "emotional_promise": "promise", "target_audience": "adults",
            "complexity_level": "MEDIUM", "story_structure": "THREE_ACT",
            "genre": "fantasy", "tone": "dark", "pov": "THIRD_LIMITED",
            "story_arcs": [], "sequences": [{"title": "Main", "summary": "s", "chapters": []}],
            "narrative_constraints": [], "success_definition": "sd",
        }),
    ]

    backend = MultiPhaseInferenceBackend(responses=responses)
    service = MultiPassImportService(backend)

    story_text = "A" * 35_000
    result = service.analyze_large_story(story_text, on_progress=on_progress)

    phases = [p for p, _ in progress_log]
    assert "structure_detection" in phases
    assert "chapter_analysis" in phases
    assert any("consolidation" in p for p in phases)

    # Verify chapter count was reported
    chapter_data = [d for _, d in progress_log if d.get("total_estimated_chapters") > 0]
    assert len(chapter_data) > 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_multi_pass_import.py::test_analyze_large_story_calls_progress_callback -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/multi_pass_import.py tests/test_multi_pass_import.py
git commit -m "feat: add progress callback to multi-pass import pipeline"
```

---

## Task Group C: Async Endpoints

### Task 7: Async POST Endpoint + GET Polling

**Files:**
- Modify: `app/api/projects.py`
- Modify: `app/main.py`
- Create: `tests/test_import_jobs.py` (extend existing)

- [ ] **Step 1: Modify projects.py — add async import endpoints**

Replace the current synchronous import endpoint and add polling:

```python
    if import_service is not None:
        from ..schemas.story_import import ImportSubmitResponse, ImportProgressResponse
        from fastapi import UploadFile, File, Form

        @router.post("/import-story", response_model=ImportSubmitResponse, status_code=202)
        async def import_story(
            story_text: str | None = Form(None),
            project_name: str | None = Form(None),
            genre: str | None = Form(None),
            tone: str | None = Form(None),
            project_id: str | None = Form(None),
            file: UploadFile | None = File(None),
        ):
            text = story_text
            if file is not None:
                ext = (file.filename or "").lower().rsplit(".", 1)[-1]
                if ext not in ("txt", "md"):
                    raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
                text = await file.read()
                text = text.decode("utf-8").strip()

            if not text or len(text.strip()) < 50:
                raise HTTPException(status_code=400, detail="Story text must be at least 50 characters")

            from ..schemas.story_import import StoryImportRequest
            request = StoryImportRequest(
                project_name=project_name or "",
                story_text=text,
                project_id=project_id or None,
                genre=genre or None,
                tone=tone or None,
            )

            job_manager: ImportJobManager = request.state._import_job_manager  # type: ignore
            import_id = job_manager.submit(
                text,
                _run_import_worker,
                import_service=import_service,
                request=request,
                job_manager=job_manager,
                import_id=import_id,
            )
            return ImportSubmitResponse(import_id=import_id)

        @router.get("/import/{import_id}", response_model=ImportProgressResponse)
        def get_import_status(import_id: str):
            from fastapi import Request
            job_manager: ImportJobManager = Request._import_job_manager  # type: ignore
            try:
                return job_manager.get_status(import_id)
            except KeyError:
                raise HTTPException(status_code=404, detail=f"Import {import_id} not found or expired")
```

Wait — the above approach with `request.state` won't work cleanly. Let me use a dependency injection pattern instead. Better approach: pass the job manager through the router builder.

Revised approach — modify `build_projects_router` to accept `import_job_manager`:

```python
def build_projects_router(
    project_service: ProjectService,
    import_service: _ImportServiceProtocol | None = None,
    mythos_service: _MythosServiceProtocol | None = None,
    pattern_service: _PatternServiceProtocol | None = None,
    import_job_manager: Any = None,
) -> APIRouter:
```

Then endpoints use it from closure. Let me write the complete revised code:

```python
    if import_service is not None and import_job_manager is not None:
        from ..schemas.story_import import ImportSubmitResponse, ImportProgressResponse
        from ..services.import_jobs import ImportJobManager
        from fastapi import UploadFile, File, Form

        def _run_import_worker(
            import_service: Any,
            request: StoryImportRequest,
            job_manager: ImportJobManager,
            import_id: str,
        ) -> Any:
            def on_progress(phase: str, data: dict[str, Any]) -> None:
                job_manager.update_progress(import_id, phase=phase, **data)

            job_manager.update_progress(import_id, status="running", phase="initializing")

            result = import_service.import_story_with_progress(request, on_progress)
            return result

        @router.post("/import-story", response_model=ImportSubmitResponse, status_code=202)
        async def import_story(
            story_text: str | None = Form(None),
            project_name: str | None = Form(None),
            genre: str | None = Form(None),
            tone: str | None = Form(None),
            project_id: str | None = Form(None),
            file: UploadFile | None = File(None),
        ):
            text = story_text
            if file is not None:
                ext = (file.filename or "").lower().rsplit(".", 1)[-1]
                if ext not in ("txt", "md"):
                    raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
                content = await file.read()
                text = content.decode("utf-8").strip()

            if not text or len(text.strip()) < 50:
                raise HTTPException(status_code=400, detail="Story text must be at least 50 characters")

            request = StoryImportRequest(
                project_name=project_name or "",
                story_text=text,
                project_id=project_id or None,
                genre=genre or None,
                tone=tone or None,
            )

            import_id = import_job_manager.submit(
                text,
                _run_import_worker,
                import_service=import_service,
                request=request,
                job_manager=import_job_manager,
                import_id=import_id,
            )
            return ImportSubmitResponse(import_id=import_id)

        @router.get("/import/{import_id}", response_model=ImportProgressResponse)
        def get_import_status(import_id: str):
            try:
                return import_job_manager.get_status(import_id)
            except KeyError:
                raise HTTPException(status_code=404, detail=f"Import {import_id} not found or expired")
```

- [ ] **Step 2: Add import_story_with_progress to StoryImportService**

Modify `app/services/story_import.py` — add method that accepts progress callback:

```python
def import_story_with_progress(
    self,
    request: StoryImportRequest,
    on_progress: Callable[[str, dict[str, Any]], None] | None = None,
) -> StoryImportResponse:
    """Same as import_story but reports progress via callback."""
    project_id = ""
    analysis_mode = "single_pass"
    chapters_processed = 0
    total_chapters = 0
    warnings: list[str] = []

    try:
        project_id = self._create_project(request)

        if on_progress:
            on_progress("initializing", {"chapters_processed": 0})

        if len(request.story_text) > MULTI_PASS_THRESHOLD:
            analysis_mode = "multi_pass"
            analysis = self._multi_pass_service.analyze_large_story(
                request.story_text,
                genre_hint=request.genre,
                tone_hint=request.tone,
                on_progress=on_progress,
            )
            chapters_processed = len(analysis.sequences[0].chapters) if analysis.sequences else 0
            total_chapters = chapters_processed
        else:
            if on_progress:
                on_progress("analysis", {"chapters_processed": 0})
            analysis = self._analyze_story(request.story_text, request.genre, request.tone)

        if on_progress:
            on_progress("persisting", {"chapters_processed": chapters_processed})

        self._transactional_import(project_id, analysis)
        self._update_manifest(project_id, analysis)

        return StoryImportResponse(
            project_id=project_id,
            status="completed",
            message=f"Successfully imported story into project '{analysis.project_name}'",
            warnings=warnings,
            chapters_processed=chapters_processed,
            total_estimated_chapters=total_chapters,
            analysis_mode=analysis_mode,
        )
    except StoryImportError as exc:
        return StoryImportResponse(
            project_id=project_id,
            status="failed",
            message=str(exc),
            warnings=["Import failed - partial data may exist on retry"],
            chapters_processed=chapters_processed,
            total_estimated_chapters=total_chapters,
            analysis_mode=analysis_mode,
        )
    except InferenceBackendError as exc:
        return StoryImportResponse(
            project_id=project_id,
            status="failed",
            message=f"LLM service unavailable: {exc.code}",
            warnings=["Retry the import when the inference service is available"],
            chapters_processed=chapters_processed,
            total_estimated_chapters=total_chapters,
            analysis_mode=analysis_mode,
        )
```

Add `Callable` to imports in story_import.py.

- [ ] **Step 3: Wire ImportJobManager into main.py**

In `app/main.py`, create the manager and pass it to the router builder. Read current `build_projects_router` call site and add the import_job_manager parameter.

- [ ] **Step 4: Write endpoint tests**

Add to `tests/test_import_jobs.py`:

```python
from fastapi.testclient import TestClient


def test_import_story_returns_202_with_import_id(tmp_path):
    """POST /import-story should return 202 with import_id."""
    from app.main import build_app
    client = TestClient(build_app())

    response = client.post(
        "/projects/import-story",
        data={
            "story_text": "A" * 100,
            "project_name": "Test Project",
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert "import_id" in data
    assert data["status"] == "pending"


def test_import_story_rejects_short_text(tmp_path):
    """POST /import-story should reject text under 50 characters."""
    from app.main import build_app
    client = TestClient(build_app())

    response = client.post(
        "/projects/import-story",
        data={
            "story_text": "too short",
            "project_name": "Test",
        },
    )
    assert response.status_code == 400


def test_get_import_status_returns_progress(tmp_path):
    """GET /import/{id} should return progress."""
    from app.main import build_app
    client = TestClient(build_app())

    submit = client.post(
        "/projects/import-story",
        data={"story_text": "A" * 100, "project_name": "Test"},
    )
    import_id = submit.json()["import_id"]

    response = client.get(f"/projects/import/{import_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == import_id


def test_get_import_status_404_for_unknown_id(tmp_path):
    """GET /import/{id} should return 404 for unknown ID."""
    from app.main import build_app
    client = TestClient(build_app())

    response = client.get("/projects/import/nonexistent-id")
    assert response.status_code == 404
```

- [ ] **Step 5: Run endpoint tests**

Run: `python -m pytest tests/test_import_jobs.py -v`
Expected: All pass (adjust as needed for app startup)

- [ ] **Step 6: Commit**

```bash
git add app/api/projects.py app/services/story_import.py app/main.py tests/test_import_jobs.py
git commit -m "feat: async import endpoint with polling and file upload"
```

---

## Task Group D: Frontend

### Task 8: Frontend Types and Service

**Files:**
- Modify: `frontend/src/types/storyImport.ts`
- Modify: `frontend/src/services/storyImport.ts`

- [ ] **Step 1: Update types**

```typescript
// frontend/src/types/storyImport.ts
export interface StoryImportRequest {
  project_name: string;
  story_text: string;
  project_id?: string;
  genre?: string;
  tone?: string;
}

export interface StoryImportResponse {
  project_id: string;
  status: string;
  message: string;
  warnings: string[];
  chapters_processed: number;
  total_estimated_chapters: number;
  analysis_mode: string;
}

export interface ImportSubmitResponse {
  import_id: string;
  status: "pending";
}

export interface ImportProgress {
  import_id: string;
  status: "pending" | "running" | "completed" | "failed";
  phase: string;
  chapters_processed: number;
  total_estimated_chapters: number;
  result: StoryImportResponse | null;
  error: string | null;
}
```

- [ ] **Step 2: Update service**

```typescript
// frontend/src/services/storyImport.ts
import type {
  StoryImportRequest,
  StoryImportResponse,
  ImportSubmitResponse,
  ImportProgress,
} from '../types/storyImport';
import api from '../lib/api';

export async function submitImport(
  formData: FormData,
): Promise<ImportSubmitResponse> {
  const response = await api.post('/projects/import-story', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  if (response.status !== 202) {
    throw new Error(`Failed to submit import: ${response.status}`);
  }

  return response.data;
}

export async function getImportStatus(
  importId: string,
): Promise<ImportProgress> {
  const response = await api.get(`/projects/import/${importId}`);

  if (response.status !== 200) {
    throw new Error(`Failed to get import status: ${response.status}`);
  }

  return response.data;
}

// Keep backward compat for text-only imports
export async function importStory(
  data: StoryImportRequest,
): Promise<StoryImportResponse> {
  const formData = new FormData();
  formData.append('story_text', data.story_text);
  formData.append('project_name', data.project_name);
  if (data.genre) formData.append('genre', data.genre);
  if (data.tone) formData.append('tone', data.tone);
  if (data.project_id) formData.append('project_id', data.project_id);

  const submit = await submitImport(formData);
  return await _pollForCompletion(submit.import_id);
}

async function _pollForCompletion(
  importId: string,
  intervalMs: number = 2000,
  maxAttempts: number = 300,
): Promise<StoryImportResponse> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const progress = await getImportStatus(importId);

    if (progress.status === 'completed' && progress.result) {
      return progress.result;
    }

    if (progress.status === 'failed') {
      throw new Error(progress.error || 'Import failed');
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error('Import timed out');
}
```

- [ ] **Step 3: Run frontend checks**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/storyImport.ts frontend/src/services/storyImport.ts
git commit -m "feat: frontend async import types and polling service"
```

---

### Task 9: StoryImportModal — Async Flow, Progress, File Upload

**Files:**
- Modify: `frontend/src/components/projects/StoryImportModal.tsx`

- [ ] **Step 1: Add state for progress tracking and file handling**

Add to component state:
```tsx
const [importId, setImportId] = useState<string | null>(null);
const [importPhase, setImportPhase] = useState('');
const [chaptersProcessed, setChaptersProcessed] = useState(0);
const [totalChapters, setTotalChapters] = useState(0);
const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
```

- [ ] **Step 2: Add file drop zone and handler**

Add file input handling in the story mode section. After the textarea, add:

```tsx
{importMode === 'story' && (
  <>
    <div
      className="mt-4 flex items-center justify-center px-6 py-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 cursor-pointer transition-colors"
      onClick={() => document.getElementById('file-upload')?.click()}
    >
      <div className="text-center">
        <Upload className="w-6 h-6 mx-auto text-gray-400" />
        <p className="mt-2 text-sm text-gray-500">
          {uploadedFileName || 'Drop a .txt or .md file, or click to browse'}
        </p>
      </div>
    </div>
    <input
      id="file-upload"
      type="file"
      accept=".txt,.md"
      className="hidden"
      onChange={(e) => {
        const file = e.target.files?.[0];
        if (file) {
          setUploadedFileName(file.name);
          // Read file into storyText state
          const reader = new FileReader();
          reader.onload = (ev) => {
            setStoryText(ev.target?.result as string);
          };
          reader.readAsText(file);
        }
      }}
    />
  </>
)}
```

- [ ] **Step 3: Replace submit handler with async flow**

Replace the `story` mode branch in `handleSubmit`:

```tsx
      } else {
        const formData = new FormData();
        formData.append('story_text', storyText);
        formData.append('project_name', projectName.trim());
        if (genre.trim()) formData.append('genre', genre.trim());
        if (tone.trim()) formData.append('tone', tone.trim());

        const submit = await submitImport(formData);
        setImportId(submit.import_id);
        setImportPhase('Starting import...');

        // Poll for progress
        pollRef.current = setInterval(async () => {
          try {
            const progress = await getImportStatus(submit.import_id);
            setImportPhase(progress.phase || 'Processing...');
            setChaptersProcessed(progress.chapters_processed);
            setTotalChapters(progress.total_estimated_chapters);

            if (progress.status === 'completed' && progress.result) {
              clearInterval(pollRef.current!);
              setIsImporting(false);
              setImportId(null);

              if (progress.result.warnings?.length > 0) {
                setWarnings(progress.result.warnings);
              }
              navigate(`/workspace/${progress.result.project_id}`);
              queryClient.invalidateQueries({ queryKey: ['projects'] });
              onClose();
            } else if (progress.status === 'failed') {
              clearInterval(pollRef.current!);
              setIsImporting(false);
              setImportId(null);
              setError(progress.error || 'Import failed');
            }
          } catch {
            // Keep polling on transient errors
          }
        }, 2000);

        return; // Exit early — polling handles completion
      }
```

- [ ] **Step 4: Add progress display UI**

Replace or augment the spinner section to show phase + chapter count:

```tsx
{isImporting && (
  <div className="flex flex-col items-center py-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
    <p className="mt-4 text-sm text-gray-600">
      {importPhase || 'Analyzing...'}
    </p>
    {totalChapters > 0 && (
      <div className="mt-2 w-full max-w-xs">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Chapter {chaptersProcessed} of {totalChapters}</span>
          <span>{Math.round((chaptersProcessed / totalChapters) * 100)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{ width: `${(chaptersProcessed / totalChapters) * 100}%` }}
          />
        </div>
      </div>
    )}
    {importId && (
      <button
        type="button"
        onClick={() => {
          if (pollRef.current) clearInterval(pollRef.current);
          setIsImporting(false);
          setImportId(null);
        }}
        className="mt-4 text-sm text-gray-500 hover:text-gray-700"
      >
        Cancel (import will continue in background)
      </button>
    )}
  </div>
)}
```

- [ ] **Step 5: Add cleanup effect**

Add a useEffect to clean up polling on unmount:
```tsx
useEffect(() => {
  return () => {
    if (pollRef.current) clearInterval(pollRef.current);
  };
}, []);
```

- [ ] **Step 6: Run frontend checks**

Run: `cd frontend && npm run lint && npm run typecheck && npm run build`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/projects/StoryImportModal.tsx
git commit -m "feat: async import UI with progress bar, file upload, and cancellation"
```

---

## Task Group E: Validation

### Task 10: Full Validation

- [ ] **Step 1: Run parallel cluster tests**

Run: `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py`
Expected: All pass (including new test_import_jobs.py tests)

- [ ] **Step 2: Run serial tests**

Run: `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records`
Expected: All pass

- [ ] **Step 3: Run frontend checks**

Run: `cd frontend && npm run lint && npm run typecheck && npm run build`
Expected: All pass

- [ ] **Step 4: Update AGENTS.md test baseline**

Update the test baseline in AGENTS.md with new counts.

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md
git commit -m "docs: update test baseline for async import"
```
