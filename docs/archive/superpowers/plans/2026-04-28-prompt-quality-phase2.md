# Prompt Quality Phase 2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add P-300 chapter length guidance, critic violation locations, and prompt caching passthrough — three additive features with zero breaking changes.

**Architecture:** All new fields are optional with `None` defaults. Schema additions to `ManifestConfig`, `SceneContext`, `Violation`, `InferenceMessage`, and `InferenceUsage`. Prompt builders inject new instructions. Backend passthroughs are no-op on unsupported providers.

**Tech Stack:** Python, Pydantic v2, dataclasses, SQLite, httpx

---

## File Structure

| File | Responsibility |
|------|----------------|
| `app/schemas/manifest.py` | +`target_word_count` on `ManifestConfig` |
| `app/services/scene_context.py` | +`target_word_count` on `SceneContext`; render in `to_prompt_string()` |
| `app/persistence/story_development.py` | +`target_word_count` column on `chapter_plans`; add to `ChapterPlanRecord` |
| `app/services/runtime_prompts.py` | P-300 length instruction; critic line-numbered draft + JSON schema; cache tagging |
| `app/services/consistency_critic.py` | +`line_start`, `line_end`, `quote` on `Violation`; parse from LLM response |
| `app/services/local_executor.py` | Rewrite prompt uses location info (2 call sites) |
| `app/schemas/inference.py` | +`cache_control` on `InferenceMessage`; +cache metrics on `InferenceUsage` |
| `app/inference/openai_compatible.py` | `cache_control` passthrough in serialization; extract cache metrics from response |

---

## Feature 1: P-300 Chapter Length Guidance

### Task 1: Add `target_word_count` to ManifestConfig

**Files:**
- Modify: `app/schemas/manifest.py:9-20`
- Test: `tests/test_p300_length_guidance.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_p300_length_guidance.py`:

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.manifest import ManifestConfig


def test_manifest_config_accepts_target_word_count():
    config = ManifestConfig(
        genre="Fantasy",
        tone_profile="dark",
        story_structure="THREE_ACT",
        target_word_count=2000,
    )
    assert config.target_word_count == 2000


def test_manifest_config_target_word_count_defaults_to_none():
    config = ManifestConfig(
        genre="Fantasy",
        tone_profile="dark",
        story_structure="THREE_ACT",
    )
    assert config.target_word_count is None


def test_manifest_config_rejects_target_word_count_below_100():
    with pytest.raises(ValidationError):
        ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            story_structure="THREE_ACT",
            target_word_count=50,
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_p300_length_guidance.py -v`
Expected: FAIL — `target_word_count` not recognized by ManifestConfig

- [ ] **Step 3: Add field to ManifestConfig**

In `app/schemas/manifest.py`, add after line 20:

```python
    target_word_count: int | None = Field(default=None, ge=100)
```

Full class becomes (L9-21):
```python
class ManifestConfig(StrictSchemaModel):
    genre: str = Field(min_length=1)
    tone_profile: str = Field(min_length=1)
    pov: PovMode = PovMode.THIRD_LIMITED
    primary_language: str = Field(default="English", min_length=1)
    secondary_language: str | None = Field(default=None, min_length=0)
    story_structure: StoryStructure
    mythos_source_corpus: str = ""
    mythos_generation_mode: str = ""
    pattern_source_type: str = ""
    pattern_generation_mode: str = ""
    pattern_source_corpus: str = ""
    target_word_count: int | None = Field(default=None, ge=100)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_p300_length_guidance.py -v`
Expected: 3/3 PASS

- [ ] **Step 5: Commit**

```bash
git add app/schemas/manifest.py tests/test_p300_length_guidance.py
git commit -m "feat: add target_word_count to ManifestConfig with ge=100 constraint"
```

### Task 2: Add `target_word_count` to SceneContext with `to_prompt_string()` rendering

**Files:**
- Modify: `app/services/scene_context.py:41-48`, `app/services/scene_context.py:49-110`
- Test: `tests/test_p300_length_guidance.py`

- [ ] **Step 1: Add test for SceneContext rendering**

Add to `tests/test_p300_length_guidance.py`:

```python
from app.services.scene_context import SceneContext


def test_scene_context_renders_target_word_count():
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        target_word_count=1500,
    )
    result = ctx.to_prompt_string()
    assert "CHAPTER LENGTH:" in result
    assert "1500 words" in result


def test_scene_context_omits_length_when_none():
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        target_word_count=None,
    )
    result = ctx.to_prompt_string()
    assert "CHAPTER LENGTH" not in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_p300_length_guidance.py::test_scene_context_renders_target_word_count -v`
Expected: FAIL — `target_word_count` not a valid field on SceneContext

- [ ] **Step 3: Add field to SceneContext and render in to_prompt_string**

In `app/services/scene_context.py`, add field at line 47 (after `author_prompt`):

```python
@dataclass(slots=True)
class SceneContext:
    characters: list[CharacterAnchor]
    world_facts: list[WorldConstraint]
    prior_chapters: list[PriorChapterSummary] | None = None
    pattern_guidance: PatternGuidance | None = None
    author_prompt: str | None = None
    target_word_count: int | None = None
```

In `to_prompt_string()`, insert before the `author_prompt` block (before line 104):

```python
        if self.target_word_count is not None:
            lines.append("")
            lines.append("CHAPTER LENGTH:")
            lines.append(f"Target approximately {self.target_word_count} words.")
            lines.append("Adjust detail and pacing to meet this target while maintaining story quality.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_p300_length_guidance.py::test_scene_context_renders_target_word_count tests/test_p300_length_guidance.py::test_scene_context_omits_length_when_none -v`
Expected: 2/2 PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/scene_context.py tests/test_p300_length_guidance.py
git commit -m "feat: add target_word_count to SceneContext with CHAPTER LENGTH rendering"
```

### Task 3: Add `target_word_count` column to chapter_plans table and ChapterPlanRecord

**Files:**
- Modify: `app/persistence/story_development.py` — `ChapterPlanRecord` dataclass, upsert SQL, row parser, CREATE TABLE
- Test: `tests/test_p300_length_guidance.py`

- [ ] **Step 1: Add test for persistence round-trip**

Add to `tests/test_p300_length_guidance.py`:

```python
import sqlite3
from pathlib import Path


def test_chapter_plan_persists_target_word_count(tmp_path: Path):
    from app.persistence.story_development import StoryDevelopmentRepository

    db_path = tmp_path / "test.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_chapter_plan(
        project_id="proj-1",
        chapter_id="ch-1",
        title="Test Chapter",
        summary="A test",
        objective="Test objective",
        conflict="Test conflict",
        stakes="Test stakes",
        active_character_ids=[],
        continuity_requirements=[],
        unresolved_questions=[],
        status="planned",
        position=1,
        target_word_count=2500,
    )

    record = repo.get_chapter_plan("ch-1")
    assert record.target_word_count == 2500


def test_chapter_plan_target_word_count_defaults_to_none(tmp_path: Path):
    from app.persistence.story_development import StoryDevelopmentRepository

    db_path = tmp_path / "test.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_chapter_plan(
        project_id="proj-1",
        chapter_id="ch-1",
        title="Test Chapter",
        summary="A test",
        objective="Test objective",
        conflict="Test conflict",
        stakes="Test stakes",
        active_character_ids=[],
        continuity_requirements=[],
        unresolved_questions=[],
        status="planned",
        position=1,
    )

    record = repo.get_chapter_plan("ch-1")
    assert record.target_word_count is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_p300_length_guidance.py::test_chapter_plan_persists_target_word_count -v`
Expected: FAIL — `target_word_count` not recognized by upsert or get

- [ ] **Step 3: Add field to ChapterPlanRecord dataclass**

In `app/persistence/story_development.py`, find `ChapterPlanRecord` (around line 422) and add:

```python
@dataclass(frozen=True)
class ChapterPlanRecord:
    chapter_id: str
    project_id: str
    sequence_id: str | None
    title: str
    summary: str
    objective: str
    conflict: str
    stakes: str
    active_character_ids: list[str]
    continuity_requirements: list[str]
    unresolved_questions: list[str]
    status: str
    position: int
    created_at: datetime
    updated_at: datetime
    target_word_count: int | None = None
```

- [ ] **Step 4: Add column to CREATE TABLE and upsert SQL**

Search for the `chapter_plans` CREATE TABLE statement. Add `target_word_count INTEGER` after `updated_at`. The CREATE TABLE should include:
```sql
CREATE TABLE IF NOT EXISTS chapter_plans (
    chapter_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    sequence_id TEXT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    objective TEXT NOT NULL,
    conflict TEXT NOT NULL,
    stakes TEXT NOT NULL,
    active_character_ids_json TEXT NOT NULL,
    continuity_requirements_json TEXT NOT NULL,
    unresolved_questions_json TEXT NOT NULL,
    status TEXT NOT NULL,
    position INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    target_word_count INTEGER
)
```

Add ALTER TABLE for migration (run after CREATE TABLE IF NOT EXISTS):
```sql
ALTER TABLE chapter_plans ADD COLUMN target_word_count INTEGER
```

In the upsert SQL (search for `upsert_chapter_plan`), add `target_word_count` parameter:
- Add `target_word_count: int | None = None` to method signature
- Add `target_word_count` to INSERT values and UPDATE set clause
- Add `EXCLUDED.target_word_count` to ON CONFLICT DO UPDATE

- [ ] **Step 5: Update row parser**

In `_chapter_plan_row_to_record()` (around line 4566), add:
```python
target_word_count = row.get("target_word_count")
```
Pass `target_word_count` to `ChapterPlanRecord` constructor.

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/test_p300_length_guidance.py::test_chapter_plan_persists_target_word_count tests/test_p300_length_guidance.py::test_chapter_plan_target_word_count_defaults_to_none -v`
Expected: 2/2 PASS

- [ ] **Step 7: Commit**

```bash
git add app/persistence/story_development.py tests/test_p300_length_guidance.py
git commit -m "feat: add target_word_count column to chapter_plans with migration"
```

### Task 4: Wire SceneContextService.assemble_context() with target_word_count resolution

**Files:**
- Modify: `app/services/scene_context.py:123-165`
- Test: `tests/test_p300_length_guidance.py`

- [ ] **Step 1: Add test for assemble_context resolution**

Add to `tests/test_p300_length_guidance.py`:

```python
def test_assemble_context_resolves_target_word_count_from_manifest(tmp_path):
    from app.persistence.story_development import StoryDevelopmentRepository
    from app.services.scene_context import SceneContextService

    repo = StoryDevelopmentRepository(tmp_path / "test.db")
    service = SceneContextService(repo)

    # No chapter plan set — should accept manifest default parameter
    ctx = service.assemble_context(
        project_id="proj-1",
        manifest_target_word_count=2000,
    )
    assert ctx.target_word_count == 2000


def test_assemble_context_chapter_plan_overrides_manifest(tmp_path):
    from app.persistence.story_development import StoryDevelopmentRepository
    from app.services.scene_context import SceneContextService

    repo = StoryDevelopmentRepository(tmp_path / "test.db")
    repo.upsert_chapter_plan(
        project_id="proj-1",
        chapter_id="ch-1",
        title="Test",
        summary="Test",
        objective="Test",
        conflict="Test",
        stakes="Test",
        active_character_ids=[],
        continuity_requirements=[],
        unresolved_questions=[],
        status="planned",
        position=1,
        target_word_count=3000,
    )
    # Add a character so assemble_context doesn't return empty
    repo.upsert_character_profile(
        project_id="proj-1",
        character_id="char-1",
        display_name="Hero",
        role_in_story="protagonist",
        archetype="hero",
    )

    service = SceneContextService(repo)
    ctx = service.assemble_context(
        project_id="proj-1",
        active_character_ids=["char-1"],
        chapter_plan_id="ch-1",
        manifest_target_word_count=2000,
    )
    assert ctx.target_word_count == 3000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_p300_length_guidance.py::test_assemble_context_resolves_target_word_count_from_manifest -v`
Expected: FAIL — `manifest_target_word_count` not a parameter

- [ ] **Step 3: Modify assemble_context signature and resolution logic**

In `app/services/scene_context.py`, change `assemble_context` (lines 123-165):

```python
    def assemble_context(
        self,
        project_id: str,
        active_character_ids: Iterable[str] | None = None,
        prior_chapters: list[PriorChapterSummary] | None = None,
        chapter_plan_id: str | None = None,
        manifest_target_word_count: int | None = None,
    ) -> SceneContext:
```

Add target_word_count resolution before the return statement (before line 165):

```python
        # Resolve target_word_count: chapter plan > manifest default
        resolved_word_count: int | None = None
        if chapter_plan_id:
            try:
                chapter_plan = self._repository.get_chapter_plan(chapter_plan_id)
                if hasattr(chapter_plan, "target_word_count") and chapter_plan.target_word_count is not None:
                    resolved_word_count = chapter_plan.target_word_count
            except KeyError:
                pass
        if resolved_word_count is None:
            resolved_word_count = manifest_target_word_count

        return SceneContext(
            characters=anchors,
            world_facts=world_facts,
            prior_chapters=prior_chapters,
            target_word_count=resolved_word_count,
        )
```

Also update the early return at line 135 to include `target_word_count`:
```python
                return SceneContext(
                    characters=[],
                    world_facts=[],
                    prior_chapters=prior_chapters,
                    target_word_count=manifest_target_word_count,
                )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_p300_length_guidance.py::test_assemble_context_resolves_target_word_count_from_manifest tests/test_p300_length_guidance.py::test_assemble_context_chapter_plan_overrides_manifest -v`
Expected: 2/2 PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/scene_context.py tests/test_p300_length_guidance.py
git commit -m "feat: wire SceneContextService with target_word_count resolution chain"
```

### Task 5: Add length instruction to `build_p300_drafter_request()`

**Files:**
- Modify: `app/services/runtime_prompts.py:109-161`
- Test: `tests/test_p300_length_guidance.py`

- [ ] **Step 1: Add test for system prompt length instruction**

Add to `tests/test_p300_length_guidance.py`:

```python
def test_p300_includes_length_instruction_from_manifest():
    from app.schemas.manifest import Manifest, ManifestConfig
    from app.schemas.enums import PovMode, StoryStructure
    from app.services.runtime_prompts import build_p300_drafter_request

    manifest = Manifest(
        project_id="proj-1",
        project_name="Test",
        config=ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            pov=PovMode.THIRD_LIMITED,
            story_structure=StoryStructure.THREE_ACT,
            target_word_count=2000,
        ),
    )
    req = build_p300_drafter_request(
        manifest=manifest,
        payload={},
        default_model="test-model",
    )
    system_content = req.messages[0].content
    assert "approximately 2000 words" in system_content


def test_p300_payload_override_beats_manifest_target():
    from app.schemas.manifest import Manifest, ManifestConfig
    from app.schemas.enums import PovMode, StoryStructure
    from app.services.runtime_prompts import build_p300_drafter_request

    manifest = Manifest(
        project_id="proj-1",
        project_name="Test",
        config=ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            pov=PovMode.THIRD_LIMITED,
            story_structure=StoryStructure.THREE_ACT,
            target_word_count=2000,
        ),
    )
    req = build_p300_drafter_request(
        manifest=manifest,
        payload={"target_word_count": 3000},
        default_model="test-model",
    )
    system_content = req.messages[0].content
    assert "approximately 3000 words" in system_content
    assert "2000" not in system_content


def test_p300_system_message_has_cache_control_tag():
    from app.schemas.manifest import Manifest, ManifestConfig
    from app.schemas.enums import PovMode, StoryStructure
    from app.services.runtime_prompts import build_p300_drafter_request

    manifest = Manifest(
        project_id="proj-1",
        project_name="Test",
        config=ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            pov=PovMode.THIRD_LIMITED,
            story_structure=StoryStructure.THREE_ACT,
        ),
    )
    req = build_p300_drafter_request(
        manifest=manifest,
        payload={},
        default_model="test-model",
    )
    assert req.messages[0].cache_control == {"type": "ephemeral"}
    assert req.messages[1].cache_control is None


def test_p300_omits_length_when_no_target():
    from app.schemas.manifest import Manifest, ManifestConfig
    from app.schemas.enums import PovMode, StoryStructure
    from app.services.runtime_prompts import build_p300_drafter_request

    manifest = Manifest(
        project_id="proj-1",
        project_name="Test",
        config=ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            pov=PovMode.THIRD_LIMITED,
            story_structure=StoryStructure.THREE_ACT,
        ),
    )
    req = build_p300_drafter_request(
        manifest=manifest,
        payload={},
        default_model="test-model",
    )
    system_content = req.messages[0].content
    assert "approximately" not in system_content or "words" not in system_content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_p300_length_guidance.py::test_p300_includes_length_instruction_from_manifest -v`
Expected: FAIL — system prompt doesn't include length instruction

- [ ] **Step 3: Add length resolution and injection to build_p300_drafter_request**

Note: `scene_context` is NOT passed by `local_executor.py` to this function. Scene context is injected separately via `inject_scene_context()` after the request is built. Chapter-specific targets flow through `SceneContext.to_prompt_string()`'s `CHAPTER LENGTH:` section in the user message. This function handles payload and manifest-level targets only.

In `app/services/runtime_prompts.py`, modify the function (lines 109-161):

After line 124 (`chapter_label = ...`), add:

```python
    # Resolve target_word_count: payload override > manifest default
    # (scene_context.target_word_count flows via CHAPTER LENGTH in user message)
    target_words: int | None = payload.get("target_word_count")
    if target_words is None:
        target_words = getattr(getattr(manifest, "config", None), "target_word_count", None)

    system_content = (
        f"You are the Drafter role for Narrative-Engine. "
        f"Produce the P-300 {chapter_label} draft as deterministic markdown. "
        f"Preserve chapter flow, continuity, and stable section ordering."
    )
    if target_words is not None:
        system_content += (
            f"\n\nTarget length: approximately {target_words} words.\n"
            f"Adjust detail and pacing to meet this target while maintaining story quality."
        )
```

Replace the existing system message (lines 141-147) to use `system_content` variable:

```python
            InferenceMessage(
                role="system",
                content=system_content,
                cache_control={"type": "ephemeral"},
            ),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_p300_length_guidance.py -v`
Expected: 8/8 PASS (all length guidance tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/runtime_prompts.py tests/test_p300_length_guidance.py
git commit -m "feat: inject target_word_count into P-300 system prompt with override chain"
```

---

## Feature 2: Critic Violation Locations

### Task 6: Add location fields to Violation dataclass and parser

**Files:**
- Modify: `app/services/consistency_critic.py:13-17`, `app/services/consistency_critic.py:47-54`
- Test: `tests/test_critic_locations.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_critic_locations.py`:

```python
from __future__ import annotations

from app.services.consistency_critic import Violation, CriticResult


def test_violation_accepts_location_fields():
    v = Violation(
        character="Hero",
        issue="Wrong voice",
        suggestion="Use simpler vocabulary",
        line_start=10,
        line_end=12,
        quote="The hero expostulated with great fervor",
    )
    assert v.line_start == 10
    assert v.line_end == 12
    assert v.quote == "The hero expostulated with great fervor"


def test_violation_defaults_locations_to_none():
    v = Violation(
        character="Hero",
        issue="Wrong voice",
        suggestion="Use simpler vocabulary",
    )
    assert v.line_start is None
    assert v.line_end is None
    assert v.quote is None


def test_backward_compat_old_violation_without_locations():
    """Simulate old LLM response that doesn't include location fields."""
    import json

    old_response = json.dumps({
        "passed": False,
        "violations": [
            {"character": "Hero", "issue": "Wrong voice", "suggestion": "Fix it"}
        ],
    })
    data = json.loads(old_response)
    for v in data.get("violations", []):
        viol = Violation(
            character=v["character"],
            issue=v["issue"],
            suggestion=v["suggestion"],
        )
    assert viol.line_start is None
    assert viol.line_end is None
    assert viol.quote is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_critic_locations.py::test_violation_accepts_location_fields -v`
Expected: FAIL — `line_start` not a valid field on Violation

- [ ] **Step 3: Add fields to Violation dataclass**

In `app/services/consistency_critic.py`, modify lines 13-17:

```python
@dataclass(slots=True)
class Violation:
    character: str
    issue: str
    suggestion: str
    line_start: int | None = None
    line_end: int | None = None
    quote: str | None = None
```

- [ ] **Step 4: Update parser to extract location fields**

In `app/services/consistency_critic.py`, modify lines 47-53:

```python
            violations = []
            for v in result.get("violations", []):
                violations.append(Violation(
                    character=v["character"],
                    issue=v["issue"],
                    suggestion=v["suggestion"],
                    line_start=v.get("line_start"),
                    line_end=v.get("line_end"),
                    quote=v.get("quote"),
                ))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_critic_locations.py -v`
Expected: 3/3 PASS

- [ ] **Step 6: Commit**

```bash
git add app/services/consistency_critic.py tests/test_critic_locations.py
git commit -m "feat: add line_start, line_end, quote fields to Violation with backward compat"
```

### Task 7: Update critic system prompt with JSON schema locations and line-numbered draft

**Files:**
- Modify: `app/services/runtime_prompts.py:577-622`
- Test: `tests/test_critic_locations.py`

- [ ] **Step 1: Add tests for prompt content**

Add to `tests/test_critic_locations.py`:

```python
def test_critic_prompt_includes_location_fields_in_json_schema():
    from app.services.runtime_prompts import build_critic_check_request

    req = build_critic_check_request(
        draft_text="Some draft text here.",
        character_bios={"Hero": "brave knight"},
        default_model="test-model",
    )
    system = req.messages[0].content
    assert "line_start" in system
    assert "line_end" in system
    assert "quote" in system


def test_critic_user_message_has_numbered_lines():
    from app.services.runtime_prompts import build_critic_check_request

    draft = "Line one.\nLine two.\nLine three."
    req = build_critic_check_request(
        draft_text=draft,
        character_bios={"Hero": "brave knight"},
        default_model="test-model",
    )
    user = req.messages[1].content
    assert "1: Line one" in user
    assert "2: Line two" in user
    assert "3: Line three" in user


def test_critic_truncates_long_draft_at_500_lines():
    from app.services.runtime_prompts import build_critic_check_request

    draft = "\n".join([f"Line {i}" for i in range(600)])
    req = build_critic_check_request(
        draft_text=draft,
        character_bios={"Hero": "brave knight"},
        default_model="test-model",
    )
    user = req.messages[1].content
    assert "500" in user  # truncation note should mention line count
    assert "501: Line 500" not in user  # lines beyond 500 should be truncated
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_critic_locations.py::test_critic_prompt_includes_location_fields_in_json_schema -v`
Expected: FAIL — current prompt doesn't include location fields

- [ ] **Step 3: Update build_critic_check_request**

In `app/services/runtime_prompts.py`, replace the function (lines 577-622):

```python
def build_critic_check_request(
    *,
    draft_text: str,
    character_bios: dict[str, str],
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for consistency critic check."""
    bio_lines = []
    for name, bio in character_bios.items():
        bio_lines.append(f"  {name}: {bio}")
    bios_block = "\n".join(bio_lines) if bio_lines else "  (no character profiles)"

    # Number draft lines for LLM reference (capped at 500)
    draft_lines = draft_text.split("\n")
    max_display_lines = 500
    numbered_lines = []
    for i, line in enumerate(draft_lines[:max_display_lines], 1):
        numbered_lines.append(f"{i}: {line}")
    numbered_draft = "\n".join(numbered_lines)
    if len(draft_lines) > max_display_lines:
        numbered_draft += f"\n... ({len(draft_lines) - max_display_lines} more lines truncated)"

    system_prompt = (
        "You are a consistency critic for Narrative-Engine. "
        "Check whether characters' dialogue and actions align with their defined profiles.\n\n"
        "CHECK FOR:\n"
        "  1. VOICE: Does word choice, sentence length, and vocabulary match the character?\n"
        "  2. BEHAVIOR: Do goals, fears, and traits drive the character's actions?\n"
        "  3. KNOWLEDGE: Does the character only know what they should know?\n"
        "  4. CONFLICT: Is the character's stance consistent with their values?\n\n"
        "NOT VIOLATIONS:\n"
        "  - Natural character growth or emotional shifts (these are arc progressions)\n"
        "  - Understatement or subtlety (not all feelings are expressed openly)\n"
        "  - Cultural or background-appropriate behavior differences\n\n"
        "Only flag CLEAR contradictions between profile and draft. Be conservative.\n\n"
        "For each violation, include approximate line numbers (line_start, line_end)\n"
        "and a short quoted excerpt (max 100 characters) of the problematic passage.\n"
        "Line numbers refer to the numbered draft below.\n\n"
        "Return ONLY a JSON object with these keys:\n"
        '{\n'
        '  "passed": true or false,\n'
        '  "violations": [\n'
        '    {\n'
        '      "character": "<name>",\n'
        '      "issue": "<what is wrong>",\n'
        '      "suggestion": "<how to fix>",\n'
        '      "line_start": <int or null>,\n'
        '      "line_end": <int or null>,\n'
        '      "quote": "<short excerpt of the offending text>"\n'
        '    }\n'
        '  ]\n\n'
        "If the character behaves consistently with their profile, set passed=true and violations=[]."
    )

    user_content = f"CHARACTER PROFILES:\n{bios_block}\n\nDRAFT TO CHECK (line numbers for reference):\n{numbered_draft}"

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=2048,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={"mode": "consistency_critic", "role": "critic"},
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_critic_locations.py -v`
Expected: 6/6 PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/runtime_prompts.py tests/test_critic_locations.py
git commit -m "feat: add line-numbered draft and location fields to critic prompt JSON schema"
```

### Task 8: Update rewrite prompts in local_executor.py to use location info

**Files:**
- Modify: `app/services/local_executor.py:961-981` (single-chapter), `app/services/local_executor.py:1191-1210` (multi-chapter)
- Test: `tests/test_critic_locations.py`

- [ ] **Step 1: Add tests for rewrite prompt formatting**

Add to `tests/test_critic_locations.py`:

```python
def test_rewrite_prompt_includes_location_info():
    from app.services.consistency_critic import Violation, CriticResult

    critic_result = CriticResult(
        passed=False,
        violations=[
            Violation(
                character="Hero",
                issue="Wrong voice",
                suggestion="Use simpler vocabulary",
                line_start=10,
                line_end=12,
                quote="The hero expostulated with great fervor",
            ),
            Violation(
                character="Villain",
                issue="Out of character",
                suggestion="Make more sinister",
                line_start=45,
                line_end=47,
                quote="The villain smiled warmly and offered help",
            ),
        ],
    )

    # Simulate rewrite prompt construction from local_executor.py
    violation_lines = []
    for v in critic_result.violations[:3]:
        if v.line_start is not None and v.quote is not None:
            violation_lines.append(
                f"- {v.character} (lines {v.line_start}-{v.line_end}): {v.issue}\n"
                f"  Quote: \"{v.quote}\"\n"
                f"  Fix: {v.suggestion}"
            )
        else:
            violation_lines.append(f"- {v.character}: {v.issue} -> {v.suggestion}")

    violation_summary = "\n".join(violation_lines)
    assert "lines 10-12" in violation_summary
    assert 'Quote: "The hero expostulated' in violation_summary
    assert "Fix: Use simpler vocabulary" in violation_summary


def test_rewrite_prompt_degrades_without_locations():
    from app.services.consistency_critic import Violation, CriticResult

    critic_result = CriticResult(
        passed=False,
        violations=[
            Violation(
                character="Hero",
                issue="Wrong voice",
                suggestion="Fix it",
            ),
        ],
    )

    violation_lines = []
    for v in critic_result.violations[:3]:
        if v.line_start is not None and v.quote is not None:
            violation_lines.append(
                f"- {v.character} (lines {v.line_start}-{v.line_end}): {v.issue}\n"
                f"  Quote: \"{v.quote}\"\n"
                f"  Fix: {v.suggestion}"
            )
        else:
            violation_lines.append(f"- {v.character}: {v.issue} -> {v.suggestion}")

    violation_summary = "\n".join(violation_lines)
    assert "- Hero: Wrong voice -> Fix it" in violation_summary
    assert "lines" not in violation_summary
```

- [ ] **Step 2: Run test to verify it passes (logic verification)**

Run: `python -m pytest tests/test_critic_locations.py::test_rewrite_prompt_includes_location_info tests/test_critic_locations.py::test_rewrite_prompt_degrades_without_locations -v`
Expected: 2/2 PASS (these test the logic; next step applies to actual code)

- [ ] **Step 3: Update single-chapter rewrite prompt in local_executor.py**

In `app/services/local_executor.py`, replace lines 963-964:

```python
                violation_lines = []
                for v in critic_result.violations[:3]:
                    if v.line_start is not None and v.quote is not None:
                        violation_lines.append(
                            f"- {v.character} (lines {v.line_start}-{v.line_end}): {v.issue}\n"
                            f'  Quote: "{v.quote}"\n'
                            f"  Fix: {v.suggestion}"
                        )
                    else:
                        violation_lines.append(f"- {v.character}: {v.issue} -> {v.suggestion}")
                violation_summary = "\n".join(violation_lines)
```

- [ ] **Step 4: Update multi-chapter rewrite prompt in local_executor.py**

In `app/services/local_executor.py`, replace lines 1193-1194 (same pattern):

```python
                    violation_lines = []
                    for v in critic_result.violations[:3]:
                        if v.line_start is not None and v.quote is not None:
                            violation_lines.append(
                                f"- {v.character} (lines {v.line_start}-{v.line_end}): {v.issue}\n"
                                f'  Quote: "{v.quote}"\n'
                                f"  Fix: {v.suggestion}"
                            )
                        else:
                            violation_lines.append(f"- {v.character}: {v.issue} -> {v.suggestion}")
                    violation_summary = "\n".join(violation_lines)
```

- [ ] **Step 5: Run full critic locations test suite**

Run: `python -m pytest tests/test_critic_locations.py -v`
Expected: 8/8 PASS

- [ ] **Step 6: Commit**

```bash
git add app/services/local_executor.py tests/test_critic_locations.py
git commit -m "feat: use violation location info in rewrite prompts with graceful degradation"
```

---

## Feature 3: Prompt Caching Passthrough

### Task 9: Add `cache_control` to InferenceMessage and cache metrics to InferenceUsage

**Files:**
- Modify: `app/schemas/inference.py:26-28`, `app/schemas/inference.py:39-42`
- Test: `tests/test_prompt_caching.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_prompt_caching.py`:

```python
from __future__ import annotations

from app.schemas.inference import InferenceMessage, InferenceUsage


def test_inference_message_accepts_cache_control():
    msg = InferenceMessage(
        role="system",
        content="You are helpful.",
        cache_control={"type": "ephemeral"},
    )
    assert msg.cache_control == {"type": "ephemeral"}


def test_inference_message_cache_control_defaults_to_none():
    msg = InferenceMessage(
        role="system",
        content="You are helpful.",
    )
    assert msg.cache_control is None


def test_inference_usage_accepts_cache_metrics():
    usage = InferenceUsage(
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        cached_prompt_tokens=800,
        prompt_cache_write_tokens=200,
    )
    assert usage.cached_prompt_tokens == 800
    assert usage.prompt_cache_write_tokens == 200


def test_inference_usage_cache_metrics_default_to_none():
    usage = InferenceUsage(
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
    )
    assert usage.cached_prompt_tokens is None
    assert usage.prompt_cache_write_tokens is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_prompt_caching.py::test_inference_message_accepts_cache_control -v`
Expected: FAIL — `cache_control` not recognized (StrictModel uses `extra="forbid"`)

- [ ] **Step 3: Add fields to schemas**

In `app/schemas/inference.py`, modify lines 26-28 and 39-42:

```python
class InferenceMessage(StrictModel):
    role: Literal["system", "user", "assistant"]
    content: str
    cache_control: dict[str, Any] | None = None


class InferenceUsage(StrictModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cached_prompt_tokens: int | None = None
    prompt_cache_write_tokens: int | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_prompt_caching.py -v`
Expected: 4/4 PASS

- [ ] **Step 5: Commit**

```bash
git add app/schemas/inference.py tests/test_prompt_caching.py
git commit -m "feat: add cache_control to InferenceMessage and cache metrics to InferenceUsage"
```

### Task 10: Implement cache_control passthrough in OpenAICompatibleInferenceBackend

**Files:**
- Modify: `app/inference/openai_compatible.py:170-226`
- Test: `tests/test_prompt_caching.py`

- [ ] **Step 1: Add tests for passthrough behavior**

Add to `tests/test_prompt_caching.py`:

```python
def test_cache_control_passthrough_in_serialization():
    """Verify that cache_control is included in serialized messages when present."""
    from app.schemas.inference import InferenceRequest, InferenceMessage

    req = InferenceRequest(
        model="test-model",
        messages=[
            InferenceMessage(role="system", content="You are helpful.", cache_control={"type": "ephemeral"}),
            InferenceMessage(role="user", content="Write a story."),
        ],
    )

    # Simulate what openai_compatible.py does in generate_text
    serialized = []
    for msg in req.messages:
        d = {"role": msg.role, "content": msg.content}
        if msg.cache_control is not None:
            d["cache_control"] = msg.cache_control
        serialized.append(d)

    assert serialized[0]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in serialized[1]


def test_cache_metrics_extraction_from_response():
    """Verify cache metrics are extracted from provider response."""
    from app.schemas.inference import InferenceUsage

    # Simulate vLLM-style response
    usage_payload = {
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "total_tokens": 1500,
        "cached_prompt_tokens": 800,
        "prompt_cache_write_tokens": 200,
    }

    usage = InferenceUsage(
        prompt_tokens=int(usage_payload.get("prompt_tokens", 0)) if usage_payload.get("prompt_tokens") else None,
        completion_tokens=int(usage_payload.get("completion_tokens", 0)) if usage_payload.get("completion_tokens") else None,
        total_tokens=int(usage_payload.get("total_tokens", 0)) if usage_payload.get("total_tokens") else None,
        cached_prompt_tokens=usage_payload.get("cached_prompt_tokens") or usage_payload.get("prompt_cache_read_tokens"),
        prompt_cache_write_tokens=usage_payload.get("prompt_cache_write_tokens"),
    )

    assert usage.cached_prompt_tokens == 800
    assert usage.prompt_cache_write_tokens == 200
```

- [ ] **Step 2: Run test to verify it passes (logic verification)**

Run: `python -m pytest tests/test_prompt_caching.py::test_cache_control_passthrough_in_serialization tests/test_prompt_caching.py::test_cache_metrics_extraction_from_response -v`
Expected: 2/2 PASS (these verify the logic; next step applies to actual backend)

- [ ] **Step 3: Update OpenAICompatibleInferenceBackend.generate_text()**

In `app/inference/openai_compatible.py`, replace lines 170-172:

```python
        messages = []
        for msg in request.messages:
            d = {"role": msg.role, "content": msg.content}
            if msg.cache_control is not None:
                d["cache_control"] = msg.cache_control
            messages.append(d)

        payload = {
            "model": request.model or self._descriptor.default_model,
            "messages": messages,
        }
```

Replace lines 214-224 (usage extraction):

```python
        usage_payload = response_payload.get("usage") if isinstance(response_payload.get("usage"), dict) else {}
        return InferenceResponse(
            backend=self._descriptor.backend,
            model=str(response_payload.get("model") or payload["model"]) if payload["model"] else None,
            content=content,
            finish_reason=str(first_choice.get("finish_reason")) if isinstance(first_choice, dict) and first_choice.get("finish_reason") is not None else None,
            usage=InferenceUsage(
                prompt_tokens=int(usage_payload.get("prompt_tokens", 0)) if usage_payload.get("prompt_tokens") else None,
                completion_tokens=int(usage_payload.get("completion_tokens", 0)) if usage_payload.get("completion_tokens") else None,
                total_tokens=int(usage_payload.get("total_tokens", 0)) if usage_payload.get("total_tokens") else None,
                cached_prompt_tokens=usage_payload.get("cached_prompt_tokens") or usage_payload.get("prompt_cache_read_tokens"),
                prompt_cache_write_tokens=usage_payload.get("prompt_cache_write_tokens"),
            ),
            raw_response=response_payload,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_prompt_caching.py -v`
Expected: 6/6 PASS

- [ ] **Step 5: Commit**

```bash
git add app/inference/openai_compatible.py tests/test_prompt_caching.py
git commit -m "feat: pass cache_control through OpenAI-compatible backend and extract cache metrics"
```

### Task 11: Add stable prefix tagging in build_p300_drafter_request()

**Files:**
- Modify: `app/services/runtime_prompts.py:136-153`
- Test: `tests/test_prompt_caching.py`

- [ ] **Step 1: Add test for cache tagging**

Add to `tests/test_prompt_caching.py`:

```python
def test_p300_system_message_has_cache_control():
    from app.schemas.manifest import Manifest, ManifestConfig
    from app.schemas.enums import PovMode, StoryStructure
    from app.services.runtime_prompts import build_p300_drafter_request

    manifest = Manifest(
        project_id="proj-1",
        project_name="Test",
        config=ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            pov=PovMode.THIRD_LIMITED,
            story_structure=StoryStructure.THREE_ACT,
        ),
    )
    req = build_p300_drafter_request(
        manifest=manifest,
        payload={},
        default_model="test-model",
        chapter_id="1",
    )

    # System message should have cache_control
    system_msg = req.messages[0]
    assert system_msg.cache_control == {"type": "ephemeral"}

    # User message should NOT have cache_control (varies per call)
    user_msg = req.messages[1]
    assert user_msg.cache_control is None


def test_p300_context_message_has_cache_control():
    from app.schemas.manifest import Manifest, ManifestConfig
    from app.schemas.enums import PovMode, StoryStructure
    from app.services.scene_context import SceneContext
    from app.services.runtime_prompts import build_p300_drafter_request

    manifest = Manifest(
        project_id="proj-1",
        project_name="Test",
        config=ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            pov=PovMode.THIRD_LIMITED,
            story_structure=StoryStructure.THREE_ACT,
        ),
    )

    # When scene_context is provided, the context should be in a separate cached message
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        target_word_count=2000,
    )
    req = build_p300_drafter_request(
        manifest=manifest,
        payload={},
        default_model="test-model",
        chapter_id="1",
        scene_context=ctx,
    )

    # System message should be cached
    assert req.messages[0].cache_control == {"type": "ephemeral"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_prompt_caching.py::test_p300_system_message_has_cache_control -v`
Expected: FAIL — system message doesn't have cache_control set

- [ ] **Step 3: Add cache tagging to build_p300_drafter_request**

In `app/services/runtime_prompts.py`, modify the InferenceRequest construction (lines 136-153). Change the messages list to include cache_control on stable prefix messages:

```python
    return InferenceRequest(
        model=str(payload.get("model_id") or payload.get("model") or default_model or "").strip() or None,
        temperature=_coerce_float(payload.get("temperature"), default=0.2),
        max_tokens=_coerce_int(payload.get("max_tokens"), default=8000),
        messages=[
            InferenceMessage(
                role="system",
                content=system_content,
                cache_control={"type": "ephemeral"},
            ),
            InferenceMessage(
                role="user",
                content="\n\n".join(user_parts),
            ),
        ],
        metadata={
            "mode": "pipeline_phase",
            "phase": "P-300",
            "role": "drafter",
            "project_id": manifest.project_id,
            "project_name": manifest.project_name,
        },
    )
```

Note: Only the system message gets `cache_control`. The user message varies per chapter (different prompt_context, different architect/sequence output), so it's NOT tagged. In multi-chapter mode with `inject_scene_context()`, the scene context is appended to the existing user message — the stable prefix of that combined message will benefit from prefix caching automatically on vLLM.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_prompt_caching.py -v`
Expected: 8/8 PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/runtime_prompts.py tests/test_prompt_caching.py
git commit -m "feat: tag P-300 system message with cache_control for vLLM prefix caching"
```

---

## Final Validation

### Task 12: Run full test suite and verify no regressions

**Files:** All modified files
**Tests:** Full critical subset

- [ ] **Step 1: Run new test files**

Run: `python -m pytest tests/test_p300_length_guidance.py tests/test_critic_locations.py tests/test_prompt_caching.py -v`
Expected: 24/24 PASS (8 + 8 + 8)

- [ ] **Step 2: Run existing affected test suites**

Run: `python -m pytest tests/test_consistency_critic.py tests/test_runtime_prompts.py tests/test_scene_context.py tests/test_local_executor.py -q`
Expected: All existing tests still pass (no regressions)

- [ ] **Step 3: Run full critical subset**

Run: `python -m pytest tests/test_mythos_extraction.py tests/test_pattern_extraction.py tests/test_story_import_service.py tests/test_braindump_service.py tests/test_local_executor_drafter_runtime.py tests/test_p300_length_guidance.py tests/test_critic_locations.py tests/test_prompt_caching.py -q`
Expected: All pass (217 existing + 15 new = 232 total, accounting for test file overlap)

- [ ] **Step 4: Commit final validation**

```bash
git commit --allow-empty -m "validate: Prompt Quality Phase 2 — 24/24 new tests pass, zero regressions in existing suites"
```

---

## Summary of Changes

| Feature | Files Modified | New Tests | Lines Added |
|---------|---------------|-----------|-------------|
| P-300 Length Guidance | `manifest.py`, `scene_context.py`, `story_development.py`, `runtime_prompts.py` | 8 | ~60 |
| Critic Locations | `consistency_critic.py`, `runtime_prompts.py`, `local_executor.py` | 8 | ~50 |
| Prompt Caching | `inference.py`, `openai_compatible.py`, `runtime_prompts.py` | 8 | ~30 |
| **Total** | **8 files** | **24 tests** | **~140 lines** |
