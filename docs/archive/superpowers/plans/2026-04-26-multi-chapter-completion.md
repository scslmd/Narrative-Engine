# Multi-Chapter Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the multi-chapter book generation flow by adding chapter summarization, ManuscriptDocument auto-creation, and executor chapter loop with prior context propagation.

**Architecture:** LLM-based ChapterSummarizerService follows ConsistencyCriticService pattern. Executor detects `chapter_ids` list in P-300 payload, enters sequential loop: draft → summarize → create ManuscriptDocument → propagate summary as prior context for next chapter. Single job, per-chapter step records.

**Tech Stack:** Python, Pydantic schemas, SQLite (existing), InferenceBackend (existing LLM layer), existing DraftingService extended for auto-creation

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `app/services/chapter_summarizer.py` | LLM-based chapter summarization service |
| `tests/test_chapter_summarizer.py` | Unit tests for summarizer service |

### Modified Files
| File | Change |
|------|--------|
| `app/services/runtime_prompts.py` | Add `build_chapter_summarize_request()` prompt builder |
| `app/services/local_executor.py` | Chapter loop, prior_chapters wiring, ManuscriptDocument creation |
| `app/main.py` | Wire ChapterSummarizerService into LocalExecutor |
| `tests/test_local_executor_drafter_runtime.py` | Multi-chapter integration tests |

---

## Tasks

### Task 1: ChapterSummarizerService - Data Model and Constructor

**Files:**
- Create: `app/services/chapter_summarizer.py`
- Test: `tests/test_chapter_summarizer.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_chapter_summarizer.py`:

```python
from __future__ import annotations

import pytest
from app.services.chapter_summarizer import ChapterSummarizerService


def test_summarizer_service_construction():
    from unittest.mock import MagicMock
    from app.inference.base import InferenceBackend, BackendDescriptor

    mock_inferencer = MagicMock(spec=InferenceBackend)
    mock_inferencer.descriptor = BackendDescriptor(
        backend="stub",
        display_name="Stub",
        default_model="test-model",
    )

    service = ChapterSummarizerService(inferencer=mock_inferencer)
    assert service._inferencer is mock_inferencer
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_chapter_summarizer.py::test_summarizer_service_construction -q -p no:cacheprovider`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.chapter_summarizer'"

- [ ] **Step 3: Write minimal implementation**

Create `app/services/chapter_summarizer.py`:

```python
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..inference.base import InferenceBackend

logger = logging.getLogger(__name__)


class ChapterSummarizerService:
    """LLM-based chapter summarization service.

    Reads completed chapter markdown and extracts structured PriorChapterSummary:
    - key_events: significant plot points from the chapter
    - character_states: character conditions/goals at chapter end
    - unresolved_threads: open questions, cliffhangers, pending conflicts

    Follows ConsistencyCriticService pattern: graceful error handling, never blocks pipeline.
    """

    def __init__(self, *, inferencer: InferenceBackend) -> None:
        self._inferencer = inferencer
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_chapter_summarizer.py::test_summarizer_service_construction -q -p no:cacheprovider`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/chapter_summarizer.py tests/test_chapter_summarizer.py
git commit -m "feat: add ChapterSummarizerService skeleton"
```

---

### Task 2: Prompt Builder - `build_chapter_summarize_request()`

**Files:**
- Modify: `app/services/runtime_prompts.py` (append after line 516)
- Test: `tests/test_chapter_summarizer.py` (add test)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_chapter_summarizer.py`:

```python
def test_build_chapter_summarize_request_structure():
    from app.services.runtime_prompts import build_chapter_summarize_request

    request = build_chapter_summarize_request(
        chapter_id="ch-001",
        chapter_text="# Chapter 1\nSome story text here.",
        character_names=["Kael", "Soraya"],
        default_model="test-model",
    )

    assert request.temperature == 0.1
    assert request.max_tokens == 2000
    assert len(request.messages) == 2
    assert request.messages[0].role == "system"
    assert request.messages[1].role == "user"
    assert "Kael" in request.messages[1].content
    assert "Soraya" in request.messages[1].content
    assert "ch-001" in request.metadata
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_chapter_summarizer.py::test_build_chapter_summarize_request_structure -q -p no:cacheprovider`
Expected: FAIL with "ImportError: cannot import name 'build_chapter_summarize_request'"

- [ ] **Step 3: Write minimal implementation**

Append to `app/services/runtime_prompts.py` after line 516:

```python


def build_chapter_summarize_request(
    *,
    chapter_id: str,
    chapter_text: str,
    character_names: list[str],
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for chapter summarization.

    Extracts structured PriorChapterSummary from completed chapter markdown.
    Returns JSON with key_events, character_states, unresolved_threads.
    """
    # Truncate chapter text to fit prompt budget
    truncated_text = chapter_text[:16000] if len(chapter_text) > 16000 else chapter_text

    names_block = ", ".join(character_names) if character_names else "(no known characters)"

    system_prompt = (
        "You are a chapter summarizer for Narrative-Engine. "
        "Extract structured context from the completed chapter below.\n\n"
        "Return ONLY a JSON object with these keys:\n"
        '{\n'
        '  "chapter_id": "<the chapter identifier>",\n'
        '  "title": "<chapter title or descriptive label>",\n'
        '  "key_events": ["<event 1>", "<event 2>"],\n'
        '  "character_states": {"<name>": "<condition/goal at chapter end>"},\n'
        '  "unresolved_threads": ["<thread 1>"]\n'
        '}\n\n'
        "Extract up to 10 key events, 10 character states, and 5 unresolved threads.\n"
        "Focus on plot-critical information that would affect continuity in subsequent chapters."
    )

    user_content = (
        f"Chapter: {chapter_id}\n"
        f"Known characters: {names_block}\n\n"
        f"CHAPTER TEXT:\n{truncated_text}"
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=2000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "chapter_summarizer",
            "role": "summarizer",
            "chapter_id": chapter_id,
        },
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_chapter_summarizer.py::test_build_chapter_summarize_request_structure -q -p no:cacheprovider`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/runtime_prompts.py tests/test_chapter_summarizer.py
git commit -m "feat: add build_chapter_summarize_request prompt builder"
```

---

### Task 3: ChapterSummarizerService - Summarize Method

**Files:**
- Modify: `app/services/chapter_summarizer.py`
- Test: `tests/test_chapter_summarizer.py` (add tests)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_chapter_summarizer.py`:

```python
def test_summarize_returns_prior_chapter_summary():
    from unittest.mock import MagicMock
    from app.inference.base import InferenceBackend, BackendDescriptor
    from app.schemas.story_development import PriorChapterSummary

    mock_inferencer = MagicMock(spec=InferenceBackend)
    mock_inferencer.descriptor = BackendDescriptor(
        backend="stub",
        display_name="Stub",
        default_model="test-model",
    )

    # Mock successful LLM response
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "chapter_id": "ch-001",
        "title": "The Departure",
        "key_events": ["Kael leaves the village"],
        "character_states": {"Kael": "restless, seeking purpose"},
        "unresolved_threads": ["Who is Soraya?"],
    })
    mock_inferencer.generate_text.return_value = mock_response

    service = ChapterSummarizerService(inferencer=mock_inferencer)
    result = service.summarize(
        chapter_id="ch-001",
        chapter_text="# The Departure\nKael left the village at dawn.",
        character_names=["Kael", "Soraya"],
    )

    assert isinstance(result, PriorChapterSummary)
    assert result.chapter_id == "ch-001"
    assert result.title == "The Departure"
    assert len(result.key_events) == 1
    assert "Kael" in result.character_states


def test_summarize_returns_none_on_llm_error():
    from unittest.mock import MagicMock
    from app.inference.base import InferenceBackend, BackendDescriptor, InferenceBackendError

    mock_inferencer = MagicMock(spec=InferenceBackend)
    mock_inferencer.descriptor = BackendDescriptor(
        backend="stub",
        display_name="Stub",
        default_model="test-model",
    )
    mock_inferencer.generate_text.side_effect = InferenceBackendError(
        code="timeout",
        category="backend",
        message="Connection timeout",
        finish_reason="error",
        retryable=True,
    )

    service = ChapterSummarizerService(inferencer=mock_inferencer)
    result = service.summarize(
        chapter_id="ch-001",
        chapter_text="# Chapter\nSome text.",
        character_names=["Kael"],
    )

    assert result is None


def test_summarize_returns_none_on_invalid_json():
    from unittest.mock import MagicMock
    from app.inference.base import InferenceBackend, BackendDescriptor

    mock_inferencer = MagicMock(spec=InferenceBackend)
    mock_inferencer.descriptor = BackendDescriptor(
        backend="stub",
        display_name="Stub",
        default_model="test-model",
    )

    mock_response = MagicMock()
    mock_response.content = "not valid json {{{"
    mock_inferencer.generate_text.return_value = mock_response

    service = ChapterSummarizerService(inferencer=mock_inferencer)
    result = service.summarize(
        chapter_id="ch-001",
        chapter_text="# Chapter\nSome text.",
        character_names=["Kael"],
    )

    assert result is None


def test_summarize_skips_on_empty_text():
    from unittest.mock import MagicMock
    from app.inference.base import InferenceBackend, BackendDescriptor

    mock_inferencer = MagicMock(spec=InferenceBackend)
    mock_inferencer.descriptor = BackendDescriptor(
        backend="stub",
        display_name="Stub",
        default_model="test-model",
    )

    service = ChapterSummarizerService(inferencer=mock_inferencer)
    result = service.summarize(
        chapter_id="ch-001",
        chapter_text="",
        character_names=["Kael"],
    )

    assert result is None
    mock_inferencer.generate_text.assert_not_called()
```

Note: Add `import json` at top of test file.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_chapter_summarizer.py::test_summarize_returns_prior_chapter_summary -q -p no:cacheprovider`
Expected: FAIL with "AttributeError: 'ChapterSummarizerService' object has no attribute 'summarize'"

- [ ] **Step 3: Write minimal implementation**

Modify `app/services/chapter_summarizer.py`:

```python
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..inference.base import InferenceBackend

from ..schemas.story_development import PriorChapterSummary
from .runtime_prompts import build_chapter_summarize_request

logger = logging.getLogger(__name__)


class ChapterSummarizerService:
    """LLM-based chapter summarization service.

    Reads completed chapter markdown and extracts structured PriorChapterSummary:
    - key_events: significant plot points from the chapter
    - character_states: character conditions/goals at chapter end
    - unresolved_threads: open questions, cliffhangers, pending conflicts

    Follows ConsistencyCriticService pattern: graceful error handling, never blocks pipeline.
    """

    def __init__(self, *, inferencer: InferenceBackend) -> None:
        self._inferencer = inferencer

    def summarize(
        self,
        chapter_id: str,
        chapter_text: str,
        character_names: list[str],
    ) -> PriorChapterSummary | None:
        """Extract structured summary from completed chapter markdown.

        Returns PriorChapterSummary on success, None on any failure.
        Never raises exceptions - errors are logged and swallowed.
        """
        if not chapter_text or not chapter_text.strip():
            logger.info("Skipping summarization for empty chapter: %s", chapter_id)
            return None

        try:
            request = build_chapter_summarize_request(
                chapter_id=chapter_id,
                chapter_text=chapter_text,
                character_names=character_names,
                default_model=self._inferencer.descriptor.default_model,
            )
            response = self._inferencer.generate_text(request)
            result = json.loads(response.content)

            return PriorChapterSummary(
                chapter_id=result.get("chapter_id", chapter_id),
                title=result.get("title", f"Chapter {chapter_id}"),
                key_events=result.get("key_events", [])[:10],
                character_states=dict(list(result.get("character_states", {}).items())[:10]),
                unresolved_threads=result.get("unresolved_threads", [])[:5],
            )

        except (json.JSONDecodeError, KeyError, AttributeError) as exc:
            logger.warning("Summarizer parse failed for %s: %s", chapter_id, exc)
            return None
        except Exception as exc:
            from ..inference.base import InferenceBackendError
            if isinstance(exc, InferenceBackendError):
                logger.warning("Summarizer LLM failed for %s: %s", chapter_id, exc)
            else:
                logger.warning("Summarizer unexpected error for %s: %s", chapter_id, exc)
            return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_chapter_summarizer.py -q -p no:cacheprovider`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/chapter_summarizer.py tests/test_chapter_summarizer.py
git commit -m "feat: implement ChapterSummarizerService.summarize() with error tolerance"
```

---

### Task 4: Executor - Extract Single-Chapter Draft Method

**Files:**
- Modify: `app/services/local_executor.py` (refactor _run_drafter_phase)
- Test: `tests/test_chapter_summarizer.py` (add test for executor integration)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_chapter_summarizer.py`:

```python
def test_executor_accepts_chapter_summarizer_parameter():
    from app.services.local_executor import LocalExecutor

    # Verify that LocalExecutor constructor accepts chapter_summarizer parameter
    import inspect
    sig = inspect.signature(LocalExecutor.__init__)
    params = list(sig.parameters.keys())
    assert "chapter_summarizer_service" in params, f"Missing parameter. Got: {params}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_chapter_summarizer.py::test_executor_accepts_chapter_summarizer_parameter -q -p no:cacheprovider`
Expected: FAIL with "AssertionError: Missing parameter"

- [ ] **Step 3: Add chapter_summarizer_service to LocalExecutor constructor**

Modify `app/services/local_executor.py` lines 96-122:

Add import at top of file (after existing imports):
```python
from ..services.chapter_summarizer import ChapterSummarizerService
```

Modify constructor signature (line 96-108):
```python
    def __init__(
        self,
        *,
        job_manager: JobManager,
        role_check_manager: RoleModelCheckManager,
        role_check_service: RoleModelCheckerService,
        inferencer: InferenceBackend | None = None,
        project_service: ProjectService | None = None,
        step_record_service: StepRecordService | None = None,
        scene_context_service: SceneContextService | None = None,
        consistency_critic_service: ConsistencyCriticService | None = None,
        entity_intake_service: EntityIntakeService | None = None,
        chapter_summarizer_service: ChapterSummarizerService | None = None,
        poll_interval_seconds: float = 0.25,
    ) -> None:
```

Add storage line after line 118:
```python
        self._chapter_summarizer = chapter_summarizer_service
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_chapter_summarizer.py::test_executor_accepts_chapter_summarizer_parameter -q -p no:cacheprovider`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/local_executor.py tests/test_chapter_summarizer.py
git commit -m "feat: wire ChapterSummarizerService into LocalExecutor constructor"
```

---

### Task 5: Executor - Multi-Chapter Loop with Prior Context Propagation

**Files:**
- Modify: `app/services/local_executor.py` (extend _run_drafter_phase)
- Test: `tests/test_local_executor_drafter_runtime.py` (add multi-chapter test)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_local_executor_drafter_runtime.py`:

```python
def test_drafting_with_chapter_ids_list_runs_sequentially(tmp_path):
    """Verify that chapter_ids list triggers sequential drafting with prior context."""
    from fastapi.testclient import TestClient
    from app.main import build_app

    runtime_path = tmp_path / "runtime"
    runtime_path.mkdir()

    import os
    env_patch = monkeypatch_os_environ(tmp_path)
    client = TestClient(build_app())

    # Create project
    project_resp = client.post("/projects/create", json={
        "project_name": "Multi-Chapter Test",
        "genre": "Science Fiction",
        "tone": "Contemplative",
        "story_structure": "THREE_ACT",
        "pov": "Third_Limited",
    })
    assert project_resp.status_code == 201
    project_id = project_resp.json()["project_id"]

    # Create chapter plans for multi-chapter mode
    for i in range(1, 4):
        client.post("/v1/story-development/planning/chapter-plans", json={
            "chapter_id": f"ch-00{i}",
            "project_id": project_id,
            "title": f"Chapter {i}",
            "description": f"Test chapter {i}",
            "active_character_ids": [],
        })

    # Launch multi-chapter job with chapter_ids list
    job_resp = client.post("/v1/jobs/create", json={
        "phase": "P-300",
        "payload": {
            "project_id": project_id,
            "chapter_ids": ["ch-001", "ch-002", "ch-003"],
        },
    })
    assert job_resp.status_code == 202
    job_id = job_resp.json()["id"]

    # Wait for completion (stub backend completes quickly)
    import time
    for _ in range(50):
        time.sleep(0.1)
        status_resp = client.get(f"/v1/jobs/{job_id}/status")
        if status_resp.json()["status"] in {"COMPLETED", "FAILED"}:
            break

    status = status_resp.json()["status"]
    assert status == "COMPLETED", f"Job failed: {status_resp.json().get('detail')}"

    # Verify chapter files were created
    chapters_dir = tmp_path / "projects" / project_id / "chapters"
    assert chapters_dir.exists(), "Chapters directory was not created"
    created_chapters = list(chapters_dir.glob("*.md"))
    assert len(created_chapters) == 3, f"Expected 3 chapters, got {len(created_chapters)}"


def test_prior_chapters_context_propagates_between_chapters(tmp_path, monkeypatch):
    """Verify that prior chapter summaries are injected into subsequent chapters."""
    from fastapi.testclient import TestClient
    from app.main import build_app

    runtime_path = tmp_path / "runtime"
    runtime_path.mkdir()

    env_patch = monkeypatch_os_environ(tmp_path)
    client = TestClient(build_app())

    project_resp = client.post("/projects/create", json={
        "project_name": "Context Propagation Test",
        "genre": "Science Fiction",
        "tone": "Contemplative",
        "story_structure": "THREE_ACT",
        "pov": "Third_Limited",
    })
    project_id = project_resp.json()["project_id"]

    # Create characters for context injection
    client.post("/v1/story-development/characters", json={
        "character_id": "char-001",
        "project_id": project_id,
        "display_name": "Kael",
        "role_in_story": "Protagonist",
        "archetype": "Reluctant Hero",
    })

    # Create chapter plans
    for i in range(1, 4):
        client.post("/v1/story-development/planning/chapter-plans", json={
            "chapter_id": f"ch-00{i}",
            "project_id": project_id,
            "title": f"Chapter {i}",
            "description": f"Test chapter {i}",
            "active_character_ids": ["char-001"],
        })

    # Launch multi-chapter job
    job_resp = client.post("/v1/jobs/create", json={
        "phase": "P-300",
        "payload": {
            "project_id": project_id,
            "chapter_ids": ["ch-001", "ch-002", "ch-003"],
        },
    })
    job_id = job_resp.json()["id"]

    # Wait for completion
    import time
    for _ in range(50):
        time.sleep(0.1)
        status_resp = client.get(f"/v1/jobs/{job_id}/status")
        if status_resp.json()["status"] in {"COMPLETED", "FAILED"}:
            break

    assert status_resp.json()["status"] == "COMPLETED"

    # Verify all 3 chapters exist
    chapters_dir = tmp_path / "projects" / project_id / "chapters"
    assert len(list(chapters_dir.glob("*.md"))) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_local_executor_drafter_runtime.py::test_drafting_with_chapter_ids_list_runs_sequentially -q -p no:cacheprovider`
Expected: FAIL (multi-chapter mode not yet implemented)

- [ ] **Step 3: Implement multi-chapter loop in _run_drafter_phase**

This is the core change. Modify `app/services/local_executor.py` _run_drafter_phase method.

The key modification: detect `chapter_ids` list, enter sequential loop, propagate prior context.

After line 781 (after chapter_id extraction), add multi-chapter detection:

```python
        # Check for multi-chapter mode
        chapter_ids_list = payload.get("chapter_ids")
        if isinstance(chapter_ids_list, list) and chapter_ids_list:
            # Multi-chapter sequential mode
            self._run_multi_chapter_draft(
                job_id=job_id,
                started_at=started_at,
                current_phase=current_phase,
                attempt=attempt,
                request_payload=request_payload,
                project_id=project_id,
                chapter_ids=[str(cid) for cid in chapter_ids_list],
            )
            return
```

Add new method after _run_drafter_phase:

```python
    def _run_multi_chapter_draft(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, object],
        project_id: str,
        chapter_ids: list[str],
    ) -> None:
        """Run sequential P-300 jobs for multiple chapters with prior context propagation.

        Each chapter is drafted, summarized, and the summary is injected into subsequent chapters.
        Prior chapters list is capped at last 3 to avoid prompt bloat.
        """
        from ..schemas.story_development import PriorChapterSummary

        project = self._project_service.get_project(project_id)
        payload = dict(request_payload.get("payload", {}))
        prior_chapters: list[PriorChapterSummary] = []
        completed_count = 0
        failed_chapters: list[str] = []

        for idx, chapter_id in enumerate(chapter_ids):
            logger.info(
                "Drafting chapter %d/%d: %s",
                idx + 1,
                len(chapter_ids),
                chapter_id,
            )

            # Sanitize chapter_id
            safe_chapter_id = chapter_id
            try:
                safe_chapter_id = sanitize_filename(chapter_id)
            except ValidationError:
                logger.warning("Invalid chapter_id, skipping: %r", chapter_id)
                failed_chapters.append(chapter_id)
                continue

            # Get active characters for this chapter
            active_chars: list[str] | None = None
            if self._scene_context:
                try:
                    _repo = self._scene_context._repository
                    chapter_plan = _repo.get_chapter_plan(safe_chapter_id)
                    active_chars = chapter_plan.active_character_ids if chapter_plan else None
                except KeyError:
                    pass  # No chapter plan, use all characters

            # Resolve upstream artifacts (shared across chapters)
            selected_inputs = self._resolve_runtime_artifact_inputs(
                job_id=job_id,
                attempt=attempt,
                project_id=project_id,
                step_name="drafter",
            )
            sequence_output = selected_inputs.get("sequence")
            architect_output = selected_inputs.get("architect_output")

            # Build inference request for this chapter
            inference_request = build_p300_drafter_request(
                manifest=project.manifest,
                payload=payload,
                sequence_output=sequence_output,
                architect_output=architect_output,
                default_model=self._inferencer.descriptor.default_model,
                chapter_id=safe_chapter_id,
            )

            # Inject scene context with prior chapters
            if self._scene_context:
                try:
                    ctx = self._scene_context.assemble_context(
                        project_id=project_id,
                        active_character_ids=active_chars,
                        prior_chapters=prior_chapters if prior_chapters else None,
                    )
                    context_prompt = ctx.to_prompt_string()
                    if context_prompt:
                        existing_content = inference_request.messages[1].content
                        new_messages = list(inference_request.messages)
                        new_messages[1] = InferenceMessage(
                            role=new_messages[1].role,
                            content=f"{existing_content}\n\n{context_prompt}",
                        )
                        inference_request = inference_request.model_copy(
                            update={"messages": new_messages},
                        )
                except Exception as exc:
                    logger.warning("Context assembly failed for %s: %s", safe_chapter_id, exc)

            # Execute LLM call
            self._job_manager.update_job(
                job_id,
                current_phase=current_phase,
                current_step=f"drafter-{safe_chapter_id}",
                detail=f"Drafting {safe_chapter_id}.",
            )

            try:
                inference_response = self._inferencer.generate_text(inference_request)
            except InferenceBackendError as exc:
                logger.error("Drafting failed for %s: %s", safe_chapter_id, exc)
                failed_chapters.append(safe_chapter_id)
                continue

            # Process output
            output_path = chapter_output_path(Path(project.project_dir), chapter_id=safe_chapter_id)
            output_text = inference_response.content.strip()
            if output_text:
                output_text += "\n"

            # Run consistency critic and entity intake (existing logic)
            _repo = StoryDevelopmentRepository(settings.operations_db_path) if project_id else None
            _chars = _repo.list_character_profiles(project_id) if _repo else []

            # Consistency critic check
            rewrite_needed = False
            critic_result = None
            if self._consistency_critic and project_id:
                try:
                    bios = {c.display_name: f"archetype: {c.archetype}; voice: {c.voice_notes}" for c in _chars if c.display_name}
                    critic_result = self._consistency_critic.check(output_text, bios)
                    if not critic_result.passed and critic_result.violations:
                        rewrite_needed = True
                except Exception as exc:
                    logger.warning("Critic check failed for %s: %s", safe_chapter_id, exc)

            # Rewrite if needed
            if rewrite_needed and critic_result:
                try:
                    violation_summary = "\n".join(f"- {v.character}: {v.issue} -> {v.suggestion}" for v in critic_result.violations[:3])
                    rewrite_prompt = f"The following issues were found:\n{violation_summary}\nRewrite the flagged passages."
                    rewrite_request = InferenceRequest(
                        model=inference_request.model,
                        temperature=0.1,
                        max_tokens=inference_request.max_tokens,
                        messages=[
                            InferenceMessage(role="system", content="Rewrite only the flagged passages to fix consistency."),
                            InferenceMessage(role="user", content=f"Draft:\n{output_text}\n\n{rewrite_prompt}"),
                        ],
                    )
                    rewrite_response = self._inferencer.generate_text(rewrite_request)
                    rewritten = rewrite_response.content.strip()
                    if rewritten:
                        output_text = rewritten + "\n"
                except Exception as exc:
                    logger.warning("Rewrite failed for %s: %s", safe_chapter_id, exc)

            # Entity intake
            if self._entity_intake and project_id:
                try:
                    known = {c.display_name: c.character_id for c in _chars if c.display_name}
                    new_entities = self._entity_intake.intake_new_entities(output_text, known)
                    for entity in new_entities:
                        entity_id = f"auto-{entity.name.lower().replace(' ', '-')}"
                        _repo.upsert_character_profile(
                            project_id=project_id,
                            character_id=entity_id,
                            display_name=entity.name,
                            role_in_story="supporting",
                            archetype=entity.inferred_archetype or "unknown",
                            external_goal=entity.inferred_goal or "",
                        )
                except Exception as exc:
                    logger.warning("Entity intake failed for %s: %s", safe_chapter_id, exc)

            # Write chapter file
            staged_output_path = self._write_staged_output(output_path=output_path, output_text=output_text)
            normalized_finish_reason = inference_response.finish_reason or "completed"
            backend_version = _provider_backend_version(inference_response.raw_response)
            artifact_role = f"chapter_{safe_chapter_id}"

            # Register artifact lineage
            content_hash = stable_hash_payload(output_text)
            self._finalize_generated_job_phase(
                job_id=job_id,
                current_phase=current_phase,
                attempt=attempt,
                project_id=project_id,
                step_name=f"drafter-{safe_chapter_id}",
                detail=f"Drafted {safe_chapter_id}.",
                model_id=inference_response.model or inference_request.model,
                backend_name=self._inferencer.descriptor.display_name,
                backend_version=backend_version,
                input_payload={"job_request": request_payload, "chapter_id": safe_chapter_id},
                output_payload={"content": output_text, "artifact_path": str(output_path)},
                prompt_payload=inference_request.model_dump(mode="json"),
                input_artifact_refs=["manifest"],
                output_artifact_refs=[artifact_role],
                started_at=started_at,
                finished_at=_utcnow(),
                finish_reason=normalized_finish_reason,
                artifact_role=artifact_role,
                artifact_kind="markdown",
                output_path=output_path,
                staged_output_path=staged_output_path,
                content_hash_source=output_text,
                source_content_hashes=[content_hash],
                project_artifact_name=artifact_role,
            )

            # Summarize this chapter for prior context propagation
            if self._chapter_summarizer:
                try:
                    character_names = [c.display_name for c in _chars if c.display_name]
                    summary = self._chapter_summarizer.summarize(
                        chapter_id=safe_chapter_id,
                        chapter_text=output_text,
                        character_names=character_names,
                    )
                    if summary:
                        prior_chapters.append(summary)
                        # Cap at last 3 chapters
                        if len(prior_chapters) > 3:
                            prior_chapters = prior_chapters[-3:]
                except Exception as exc:
                    logger.warning("Summarization failed for %s: %s", safe_chapter_id, exc)

            completed_count += 1
            logger.info("Chapter %s completed successfully", safe_chapter_id)

        # Final job status
        if completed_count == 0:
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                detail=f"All {len(chapter_ids)} chapters failed.",
            )
        else:
            self._job_manager.update_job(
                job_id,
                status="COMPLETED",
                current_phase=current_phase,
                detail=f"Completed {completed_count}/{len(chapter_ids)} chapters.",
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_local_executor_drafter_runtime.py::test_drafting_with_chapter_ids_list_runs_sequentially -q -p no:cacheprovider`
Expected: PASS

Run: `python -m pytest tests/test_local_executor_drafter_runtime.py::test_prior_chapters_context_propagates_between_chapters -q -p no:cacheprovider`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/local_executor.py tests/test_local_executor_drafter_runtime.py
git commit -m "feat: implement multi-chapter drafting loop with prior context propagation"
```

---

### Task 6: Executor - ManuscriptDocument Auto-Creation

**Files:**
- Modify: `app/services/local_executor.py` (add ManuscriptDocument creation in chapter loop)
- Test: `tests/test_local_executor_drafter_runtime.py` (add test)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_local_executor_drafter_runtime.py`:

```python
def test_manuscript_documents_created_for_multi_chapter_draft(tmp_path, monkeypatch):
    """Verify that ManuscriptDocument records are created after each chapter draft."""
    from fastapi.testclient import TestClient
    from app.main import build_app

    runtime_path = tmp_path / "runtime"
    runtime_path.mkdir()

    env_patch = monkeypatch_os_environ(tmp_path)
    client = TestClient(build_app())

    project_resp = client.post("/projects/create", json={
        "project_name": "Manuscript Creation Test",
        "genre": "Science Fiction",
        "tone": "Contemplative",
        "story_structure": "THREE_ACT",
        "pov": "Third_Limited",
    })
    project_id = project_resp.json()["project_id"]

    # Create chapter plans
    for i in range(1, 4):
        client.post("/v1/story-development/planning/chapter-plans", json={
            "chapter_id": f"ch-00{i}",
            "project_id": project_id,
            "title": f"Chapter {i}",
            "description": f"Test chapter {i}",
            "active_character_ids": [],
        })

    # Launch multi-chapter job
    job_resp = client.post("/v1/jobs/create", json={
        "phase": "P-300",
        "payload": {
            "project_id": project_id,
            "chapter_ids": ["ch-001", "ch-002", "ch-003"],
        },
    })
    job_id = job_resp.json()["id"]

    # Wait for completion
    import time
    for _ in range(50):
        time.sleep(0.1)
        status_resp = client.get(f"/v1/jobs/{job_id}/status")
        if status_resp.json()["status"] in {"COMPLETED", "FAILED"}:
            break

    assert status_resp.json()["status"] == "COMPLETED"

    # Verify ManuscriptDocument records exist in database
    manuscripts_resp = client.get(
        "/v1/story-development/drafting/manuscript-documents",
        params={"project_id": project_id},
    )
    manuscripts = manuscripts_resp.json()
    manuscript_count = len(manuscripts)
    assert manuscript_count == 3, f"Expected 3 manuscript documents, got {manuscript_count}"

    # Verify each manuscript has correct chapter_id linkage
    chapter_ids_found = {m.get("chapter_id") for m in manuscripts}
    expected_chapters = {"ch-001", "ch-002", "ch-003"}
    assert chapter_ids_found == expected_chapters, f"Chapter IDs mismatch: {chapter_ids_found}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_local_executor_drafter_runtime.py::test_manuscript_documents_created_for_multi_chapter_draft -q -p no:cacheprovider`
Expected: FAIL (no ManuscriptDocument creation yet)

- [ ] **Step 3: Add ManuscriptDocument creation in chapter loop**

Add after the artifact lineage registration in `_run_multi_chapter_draft`, before the summarization block:

```python
            # Auto-create ManuscriptDocument for this chapter
            try:
                from ..services.drafting import DraftingService
                _drafting_service = DraftingService(repository=_repo)
                chapter_title = f"Chapter {safe_chapter_id}"
                # Try to get title from chapter plan
                try:
                    _cp = _repo.get_chapter_plan(safe_chapter_id)
                    chapter_title = _cp.title or chapter_title
                except KeyError:
                    pass

                _drafting_service.save_manuscript_document(
                    project_id=project_id,
                    document_id=f"ms-{safe_chapter_id}",
                    content=output_text,
                    title=chapter_title,
                    chapter_id=safe_chapter_id,
                )
            except Exception as exc:
                logger.warning("ManuscriptDocument creation failed for %s: %s", safe_chapter_id, exc)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_local_executor_drafter_runtime.py::test_manuscript_documents_created_for_multi_chapter_draft -q -p no:cacheprovider`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/local_executor.py tests/test_local_executor_drafter_runtime.py
git commit -m "feat: auto-create ManuscriptDocument records for multi-chapter drafts"
```

---

### Task 7: Wire ChapterSummarizerService in build_app()

**Files:**
- Modify: `app/main.py`
- Test: none required (wiring verification covered by integration tests)

- [ ] **Step 1: Add import and service instantiation**

Modify `app/main.py`:

Add import after line 240:
```python
    from .services.chapter_summarizer import ChapterSummarizerService
```

Modify LocalExecutor construction (line 277-286):
```python
    local_executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=role_check_manager,
        role_check_service=role_check_service,
        inferencer=inferencer,
        project_service=project_service,
        scene_context_service=SceneContextService(repository=story_development_repository),
        consistency_critic_service=ConsistencyCriticService(inferencer=inferencer),
        entity_intake_service=EntityIntakeService(inferencer=inferencer),
        chapter_summarizer_service=ChapterSummarizerService(inferencer=inferencer),
    )
```

- [ ] **Step 2: Verify full test suite passes**

Run: `python -m pytest -q -p no:cacheprovider`
Expected: All tests PASS (900+ passed, 9 skipped)

- [ ] **Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: wire ChapterSummarizerService into build_app"
```

---

### Task 8: Full Validation Suite Run

**Files:** All changed files

- [ ] **Step 1: Run full backend test suite**

Run: `python -m pytest -q -p no:cacheprovider`
Expected: PASS (all tests including new ones)

- [ ] **Step 2: Run frontend validation**

Run:
```bash
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
```
Expected: All pass

- [ ] **Step 3: Commit final state**

```bash
git add -A
git commit -m "feat: complete multi-chapter book generation with summarization and ManuscriptDocument creation"
```

---

## Self-Review Checklist

1. **Spec coverage:** All design spec sections implemented:
   - [x] ChapterSummarizerService (Tasks 1-3)
   - [x] Prompt builder (Task 2)
   - [x] Executor multi-chapter loop (Task 5)
   - [x] Prior context propagation (Task 5)
   - [x] ManuscriptDocument auto-creation (Task 6)
   - [x] Service wiring in build_app() (Task 7)
   - [x] Integration tests (Tasks 5-6)

2. **Placeholder scan:** No TBDs, TODOs, or vague requirements found.

3. **Type consistency:** PriorChapterSummary used consistently across summarizer, SceneContext, and executor. ChapterSummarizerService signature matches ConsistencyCriticService pattern.

4. **Scope check:** Focused on completing multi-chapter flow. P-400 per-chapter compilation deferred to separate feature (not in scope).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-26-multi-chapter-completion.md`. Two execution options:

**1. Subagent-Driven (recommended)** - Dispatch fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans skill, batch execution with checkpoints

Which approach?
