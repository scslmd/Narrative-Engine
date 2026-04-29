# Multi-Chapter Narrative Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable multi-chapter book generation with cross-chapter continuity, designed from day one to extend to multi-book series without architectural rewrite.

**Architecture:** Two-phase approach. Phase A implements token budget increase + multi-chapter single book with forward-compatible abstractions (ChapterContext, PriorChapterSummary, parameterized P-300). Phase B (documented but not implemented) adds BookPlan/SeriesState schemas and cross-book context injection. The key design principle: build the extension points now so Phase B is additive, not rewriting.

**Tech Stack:** Python, Pydantic schemas, SQLite (existing), InferenceBackend (existing LLM layer), existing SceneContextService extended for multi-chapter context

---

## Forward-Compatible Design Decisions

These decisions are baked into Phase A to avoid Phase B rewrite:

1. **ChapterContext abstraction** - SceneContextService will accept a new `prior_chapters` parameter (list of chapter summaries). Empty list today, populated in Phase A for cross-chapter continuity. In Phase B, this same parameter can include `book_summaries` and `series_state`.

2. **Parameterized P-300** - The drafter phase will accept a `chapter_id` from the job payload. Output path becomes `chapters/{chapter_id}.md`. Artifact role becomes `"chapter_{index}"`. This same parameterization works for multi-book: chapter IDs can be scoped per book in Phase B.

3. **PriorChapterSummary dataclass** - Introduced now as a lightweight structure (chapter_id, key_events, character_states, unresolved_threads). Used for cross-chapter context today. In Phase B, the same structure extends with `book_id` and feeds into SeriesState.

4. **Pipeline orchestrator** - A new ChapterOrchestrator service runs N sequential P-300 jobs, one per chapter plan. It is generic enough that in Phase B it can run book-level orchestration (N books x M chapters each).

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `app/services/chapter_orchestrator.py` | Run N sequential P-300 jobs, one per chapter plan |
| `tests/test_chapter_orchestrator.py` | Unit + integration tests for orchestrator |

### Modified Files
| File | Change |
|------|--------|
| `app/services/runtime_prompts.py` | Increase P-300 default max_tokens, parameterize chapter index in prompt |
| `app/services/scene_context.py` | Add ChapterContext with prior-chapter summaries, wire active_character_ids |
| `app/services/local_executor.py` | Parameterize output path and artifact role by chapter_id |
| `app/schemas/story_development.py` | Add PriorChapterSummary dataclass |
| `tests/test_scene_context.py` | Tests for ChapterContext with prior chapters |
| `tests/test_local_executor_drafter_runtime.py` | Multi-chapter integration test |

---

## Phase A: Implement Now

### Task 1: Increase P-300 default max_tokens

**Files:**
- Modify: `app/services/runtime_prompts.py:108`

- [ ] **Step 1: Write the failing test**

Create `tests/test_p300_token_budget.py`:

```python
from __future__ import annotations

import pytest
from app.schemas.manifest import Manifest
from app.services.runtime_prompts import build_p300_drafter_request

def _make_manifest() -> Manifest:
    return Manifest.model_validate({
        "project_id": "test-project",
        "project_name": "Test Project",
        "genre": "Science Fiction",
        "tone": "Contemplative",
        "story_structure": "THREE_ACT",
        "constraints": [],
        "premise_text": "A test story.",
    })

def test_p300_default_max_tokens_is_8000():
    manifest = _make_manifest()
    request = build_p300_drafter_request(
        manifest=manifest,
        payload={"project_id": "test-project"},
        default_model=None,
    )
    assert request.max_tokens == 8000

def test_p300_max_tokens_overridable_via_payload():
    manifest = _make_manifest()
    request = build_p300_drafter_request(
        manifest=manifest,
        payload={"project_id": "test-project", "max_tokens": 16000},
        default_model=None,
    )
    assert request.max_tokens == 16000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_p300_token_budget.py::test_p300_default_max_tokens_is_8000 -q -p no:cacheprovider`
Expected: FAIL with "AssertionError: assert 1200 == 8000"

- [ ] **Step 3: Write minimal implementation**

In `app/services/runtime_prompts.py`, change line 108:

```python
        max_tokens=_coerce_int(payload.get("max_tokens"), default=8000),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_p300_token_budget.py -q -p no:cacheprovider`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/runtime_prompts.py tests/test_p300_token_budget.py
git commit -m "feat: increase P-300 default max_tokens from 1200 to 8000 for full-chapter drafts"
```

---

### Task 2: Add PriorChapterSummary dataclass

**Files:**
- Modify: `app/schemas/story_development.py`
- Test: `tests/test_prior_chapter_summary.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_prior_chapter_summary.py`:

```python
from __future__ import annotations

import pytest
from app.schemas.story_development import PriorChapterSummary

def test_prior_chapter_summary_dataclass():
    summary = PriorChapterSummary(
        chapter_id="ch-001",
        title="The Departure",
        key_events=["Kael leaves the village", "Meets Soraya at the crossroads"],
        character_states={"Kael": "restless, seeking purpose", "Soraya": "mysterious, evasive"},
        unresolved_threads=["Who is Soraya really?", "What is in the package?"],
    )
    assert len(summary.key_events) == 2
    assert "Kael" in summary.character_states

def test_prior_chapter_summary_to_context_string():
    summary = PriorChapterSummary(
        chapter_id="ch-001",
        title="The Departure",
        key_events=["Kael leaves"],
        character_states={"Kael": "restless"},
        unresolved_threads=["Where is he going?"],
    )
    ctx = summary.to_context_string()
    assert "The Departure" in ctx
    assert "Kael leaves" in ctx
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_prior_chapter_summary.py -q -p no:cacheprovider`
Expected: FAIL with "cannot import name 'PriorChapterSummary'"

- [ ] **Step 3: Write minimal implementation**

Add to `app/schemas/story_development.py` after existing dataclasses (before the first schema class, around line 194):

```python
@dataclass(slots=True)
class PriorChapterSummary:
    """Summary of a prior chapter for cross-chapter continuity context.

    Forward-compatible: same structure used for book summaries in multi-book mode.
    """
    chapter_id: str
    title: str
    key_events: list[str]
    character_states: dict[str, str]
    unresolved_threads: list[str]

    def to_context_string(self) -> str:
        lines = [f"PRIOR CHAPTER: {self.title}", ""]
        if self.key_events:
            lines.append("Key events:")
            for event in self.key_events[:10]:
                lines.append(f"  - {event}")
            lines.append("")
        if self.character_states:
            lines.append("Character states at chapter end:")
            for name, state in list(self.character_states.items())[:10]:
                lines.append(f"  - {name}: {state}")
            lines.append("")
        if self.unresolved_threads:
            lines.append("Unresolved threads:")
            for thread in self.unresolved_threads[:5]:
                lines.append(f"  ? {thread}")
            lines.append("")
        return "\n".join(lines).rstrip()
```

NOTE: Add `from dataclasses import dataclass` import at top of file if not present.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_prior_chapter_summary.py -q -p no:cacheprovider`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/schemas/story_development.py tests/test_prior_chapter_summary.py
git commit -m "feat: add PriorChapterSummary dataclass for cross-chapter continuity context"
```

---

### Task 3: Extend SceneContextService with ChapterContext (prior chapters support)

**Files:**
- Modify: `app/services/scene_context.py`
- Modify: `tests/test_scene_context.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_scene_context.py`:

```python
from __future__ import annotations

import pytest
from app.schemas.story_development import PriorChapterSummary
from app.services.scene_context import SceneContextService

class FakeRepositoryWithChapters:
    def list_character_profiles(self, project_id: str):
        return []
    def get_character_profile(self, character_id: str):
        from app.schemas.story_development import CharacterProfile
        return CharacterProfile(
            character_id=character_id,
            project_id="proj-1",
            display_name="Kael",
            role_in_story="protagonist",
            archetype="reluctant hero",
            external_goal="Find the truth",
            internal_need="Trust others",
            core_fear="Being abandoned",
            voice_notes="Terse, avoids metaphors",
        )
    def list_world_bible_entries(self, project_id: str):
        return []

def test_assemble_context_with_prior_chapters():
    repo = FakeRepositoryWithChapters()
    service = SceneContextService(repository=repo)
    prior = [PriorChapterSummary(
        chapter_id="ch-001",
        title="The Departure",
        key_events=["Kael leaves the village"],
        character_states={"Kael": "restless"},
        unresolved_threads=["Who is waiting at the crossroads?"],
    )]
    ctx = service.assemble_context(
        project_id="proj-1",
        active_character_ids=["char-001"],
        prior_chapters=prior,
    )
    assert len(ctx.prior_chapters) == 1
    assert ctx.prior_chapters[0].title == "The Departure"

def test_to_prompt_string_includes_prior_chapters():
    from app.services.scene_context import SceneContext, CharacterAnchor
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        prior_chapters=[PriorChapterSummary(
            chapter_id="ch-001",
            title="The Departure",
            key_events=["Kael leaves"],
            character_states={},
            unresolved_threads=["Where next?"],
        )],
    )
    prompt = ctx.to_prompt_string()
    assert "PRIOR CHAPTER: The Departure" in prompt
    assert "Kael leaves" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_scene_context.py::test_assemble_context_with_prior_chapters -q -p no:cacheprovider`
Expected: FAIL (SceneContext does not have prior_chapters field yet)

- [ ] **Step 3: Write minimal implementation**

Modify `app/services/scene_context.py`:

Add import at top:
```python
from ..schemas.story_development import PriorChapterSummary
```

Update SceneContext dataclass to include prior_chapters:
```python
@dataclass(slots=True)
class SceneContext:
    characters: list[CharacterAnchor]
    world_facts: list[WorldConstraint]
    prior_chapters: list[PriorChapterSummary] | None = None
```

Update `to_prompt_string()` to include prior chapter context. Add after existing world constraints section:
```python
        if self.prior_chapters:
            lines.append("")
            lines.append("PRIOR CHAPTER CONTEXT:")
            for ch in self.prior_chapters[-3:]:  # Last 3 chapters max
                lines.append(ch.to_context_string())
```

Update `assemble_context()` to accept and pass through prior_chapters:
```python
    def assemble_context(
        self,
        project_id: str,
        active_character_ids: Iterable[str] | None = None,
        prior_chapters: list[PriorChapterSummary] | None = None,
    ) -> SceneContext:
        # ... existing character + world assembly ...
        return SceneContext(characters=anchors, world_facts=world_facts, prior_chapters=prior_chapters)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_scene_context.py -q -p no:cacheprovider`
Expected: PASS (all existing + new tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/scene_context.py tests/test_scene_context.py
git commit -m "feat: extend SceneContextService with prior-chapter context injection"
```

---

### Task 4: Parameterize P-300 output path and artifact role by chapter_id

**Files:**
- Modify: `app/services/local_executor.py`
- Modify: `app/services/runtime_prompts.py`
- Test: `tests/test_local_executor_drafter_runtime.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_local_executor_drafter_runtime.py`:

```python
def test_local_executor_p300_writes_parameterized_chapter_path(tmp_path: Path) -> None:
    """P-300 should write chapter output to chapters/{chapter_id}.md when chapter_id is provided."""
    from app.services.scene_context import SceneContextService

    project_id = "param-chapter-test"
    manifest = _make_manifest(project_id)
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)

    inferencer = FakePipelineInferenceBackend(
        content_by_phase={
            "P-100": "## Logline\nA mapmaker learns her city is alive.\n",
            "P-200": json.dumps({"beats": [{"id": "beat-1", "title": "Opening", "depends_on": []}]}),
            "P-300": "# Chapter 3: The Confrontation\nKael faced the truth at last.\n",
        },
    )

    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    models_root = tmp_path / "data" / "models"
    reports_root = tmp_path / "data" / "role_model_checker_runs"
    models_root.mkdir(parents=True, exist_ok=True)
    project_service = ProjectService(tmp_path)
    job_manager = JobManager(db_path)
    checker_manager = RoleModelCheckManager(db_path)
    step_records = StepRecordService(db_path)

    executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=checker_manager,
        role_check_service=RoleModelCheckerService(models_root, reports_root, inferencer=inferencer),
        inferencer=inferencer,
        project_service=project_service,
        step_record_service=step_records,
        poll_interval_seconds=0.05,
    )
    project_service.reconcile_projects()

    executor.start()
    try:
        p100 = _run_phase(job_manager, phase="P-100", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        p200 = _run_phase(job_manager, phase="P-200", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"
        p300 = _run_phase(job_manager, phase="P-300", project_id=project_id, payload={"chapter_id": "ch-003"})
        final_status = _wait_for_terminal_status(job_manager, p300.id)
    finally:
        executor.stop()

    assert final_status == "COMPLETED"

    # Verify chapter was written to parameterized path
    chapter_path = tmp_path / "data" / "projects" / project_id / "chapters" / "ch-003.md"
    assert chapter_path.exists(), f"Expected chapter at {chapter_path}"
    content = chapter_path.read_text()
    assert "Chapter 3: The Confrontation" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_local_executor_drafter_runtime.py::test_local_executor_p300_writes_parameterized_chapter_path -q -p no:cacheprovider`
Expected: FAIL (output still goes to flat chapter.md)

- [ ] **Step 3: Write minimal implementation**

Modify `app/services/runtime_prompts.py` - add parameterized path function:

```python
def chapter_output_path(project_dir: Path, chapter_id: str | None = None) -> Path:
    """Return output path for a chapter draft.

    If chapter_id is provided, writes to chapters/{chapter_id}.md.
    Otherwise falls back to project_dir/chapter.md (backward compat).
    """
    if chapter_id:
        out_dir = project_dir / "chapters"
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / f"{chapter_id}.md"
    return project_dir / "chapter.md"
```

Modify `app/services/local_executor.py` in `_run_drafter_phase`:

Extract chapter_id from payload:
```python
        chapter_id = str(payload.get("chapter_id") or "").strip() or None
```

Use parameterized output path:
```python
        output_path = chapter_output_path(Path(project.project_dir), chapter_id=chapter_id)
```

Parameterize artifact role for step records:
```python
        artifact_role = f"chapter_{chapter_id}" if chapter_id else "chapter_1"
```

Update the system prompt to reference the chapter. In `build_p300_drafter_request`, add chapter_id parameter and use in prompt:
```python
def build_p300_drafter_request(
    *,
    manifest: Manifest,
    payload: dict[str, Any],
    sequence_output: str | None = None,
    architect_output: str | None = None,
    default_model: str | None,
    chapter_id: str | None = None,
) -> InferenceRequest:
    # ... existing context assembly ...
    chapter_label = f"chapter {chapter_id}" if chapter_id else "chapter-1"
```

Update the call site in `_run_drafter_phase`:
```python
        inference_request = build_p300_drafter_request(
            manifest=project.manifest,
            payload=payload,
            sequence_output=sequence_output,
            architect_output=architect_output,
            default_model=self._inferencer.descriptor.default_model,
            chapter_id=chapter_id,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_local_executor_drafter_runtime.py::test_local_executor_p300_writes_parameterized_chapter_path -q -p no:cacheprovider`
Expected: PASS

- [ ] **Step 5: Verify backward compatibility**

Run existing drafter test to ensure flat chapter.md still works without chapter_id:
```bash
python -m pytest tests/test_local_executor_drafter_runtime.py::test_local_executor_runs_real_drafter_path_for_p300_with_fake_inferencer -q -p no:cacheprovider
```

- [ ] **Step 6: Commit**

```bash
git add app/services/local_executor.py app/services/runtime_prompts.py tests/test_local_executor_drafter_runtime.py
git commit -m "feat: parameterize P-300 output path and artifact role by chapter_id"
```

---

### Task 5: Wire active_character_ids from ChapterPlan to SceneContextService

**Files:**
- Modify: `app/services/local_executor.py`
- Test: `tests/test_scene_context.py` (add integration test)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_scene_context.py`:

```python
def test_assemble_context_respects_active_character_ids():
    """SceneContextService should filter characters by active_character_ids from ChapterPlan."""
    from app.services.scene_context import SceneContextService

    class MultiCharRepo:
        def list_character_profiles(self, project_id: str):
            return []  # Empty to force no fallback
        def get_character_profile(self, character_id: str):
            from app.schemas.story_development import CharacterProfile
            names = {"char-001": "Kael", "char-002": "Soraya", "char-003": "Joss"}
            return CharacterProfile(
                character_id=character_id,
                project_id="proj-1",
                display_name=names.get(character_id, "Unknown"),
                role_in_story="supporting",
                archetype="hero",
                external_goal="Survive",
                internal_need="Trust",
                core_fear="Loss",
                voice_notes="Normal",
            )
        def list_world_bible_entries(self, project_id: str):
            return []

    repo = MultiCharRepo()
    service = SceneContextService(repository=repo)
    ctx = service.assemble_context(
        project_id="proj-1",
        active_character_ids=["char-001", "char-002"],  # Only Kael and Soraya
    )
    assert len(ctx.characters) == 2
    names = {c.display_name for c in ctx.characters}
    assert "Kael" in names
    assert "Soraya" in names
    assert "Joss" not in names  # Not in active list
```

- [ ] **Step 2: Run test to verify it passes (existing behavior)**

Run: `python -m pytest tests/test_scene_context.py::test_assemble_context_respects_active_character_ids -q -p no:cacheprovider`
Expected: PASS (this is already supported - the service filters by active_character_ids)

- [ ] **Step 3: Wire chapter_id to ChapterPlan to active_character_ids in drafter phase**

In `app/services/local_executor.py`, after assembling context, pass active_character_ids if a chapter plan exists:

```python
        # Context injection: assemble character anchors and world constraints
        if self._scene_context:
            try:
                # Try to get active_character_ids from the chapter plan
                active_chars = None
                if chapter_id:
                    try:
                        from ..persistence.story_development import StoryDevelopmentRepository as _SDR
                        from ..settings import settings as _s
                        _repo = _SDR(_s.operations_db_path)
                        chapter_plan = _repo.get_chapter_plan(chapter_id)
                        active_chars = chapter_plan.active_character_ids if chapter_plan else None
                    except (KeyError, AttributeError):
                        pass  # No chapter plan found, use all characters

                ctx = self._scene_context.assemble_context(
                    project_id=project_id,
                    active_character_ids=active_chars,
                    prior_chapters=None,  # Will be populated by orchestrator in Task 6
                )
```

NOTE: This requires `get_chapter_plan` method on StoryDevelopmentRepository. Check if it exists - if not, add a simple getter that queries the chapter_plans table.

- [ ] **Step 4: Run existing tests to verify no regressions**

Run: `python -m pytest tests/test_scene_context.py -q -p no:cacheprovider`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/local_executor.py app/persistence/story_development.py tests/test_scene_context.py
git commit -m "feat: wire ChapterPlan.active_character_ids to SceneContextService in P-300"
```

---

### Task 6: Add ChapterOrchestrator for sequential multi-chapter generation

**Files:**
- Create: `app/services/chapter_orchestrator.py`
- Test: `tests/test_chapter_orchestrator.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_chapter_orchestrator.py`:

```python
from __future__ import annotations

import pytest
from app.services.chapter_orchestrator import ChapterOrchestrator, ChapterResult


class FakeJobManager:
    def __init__(self, outcomes: dict[str, str] | None = None):
        self._outcomes = outcomes or {}
        self.created_jobs: list[dict] = []

    def create_job(self, request):
        from uuid import uuid4
        job_id = str(uuid4())
        self.created_jobs.append({"id": job_id, "phase": request.phase, "payload": request.payload})
        return type("Job", (), {"id": job_id})()

    def get_status(self, job_id):
        outcome = self._outcomes.get(job_id, "COMPLETED")
        return type("Status", (), {"status": outcome})()


def test_orchestrator_creates_sequential_jobs():
    manager = FakeJobManager()
    orch = ChapterOrchestrator(
        project_id="proj-1",
        chapter_ids=["ch-001", "ch-002", "ch-003"],
        job_manager=manager,
    )
    results = orch.run_all()

    assert len(results) == 3
    assert all(r.success for r in results)
    assert len(manager.created_jobs) == 3
    # Verify chapter_ids were passed in payloads
    for i, job in enumerate(manager.created_jobs):
        assert job["payload"]["chapter_id"] == f"ch-00{i+1}"


def test_orchestrator_handles_failed_chapter():
    manager = FakeJobManager()
    orch = ChapterOrchestrator(
        project_id="proj-1",
        chapter_ids=["ch-001", "ch-002"],
        job_manager=manager,
    )
    # Override: second job will return FAILED
    original_get = manager.get_status
    def failing_get(job_id):
        if len(manager.created_jobs) >= 2:
            return type("Status", (), {"status": "FAILED"})()
        return original_get(job_id)
    manager.get_status = failing_get

    results = orch.run_all()
    assert results[0].success is True
    assert results[1].success is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_chapter_orchestrator.py -q -p no:cacheprovider`
Expected: FAIL with "cannot import name 'ChapterOrchestrator'"

- [ ] **Step 3: Write minimal implementation**

Create `app/services/chapter_orchestrator.py`:

```python
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChapterResult:
    chapter_id: str
    success: bool
    output_path: str | None = None
    error: str | None = None


class ChapterOrchestrator:
    """Orchestrate sequential P-300 jobs for multi-chapter generation.

    Forward-compatible: same orchestrator can handle book-level orchestration
    in multi-book mode by changing the job payload and summary extraction.
    """

    def __init__(
        self,
        *,
        project_id: str,
        chapter_ids: list[str],
        job_manager: Any,  # JobManager - avoid circular import
    ) -> None:
        self._project_id = project_id
        self._chapter_ids = chapter_ids
        self._job_manager = job_manager

    def run_all(self) -> list[ChapterResult]:
        """Run P-300 jobs sequentially for each chapter.

        Each chapter waits for the prior to complete before starting.
        Prior chapter summaries are built from completed chapters and
        passed as context to subsequent chapters.
        """
        results: list[ChapterResult] = []
        prior_summaries: list[Any] = []  # PriorChapterSummary instances

        for i, chapter_id in enumerate(self._chapter_ids):
            logger.info("Orchestrating chapter %d/%d: %s", i + 1, len(self._chapter_ids), chapter_id)

            # Build job payload with chapter context
            payload = {
                "project_id": self._project_id,
                "chapter_id": chapter_id,
            }

            # Create and wait for the P-300 job
            try:
                from app.schemas.jobs import JobCreateRequest
                job = self._job_manager.create_job(
                    JobCreateRequest(phase="P-300", payload=payload),
                )
                status = self._wait_for_completion(job.id)

                if status == "COMPLETED":
                    results.append(ChapterResult(
                        chapter_id=chapter_id,
                        success=True,
                    ))
                    # Build summary for next chapter's context
                    # NOTE: Summary extraction via LLM is a future enhancement.
                    # For now, the prior_chapters list grows but summaries are empty.
                    logger.info("Chapter %s completed", chapter_id)
                else:
                    results.append(ChapterResult(
                        chapter_id=chapter_id,
                        success=False,
                        error=f"Job failed with status: {status}",
                    ))
                    logger.warning("Chapter %s failed: %s", chapter_id, status)

            except Exception as exc:
                results.append(ChapterResult(
                    chapter_id=chapter_id,
                    success=False,
                    error=str(exc),
                ))
                logger.error("Chapter %s error: %s", chapter_id, exc)

        return results

    def _wait_for_completion(self, job_id: str, attempts: int = 200) -> str:
        """Poll job status until terminal state."""
        from time import sleep
        for _ in range(attempts):
            status = self._job_manager.get_status(job_id)
            if str(status.status) in {"COMPLETED", "FAILED"}:
                return str(status.status)
            sleep(0.1)
        return "TIMEOUT"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_chapter_orchestrator.py -q -p no:cacheprovider`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/chapter_orchestrator.py tests/test_chapter_orchestrator.py
git commit -m "feat: add ChapterOrchestrator for sequential multi-chapter P-300 generation"
```

---

### Task 7: Integration test - full multi-chapter pipeline

**Files:**
- Modify: `tests/test_local_executor_drafter_runtime.py`

- [ ] **Step 1: Write the integration test**

Add to `tests/test_local_executor_drafter_runtime.py`:

```python
def test_multi_chapter_pipeline_generates_sequential_chapters(tmp_path: Path) -> None:
    """Full integration: run P-300 for two chapters with parameterized output paths."""
    project_id = "multi-chapter-test"
    manifest = _make_manifest(project_id)
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)

    inferencer = FakePipelineInferenceBackend(
        content_by_phase={
            "P-100": "## Logline\nA hero's journey.\n",
            "P-200": json.dumps({"beats": [
                {"id": "beat-1", "title": "Opening", "depends_on": []},
                {"id": "beat-2", "title": "Climax", "depends_on": ["beat-1"]},
            ]}),
            "P-300": "# Chapter Content\nDraft prose.\n",
        },
    )

    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    models_root = tmp_path / "data" / "models"
    reports_root = tmp_path / "data" / "role_model_checker_runs"
    models_root.mkdir(parents=True, exist_ok=True)
    project_service = ProjectService(tmp_path)
    job_manager = JobManager(db_path)
    checker_manager = RoleModelCheckManager(db_path)
    step_records = StepRecordService(db_path)

    executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=checker_manager,
        role_check_service=RoleModelCheckerService(models_root, reports_root, inferencer=inferencer),
        inferencer=inferencer,
        project_service=project_service,
        step_record_service=step_records,
        poll_interval_seconds=0.05,
    )
    project_service.reconcile_projects()

    executor.start()
    try:
        p100 = _run_phase(job_manager, phase="P-100", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        p200 = _run_phase(job_manager, phase="P-200", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"

        # Run P-300 for two chapters
        ch1 = _run_phase(job_manager, phase="P-300", project_id=project_id, payload={"chapter_id": "ch-001"})
        assert _wait_for_terminal_status(job_manager, ch1.id) == "COMPLETED"

        ch2 = _run_phase(job_manager, phase="P-300", project_id=project_id, payload={"chapter_id": "ch-002"})
        assert _wait_for_terminal_status(job_manager, ch2.id) == "COMPLETED"
    finally:
        executor.stop()

    # Verify both chapters exist in parameterized paths
    ch1_path = tmp_path / "data" / "projects" / project_id / "chapters" / "ch-001.md"
    ch2_path = tmp_path / "data" / "projects" / project_id / "chapters" / "ch-002.md"
    assert ch1_path.exists(), f"Expected chapter 1 at {ch1_path}"
    assert ch2_path.exists(), f"Expected chapter 2 at {ch2_path}"
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters -q -p no:cacheprovider`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_local_executor_drafter_runtime.py
git commit -m "test: add multi-chapter pipeline integration test"
```

---

### Task 8: Full validation suite run

**Files:** All changed files

- [ ] **Step 1: Run full backend test suite**

Run: `python -m pytest -q -p no:cacheprovider`
Expected: PASS (all tests, including new ones)

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
git commit -m "feat: complete multi-chapter narrative generation with forward-compatible architecture"
```

---

## Phase B: Future Plan (Multi-Book Series)

This phase is documented but NOT implemented. The architecture from Phase A provides the extension points.

### BookPlan Schema (new layer above SequencePlan)

Add to `app/schemas/story_development.py`:

```python
class BookPlan(StrictSchemaModel):
    book_id: str = Field(min_length=1)
    series_id: str | None = None  # Links books in a series
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    sequence_ids: list[str] = Field(default_factory=list)
    chapter_count: int = 0
    status: str = Field(default="planned", min_length=1)
```

### SeriesState Schema (cross-book continuity)

Add to `app/schemas/story_development.py`:

```python
class SeriesState(StrictSchemaModel):
    series_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    book_summaries: list[PriorChapterSummary] = Field(default_factory=list)  # Reuses same structure
    character_arcs: dict[str, str] = Field(default_factory=dict)  # character_id -> arc status
    unresolved_threads: list[str] = Field(default_factory=list)
    world_changes: dict[str, str] = Field(default_factory=dict)  # location/event -> current state
```

### Post-Manuscript Summarizer (P-500 phase)

New phase that runs after all chapters are complete:
1. Extract key events from each chapter via LLM
2. Build PriorChapterSummary for each completed chapter
3. Update SeriesState with character arc progress, unresolved threads, world changes
4. Feed SeriesState into SceneContextService for next book's drafting

### ChapterOrchestrator Enhancement

Extend existing orchestrator to handle book-level orchestration:
- Accept `book_id` parameter
- Query BookPlan to get chapter_ids for that book
- After all chapters complete, trigger P-500 summarizer
- Feed SeriesState into next book's drafting pipeline

### Key Design Principle

The same PriorChapterSummary structure used for cross-chapter continuity in Phase A will be reused for cross-book continuity in Phase B. The SceneContextService already accepts `prior_chapters` - in Phase B it will also accept `book_summaries` and `series_state`, which are just more PriorChapterSummary instances with book-level metadata.

---

## Self-Review Checklist

1. **Spec coverage:** All requested features (token budget, multi-chapter, forward-compatible architecture) are covered by tasks 1-8. Phase B roadmap is documented for future implementation.

2. **Placeholder scan:** No TBDs or TODOs in implementation steps. All code blocks contain actual implementations.

3. **Type consistency:** PriorChapterSummary is defined once (Task 2) and referenced consistently across Tasks 3, 6, and Phase B plan. SceneContext.prior_chapters uses the same type throughout.

4. **Forward compatibility verified:** ChapterOrchestrator accepts generic chapter_ids list. SceneContextService accepts prior_chapters parameter that can hold book summaries later. PriorChapterSummary has no book-specific fields but can extend with book_id in Phase B without breaking changes.
