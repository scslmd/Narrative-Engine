# Story Import - Implementation Task List

> Complete research-backed task list with all code patterns, column names, and implementation knowledge.
> Branch: `codex/complete-remaining-todos`
> Created: April 2026

---

## Phase 1: Foundation (Service) — 6 tasks

### Task 1.1: Create `app/services/story_import.py` — StoryImportService class skeleton

**File**: `app/services/story_import.py` (NEW)

**Purpose**: Main service class that orchestrates story import flow.

**Pattern to follow**: `ManuscriptReviewService` in `app/services/manuscript_review.py`
- Takes repository and inferencer in `__init__`
- Main method returns a response model
- Uses try/except blocks, returns response (not raises) on controlled failures

**Exact imports needed**:
```python
from __future__ import annotations

import json
import logging
import re
import sqlite3
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from ..inference.base import InferenceBackend, InferenceBackendError
from ..persistence.story_development import StoryDevelopmentRepository
from ..schemas.inference import InferenceRequest
from ..schemas.story_import import (
    StoryImportAnalysis,
    StoryImportArc,
    StoryImportCharacterRequest,
    StoryImportRequest,
    StoryImportResponse,
    StoryImportWorldEntry,
)
from ..settings import settings
from .projects import ProjectService
from .runtime_prompts import build_import_analysis_request

logger = logging.getLogger(__name__)
```

**Class skeleton**:
```python
class StoryImportError(ValueError):
    """Base error for story import failures."""
    pass


class StoryImportService:
    def __init__(
        self,
        *,
        project_service: ProjectService,
        repository: StoryDevelopmentRepository,
        inferencer: InferenceBackend,
        root_dir: Path | None = None,
    ) -> None:
        self._project_service = project_service
        self._repository = repository
        self._inferencer = inferencer
        self._root_dir = root_dir or settings.root_dir

    def import_story(self, request: StoryImportRequest) -> StoryImportResponse:
        """Main entry point. Synchronous processing flow.

        Steps:
        1. Validate request (text length, project_id if provided)
        2. Create project (if project_id not provided, create new)
        3. Call LLM to analyze and extract structured data
        4. Validate LLM output against StoryImportAnalysis schema
        5. Create all entities (foundation, characters, world bible, arcs) in single transaction
        6. Update manifest.json with LLM-extracted metadata (genre, tone, pov, structure)
        7. Return response
        """
        project_id = ""
        try:
            project_id = self._create_project(request)
            analysis = self._analyze_story(request.story_text, request.genre, request.tone)
            self._transactional_import(project_id, analysis)
            return StoryImportResponse(
                project_id=project_id,
                status="completed",
                message=f"Successfully imported story into project '{analysis.project_name}'",
                warnings=[],
            )
        except StoryImportError as exc:
            return StoryImportResponse(
                project_id=project_id,
                status="failed",
                message=str(exc),
                warnings=["Import failed - partial data may exist on retry"],
            )
        except InferenceBackendError as exc:
            return StoryImportResponse(
                project_id=project_id,
                status="failed",
                message=f"LLM service unavailable: {exc.code}",
                warnings=["Retry the import when the inference service is available"],
            )
```

**Key decisions**:
- `StoryImportError(ValueError)` — inherits ValueError so HTTP layer can catch it as 400
- `InferenceBackendError` — caught separately, returns `status="failed"` (not HTTP error)
- `project_id = ""` — tracks the project_id for error response (empty string = project not created yet)

---

### Task 1.2: Implement `_create_project` method

**Method signature**:
```python
def _create_project(self, request: StoryImportRequest) -> str:
    """Create project if needed, return project_id."""
```

**Logic**:
1. If `request.project_id` is provided:
   - Call `self._project_service.get_project(request.project_id)` to validate it exists
   - If raises (project not found), raise `StoryImportError("Project not found: {request.project_id}")`
   - Return `request.project_id`
2. If `request.project_id` is None:
   - Import `ProjectCreateRequest` from `app.schemas.projects`
   - Create `ProjectCreateRequest(project_name=request.project_name)`
   - Call `self._project_service.create_project(create_request)`
   - Return `response.project_id`

**Reference**: `ProjectService.create_project()` in `app/services/projects.py:30`
- Returns `ProjectDetailResponse` with `project_id` field
- Creates `data/projects/{project_id}/` directory with manifest.json, bible.db, etc.

---

### Task 1.3: Implement `_analyze_story` method + JSON parsing

**Method signature**:
```python
def _analyze_story(self, story_text: str, genre_hint: str | None, tone_hint: str | None) -> StoryImportAnalysis:
    """Call LLM to analyze story and extract structured data."""
```

**Logic**:
1. Truncate `story_text` to 24,000 chars: `story_text[:24_000]`
2. Build `InferenceRequest` using `build_import_analysis_request()`:
   ```python
   inference_request = build_import_analysis_request(
       story_text=truncated_text,
       genre_hint=genre_hint,
       tone_hint=tone_hint,
       default_model=self._inferencer.descriptor.default_model,
   )
   ```
3. Call LLM:
   ```python
   try:
       response = self._inferencer.generate_text(inference_request)
   except InferenceBackendError:
       raise  # Re-raise so import_story catches it
   ```
4. Parse JSON from `response.content`:
   ```python
   parsed = self._parse_llm_json(response.content)
   ```
5. Validate against schema:
   ```python
   return StoryImportAnalysis.model_validate(parsed)
   ```

**`_parse_llm_json` implementation**:
```python
    def _parse_llm_json(self, content: str) -> dict[str, Any]:
        """Extract JSON from LLM response.

        Handles:
        - Raw JSON object
        - JSON inside ```json code fences
        - JSON with trailing text/garbage
        - JSON with leading text/garbage
        """
        stripped = content.strip()

        # Try direct parse first
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass

        # Strip markdown code fences
        fenced = re.sub(r'^```(?:json)?\s*|\s*```$', '', stripped, flags=re.MULTILINE)
        fenced = fenced.strip()
        if fenced:
            try:
                return json.loads(fenced)
            except (json.JSONDecodeError, ValueError):
                pass

        # Find first { and last } in content
        first_brace = stripped.find('{')
        last_brace = stripped.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidate = stripped[first_brace : last_brace + 1]
            try:
                return json.loads(candidate)
            except (json.JSONDecodeError, ValueError):
                pass

        raise StoryImportError("Failed to parse LLM response as JSON")
```

---

### Task 1.4: Implement `_transactional_import` method

**Method signature**:
```python
    def _transactional_import(
        self,
        project_id: str,
        analysis: StoryImportAnalysis,
    ) -> None:
        """Execute entire entity creation in a single database transaction."""
```

**CRITICAL: Use raw SQL with a single connection — DO NOT use repo methods**

**Exact SQL statements** (from `app/persistence/story_development.py`):

**1. Foundation revision** (3 operations — header + revision + update):
```python
now = datetime.now(timezone.utc).isoformat()
now_dt = datetime.now(timezone.utc)

# 1a. Insert foundation_profiles header
conn.execute(
    """
    INSERT INTO foundation_profiles (project_id, current_revision_id, created_at, updated_at)
    VALUES (?, NULL, ?, ?)
    ON CONFLICT(project_id) DO UPDATE SET updated_at = excluded.updated_at
    """,
    (project_id, now, now),
)

# 1b. Insert foundation_revisions row
# Get next revision number
rev_row = conn.execute(
    "SELECT COALESCE(MAX(revision_number), 0) + 1 FROM foundation_revisions WHERE project_id = ?",
    (project_id,),
).fetchone()
next_rev = rev_row[0]

narrative_constraints_json = json.dumps(list(analysis.narrative_constraints or []), ensure_ascii=True, sort_keys=True)

conn.execute(
    """
    INSERT INTO foundation_revisions (
        project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
        tone_direction, target_audience, narrative_constraints_json, complexity_level,
        success_definition, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        project_id,
        next_rev,
        analysis.premise,
        analysis.logline,
        analysis.thematic_spine or None,
        analysis.emotional_promise or None,
        analysis.tone or None,
        analysis.target_audience or None,
        narrative_constraints_json,
        analysis.complexity_level or None,
        analysis.success_definition or None,
        now,
        now,
    ),
)

# 1c. Update foundation_profiles.current_revision_id
revision_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
conn.execute(
    "UPDATE foundation_profiles SET current_revision_id = ?, updated_at = ? WHERE project_id = ?",
    (revision_id, now, project_id),
)
```

**2. Characters** (using ON CONFLICT for idempotency, hash-based IDs):
```python
for char_data in analysis.characters:
    char_id = _hash_id("character", char_data.name)
    contradictions_json = json.dumps(char_data.contradictions or [], ensure_ascii=True, sort_keys=True)
    secrets_json = json.dumps(char_data.secrets or [], ensure_ascii=True, sort_keys=True)
    values_json = json.dumps(char_data.values or [], ensure_ascii=True, sort_keys=True)
    taboos_json = json.dumps(char_data.taboos or [], ensure_ascii=True, sort_keys=True)
    continuity_facts_json = json.dumps(char_data.continuity_facts or [], ensure_ascii=True, sort_keys=True)

    conn.execute(
        """
        INSERT INTO character_profiles (
            character_id, project_id, display_name, role_in_story, archetype,
            external_goal, internal_need, misbelief_or_wound, core_fear,
            primary_strength, fatal_flaw_or_limitation, contradictions_json,
            backstory_summary, voice_notes, relationship_map_json, secrets_json,
            values_json, taboos_json, change_axis, arc_stage_notes,
            continuity_facts_json, writer_notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(character_id) DO UPDATE SET
            project_id = excluded.project_id,
            display_name = excluded.display_name,
            role_in_story = excluded.role_in_story,
            archetype = excluded.archetype,
            external_goal = excluded.external_goal,
            internal_need = excluded.internal_need,
            misbelief_or_wound = excluded.misbelief_or_wound,
            core_fear = excluded.core_fear,
            primary_strength = excluded.primary_strength,
            fatal_flaw_or_limitation = excluded.fatal_flaw_or_limitation,
            contradictions_json = excluded.contradictions_json,
            backstory_summary = excluded.backstory_summary,
            voice_notes = excluded.voice_notes,
            relationship_map_json = excluded.relationship_map_json,
            secrets_json = excluded.secrets_json,
            values_json = excluded.values_json,
            taboos_json = excluded.taboos_json,
            change_axis = excluded.change_axis,
            arc_stage_notes = excluded.arc_stage_notes,
            continuity_facts_json = excluded.continuity_facts_json,
            writer_notes = excluded.writer_notes,
            updated_at = excluded.updated_at
        """,
        (
            char_id,
            project_id,
            char_data.name,
            char_data.role or None,
            char_data.archetype or None,
            char_data.external_goal or None if char_data.external_goal != "" else None,
            char_data.internal_need or None if char_data.internal_need != "" else None,
            None,  # misbelief_or_wound - not in schema
            char_data.core_fear or None if char_data.core_fear != "" else None,
            char_data.primary_strength or None if char_data.primary_strength != "" else None,
            char_data.fatal_flaw or None if char_data.fatal_flaw != "" else None,
            contradictions_json,
            char_data.backstory or None if char_data.backstory != "" else None,
            char_data.voice_notes or None if char_data.voice_notes != "" else None,
            json.dumps([], ensure_ascii=True, sort_keys=True),  # relationship_map_json
            secrets_json,
            values_json,
            taboos_json,
            char_data.change_axis or None if char_data.change_axis != "" else None,
            None,  # arc_stage_notes - not in schema
            continuity_facts_json,
            None,  # writer_notes - not in schema
            now,
            now,
        ),
    )
```

**3. World Bible entries** (using ON CONFLICT on (project_id, entry_type, title)):
```python
for entry in analysis.world_bible:
    canonical_facts_json = json.dumps(entry.canonical_facts or [], ensure_ascii=True, sort_keys=True)
    related_chars_json = json.dumps(entry.related_character_ids or [], ensure_ascii=True, sort_keys=True)
    source_artifacts_json = json.dumps([], ensure_ascii=True, sort_keys=True)
    continuity_warnings_json = json.dumps([], ensure_ascii=True, sort_keys=True)

    conn.execute(
        """
        INSERT INTO world_bible_entries (
            project_id, entry_type, title, summary, canonical_facts_json,
            related_character_ids_json, visibility_scope, source_artifacts_json,
            continuity_warnings_json, writer_notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_id, entry_type, title) DO UPDATE SET
            summary = excluded.summary,
            canonical_facts_json = excluded.canonical_facts_json,
            related_character_ids_json = excluded.related_character_ids_json,
            visibility_scope = excluded.visibility_scope,
            source_artifacts_json = excluded.source_artifacts_json,
            continuity_warnings_json = excluded.continuity_warnings_json,
            writer_notes = excluded.writer_notes,
            updated_at = excluded.updated_at
        """,
        (
            project_id,
            entry.entry_type,
            entry.title,
            entry.summary if entry.summary else None,
            canonical_facts_json,
            related_chars_json,
            "project",
            source_artifacts_json,
            continuity_warnings_json,
            None,
            now,
            now,
        ),
    )
```

**4. Arc candidates** (using ON CONFLICT on arc_id, hash-based IDs):
```python
for arc_data in analysis.story_arcs:
    arc_id = _hash_id("arc", arc_data.name)
    stage_map_json = json.dumps(arc_data.stage_map or [], ensure_ascii=True, sort_keys=True)
    fit_notes_json = json.dumps([], ensure_ascii=True, sort_keys=True)
    tags_json = json.dumps(arc_data.tags or [], ensure_ascii=True, sort_keys=True)

    conn.execute(
        """
        INSERT INTO arc_candidates (
            arc_id, project_id, name, summary, stage_map_notes_json,
            fit_notes_json, tags_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(arc_id) DO UPDATE SET
            project_id = excluded.project_id,
            name = excluded.name,
            summary = excluded.summary,
            stage_map_notes_json = excluded.stage_map_notes_json,
            fit_notes_json = excluded.fit_notes_json,
            tags_json = excluded.tags_json,
            updated_at = excluded.updated_at
        """,
        (
            arc_id,
            project_id,
            arc_data.name,
            arc_data.summary if arc_data.summary else None,
            stage_map_json,
            fit_notes_json,
            tags_json,
            now,
            now,
        ),
    )
```

**Transaction wrapper**:
```python
from datetime import datetime, timezone

conn = sqlite3.connect(self._repository.db_path, timeout=30)
try:
    conn.execute("BEGIN")
    # ... all the INSERT/UPDATE statements above ...
    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
```

**Important mapping notes**:
- `StoryImportCharacterRequest` fields that don't map to DB columns: `misbelief_or_wound` (has no direct DB column, stored in field but DB column is `misbelief_or_wound` — actually it DOES map), `writer_notes` (DB has it but empty from schema)
- `fatal_flaw_or_limitation` maps from `fatal_flaw`
- Empty string fields from schema should be stored as `NULL` (not empty strings)
- JSON columns: use `json.dumps(list, ensure_ascii=True, sort_keys=True)` pattern

---

### Task 1.5: Create `build_import_analysis_request()` in `app/services/runtime_prompts.py`

**File**: `app/services/runtime_prompts.py` (MODIFY)

**Add at end of file, before helper functions**:
```python
def build_import_analysis_request(
    *,
    story_text: str,
    genre_hint: str | None = None,
    tone_hint: str | None = None,
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for story analysis/structure extraction.

    The LLM should return a JSON object matching StoryImportAnalysis structure.
    Uses temperature=0.1 for deterministic output.
    max_tokens=16000 to fit full JSON output.
    Truncates story_text to 24,000 chars for single-pass analysis.
    """
    truncated_text = story_text[:24_000]
    context_parts = []
    if genre_hint:
        context_parts.append(f"Genre hint: {genre_hint}")
    if tone_hint:
        context_parts.append(f"Tone hint: {tone_hint}")
    context = "\n".join(context_parts)

    system_prompt = (
        "You are a story analysis AI for Narrative-Engine. You analyze completed stories "
        "and extract structured metadata that fills out all project elements.\n\n"
        "Your output MUST be valid JSON with these exact top-level keys:\n"
        "- project_name (string, required)\n"
        "- genre (string, required)\n"
        "- tone (string, required)\n"
        "- pov (string: FIRST, SECOND, THIRD_LIMITED, THIRD_OMNI, THIRD_OBJECTIVE, THIRD_MULTIPLE, OTHER)\n"
        "- story_structure (string: SAVE_THE_CAT, THREE_ACT, HERO_JOURNEY, FREYTAGS_PYRAMID, KISHOTENKETSU, FICHTEAN_CURVE, SEVEN_POINT_STRUCTURE, SEVEN_KEY_STEPS, SNOWFLAKE_METHOD, BRAINDUMP, OTHER)\n"
        "- premise (string, required)\n"
        "- logline (string, required)\n"
        "- thematic_spine (string, required)\n"
        "- emotional_promise (string, required)\n"
        "- target_audience (string, required)\n"
        "- complexity_level (string, required: LOW, MEDIUM, HIGH)\n"
        "- characters (array of objects: each with name, role, archetype, external_goal, internal_need, core_fear, primary_strength, fatal_flaw, backstory, voice_notes, change_axis, contradictions, secrets, values, taboos, continuity_facts)\n"
        "- world_bible (array of objects: each with entry_type, title, summary, canonical_facts, related_character_ids)\n"
        "- story_arcs (array of objects: each with name, summary, stage_map, tags)\n"
        "- sequences (array of objects: each with title, summary, chapters)\n"
        "- narrative_constraints (array of strings)\n"
        "- success_definition (string)\n"
        "- raw_story_text (string)\n\n"
        "CRITICAL: Return ONLY the JSON object. No markdown, no explanation, no code blocks."
    )

    user_content = f"Analyze this completed story and extract all structured metadata:\n\n{truncated_text}"
    if context:
        user_content += f"\n\nAdditional context:\n{context}"

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "story_import",
            "role": "import_analyzer",
        },
    )
```

**Note**: This function is different from existing `build_p100_architect_request` etc. because:
- Existing functions take `manifest: Manifest` (requires a project)
- This function takes raw `story_text` (no project exists yet)
- Uses `messages` list format (same as existing)
- Returns `InferenceRequest` with `temperature=0.1` (deterministic), `max_tokens=16000`

---

### Task 1.6: Implement `_parse_llm_json` helper + refine error handling

**Already included in Task 1.3 above** — the `_parse_llm_json` method with:
1. Direct `json.loads()` attempt
2. Markdown code fence stripping with regex
3. First `{` ... last `}` extraction
4. Raise `StoryImportError` if all fail

**Also add validation in `_analyze_story`**:
```python
if not analysis.characters or len(analysis.characters) == 0:
    raise StoryImportError("LLM analysis returned no characters")
```

---

## Phase 2: API Endpoint — 3 tasks

### Task 2.1: Add import endpoint to `app/api/projects.py`

**File**: `app/api/projects.py` (MODIFY)

**Changes**:
1. Add import for `StoryImportService` and `StoryImportRequest`/`StoryImportResponse`
2. Update `build_projects_router` signature to accept `import_service`
3. Add `POST /import-story` endpoint

**Exact code**:
```python
def build_projects_router(
    project_service: ProjectService,
    import_service: StoryImportService | None = None,
) -> APIRouter:
    from ..schemas.story_import import StoryImportRequest, StoryImportResponse
    from ..services.story_import import StoryImportService as _StoryImportService

    router = APIRouter(prefix="/projects", tags=["projects"])

    # ... existing endpoints unchanged ...

    if import_service is not None:
        @router.post("/import-story", response_model=StoryImportResponse, status_code=201)
        def import_story(request: StoryImportRequest) -> StoryImportResponse:
            try:
                return import_service.import_story(request)
            except StoryImportError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except Exception as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc

    return router
```

**Reference**: `build_projects_router(project_service)` currently on line 19.
**Key**: `if import_service is not None` guard for backward compatibility (tests that don't need import service).

---

### Task 2.2: Wire in `app/api/__init__.py`

**File**: `app/api/__init__.py` (MODIFY)

**Changes**: No changes needed here. The `build_projects_router` function is already exported.
The only change is that its signature now accepts an optional second parameter.

---

### Task 2.3: Wire in `app/main.py`

**File**: `app/main.py` (MODIFY)

**Changes in `build_app()` function**:

1. After `project_service = ProjectService(settings.root_dir)` (line 255), add:
```python
    from .services.story_import import StoryImportService
    import_service = StoryImportService(
        project_service=project_service,
        repository=story_development_repository,
        inferencer=inferencer,
    )
```

2. Update the router registration line (line 449):
```python
    # Before:
    app.include_router(build_projects_router(project_service))
    # After:
    app.include_router(build_projects_router(project_service, import_service=import_service))
```

---

## Phase 3: Tests — 5 tasks (10 test functions)

### Task 3.1: Create test file + fake inference backend

**File**: `tests/test_story_import_service.py` (NEW)

**Pattern**: Follow `test_local_executor_architect_runtime.py` exactly for fake inference backend.

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.inference.base import InferenceBackend, InferenceBackendError
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.inference import (
    InferenceProviderDescriptor,
    InferenceRequest,
    InferenceResponse,
    InferenceUsage,
)
from app.schemas.story_import import StoryImportRequest, StoryImportResponse
from app.services.projects import ProjectService
from app.services.story_import import StoryImportError, StoryImportService


class FakeImportInferenceBackend(InferenceBackend):
    """Returns a fixed JSON response for import analysis."""

    def __init__(self, *, content: str, model: str = "import-fake-model") -> None:
        self.requests: list[InferenceRequest] = []
        self._content = content
        self._model = model
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Import Backend",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model=model,
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["fake-import"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        return InferenceResponse(
            backend="openai_compatible",
            model=request.model,
            content=self._content,
            finish_reason="stop",
            usage=InferenceUsage(prompt_tokens=101, completion_tokens=202, total_tokens=303),
            raw_response={"backend": "fake", "backend_version": "2026.03"},
        )


def _make_json_response(
    project_name: str = "Test Story",
    genre: str = "fantasy",
    tone: str = "dark",
    pov: str = "THIRD_LIMITED",
    structure: str = "THREE_ACT",
    characters: list[dict] | None = None,
) -> str:
    """Helper to generate a valid LLM JSON response."""
    if characters is None:
        characters = [
            {
                "name": "Aria",
                "role": "protagonist",
                "archetype": "hero",
                "external_goal": "Save the kingdom",
                "internal_need": "Find belonging",
                "core_fear": "Being forgotten",
                "primary_strength": "Courage",
                "fatal_flaw": "Recklessness",
                "backstory": "A peasant raised by knights",
                "voice_notes": "Direct, earnest",
                "change_axis": "From naive to wise leader",
            }
        ]
    return json.dumps({
        "project_name": project_name,
        "genre": genre,
        "tone": tone,
        "pov": pov,
        "story_structure": structure,
        "premise": "A hero saves the world from darkness",
        "logline": "One hero against all odds",
        "thematic_spine": "Courage over fear",
        "emotional_promise": "Satisfying victory",
        "target_audience": "Young adults",
        "complexity_level": "MEDIUM",
        "characters": characters,
        "world_bible": [
            {
                "entry_type": "location",
                "title": "The Kingdom",
                "summary": "A magical kingdom in peril",
            }
        ],
        "story_arcs": [
            {"name": "Hero's Journey", "summary": "Classic hero's journey arc"}
        ],
        "sequences": [
            {"title": "Act 1", "summary": "The beginning", "chapters": ["Chapter 1"]}
        ],
        "narrative_constraints": [],
        "success_definition": "Satisfying ending",
        "raw_story_text": "",
    })
```

---

### Task 3.2: Test 1 — Happy path: `test_import_story_creates_project_and_all_entities`

```python
def test_import_story_creates_project_and_all_entities(tmp_path: Path) -> None:
    # 1. Setup
    json_content = _make_json_response()
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(
        project_name="Test Story",
        story_text="Once upon a time in a kingdom far away...",
    )
    response = import_service.import_story(request)

    # 3. Assert response
    assert response.status == "completed"
    assert response.project_id is not None
    assert "Successfully imported" in response.message

    # 4. Assert project exists
    project = project_service.get_project(response.project_id)
    assert project.project_name == "Test Story"

    # 5. Assert foundation created
    foundation_revisions = repository.list_foundation_revisions(response.project_id)
    assert len(foundation_revisions) == 1
    assert foundation_revisions[0].premise == "A hero saves the world from darkness"
    assert foundation_revisions[0].logline == "One hero against all odds"

    # 6. Assert character created
    characters = repository.list_character_profiles(response.project_id)
    assert len(characters) == 1
    assert characters[0].display_name == "Aria"
    assert characters[0].role_in_story == "protagonist"

    # 7. Assert world bible entry created
    bible_entries = repository.list_world_bible_entries(response.project_id)
    assert len(bible_entries) == 1
    assert bible_entries[0].title == "The Kingdom"
    assert bible_entries[0].entry_type == "location"

    # 8. Assert arc created
    arcs = repository.list_arc_candidates(response.project_id)
    assert len(arcs) == 1
    assert arcs[0].name == "Hero's Journey"

    # 9. Assert LLM was called with correct params
    assert len(inferencer.requests) == 1
    req = inferencer.requests[0]
    assert req.temperature == 0.1
    assert req.max_tokens == 16000
    assert req.messages[0].role == "system"
    assert req.messages[1].role == "user"
```

---

### Task 3.3: Test 2 — `test_import_story_with_existing_project_id`

```python
def test_import_story_with_existing_project_id(tmp_path: Path) -> None:
    # 1. Setup: Create project first
    project_service = ProjectService(tmp_path)
    create_resp = project_service.create_project(
        type("ProjectCreateRequest", (), {"project_name": "Existing Project"})()
    )
    project_id = create_resp.project_id

    # 2. Setup: Create import service
    json_content = _make_json_response()
    inferencer = FakeImportInferenceBackend(content=json_content)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 3. Act
    request = StoryImportRequest(
        project_name="Existing Project",
        story_text="Long ago...",
        project_id=project_id,
    )
    response = import_service.import_story(request)

    # 4. Assert
    assert response.status == "completed"
    assert response.project_id == project_id

    # 5. Assert entities created in existing project
    characters = repository.list_character_profiles(project_id)
    assert len(characters) >= 1
```

---

### Task 3.4: Test 3 — `test_import_story_rejects_invalid_project_id`

```python
def test_import_story_rejects_invalid_project_id(tmp_path: Path) -> None:
    # 1. Setup
    inferencer = FakeImportInferenceBackend(content=_make_json_response())
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(
        project_name="Test",
        story_text="Once upon a time...",
        project_id="nonexistent-uuid-0000",
    )
    response = import_service.import_story(request)

    # 3. Assert
    assert response.status == "failed"
    assert "not found" in response.message.lower() or "invalid" in response.message.lower()
```

---

### Task 3.5: Test 4, 5, 6 — JSON parsing and LLM errors

```python
def test_import_story_handles_malformed_json(tmp_path: Path) -> None:
    """Malformed JSON that can't be extracted should fail gracefully."""
    inferencer = FakeImportInferenceBackend(content="this is not json at all")
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    request = StoryImportRequest(project_name="Test", story_text="story...")
    response = import_service.import_story(request)

    assert response.status == "failed"
    assert "JSON" in response.message or "parse" in response.message.lower()


def test_import_story_handles_markdown_code_fences(tmp_path: Path) -> None:
    """LLM wraps JSON in ```json fences — should extract successfully."""
    wrapped = "```json\n" + _make_json_response() + "\n```"
    inferencer = FakeImportInferenceBackend(content=wrapped)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    request = StoryImportRequest(project_name="Test", story_text="story...")
    response = import_service.import_story(request)

    assert response.status == "completed"
    characters = repository.list_character_profiles(response.project_id)
    assert len(characters) >= 1


def test_import_story_handles_inference_backend_error(tmp_path: Path) -> None:
    """InferenceBackendError should return status='failed' without raising."""
    from app.inference.base import InferenceBackendError

    class FailingInferenceBackend(InferenceBackend):
        @property
        def descriptor(self) -> InferenceProviderDescriptor:
            return InferenceProviderDescriptor(
                backend="stub", display_name="Failing", transport="stub",
                default_model="fail-model", timeout_seconds=30.0,
            )

        def generate_text(self, request: InferenceRequest) -> InferenceResponse:
            raise InferenceBackendError(
                "Service unavailable",
                category="timeout",
                code="SERVICE_UNAVAILABLE",
                finish_reason="timeout",
                retryable=True,
            )

    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=FailingInferenceBackend(),
    )

    request = StoryImportRequest(project_name="Test", story_text="story...")
    response = import_service.import_story(request)

    assert response.status == "failed"
    assert "unavailable" in response.message.lower() or "SERVICE_UNAVAILABLE" in response.message
```

---

### Task 3.6: Test 7, 8, 9, 10 — Edge cases and truncation

```python
def test_import_story_handles_trailing_text(tmp_path: Path) -> None:
    """JSON followed by explanatory text should still parse."""
    json_content = _make_json_response()
    wrapped = json_content + "\n\nHope this helps!"
    inferencer = FakeImportInferenceBackend(content=wrapped)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    request = StoryImportRequest(project_name="Test", story_text="story...")
    response = import_service.import_story(request)

    assert response.status == "completed"


def test_import_story_is_idempotent_on_retry(tmp_path: Path) -> None:
    """Re-importing the same story should use ON CONFLICT DO UPDATE."""
    json_content = _make_json_response(project_name="Idempotent Test")
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    request = StoryImportRequest(
        project_name="Idempotent Test",
        story_text="First import...",
    )
    first_response = import_service.import_story(request)
    assert first_response.status == "completed"

    # Re-import same story text
    request.story_text = "Second import of same story..."
    second_response = import_service.import_story(request)
    assert second_response.status == "completed"

    # Characters should still be 1 (not duplicated)
    characters = repository.list_character_profiles(first_response.project_id)
    assert len(characters) == 1


def test_import_story_story_text_truncation(tmp_path: Path) -> None:
    """Story text > 24K chars should be truncated before sending to LLM."""
    long_story = "A" * 30_000
    json_content = _make_json_response()
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    request = StoryImportRequest(project_name="Test", story_text=long_story)
    response = import_service.import_story(request)

    assert response.status == "completed"

    # Verify the LLM was called with truncated text
    req = inferencer.requests[0]
    user_content = req.messages[1].content
    # Should contain the story text (truncated) but not the full 30K chars
    assert len(user_content) < 30_000


def test_import_story_handles_missing_fields(tmp_path: Path) -> None:
    """LLM response missing required characters field should fail."""
    incomplete = json.dumps({
        "project_name": "Incomplete",
        "genre": "fantasy",
        "tone": "dark",
        "pov": "THIRD_LIMITED",
        "story_structure": "THREE_ACT",
        "premise": "A story",
        "logline": "A logline",
        "thematic_spine": "Theme",
        "emotional_promise": "Feeling",
        "target_audience": "Everyone",
        "complexity_level": "MEDIUM",
        "characters": [],  # Empty characters array
        "narrative_constraints": [],
    })
    inferencer = FakeImportInferenceBackend(content=incomplete)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    request = StoryImportRequest(project_name="Test", story_text="story...")
    response = import_service.import_story(request)

    assert response.status == "failed"
    assert "characters" in response.message.lower() or "min" in response.message.lower()
```

---

## Phase 4: Validation — 1 task

### Task 4.1: Run full validation suite

**Commands** (run from project root):
```bash
# 1. Backend tests
uv run pytest tests/test_story_import_service.py -v

# 2. Full test suite
uv run pytest -q -p no:cacheprovider

# 3. Format
uv run black .

# 4. Frontend checks
cd frontend && npm run lint && npm run typecheck && npm run build
```

**Expected result**:
- `test_story_import_service.py`: 10 tests pass
- Full suite: 554 + 10 = ~564 tests pass
- No lint/typecheck/build errors

---

## Summary

| Phase | Tasks | Time |
|-------|-------|------|
| 1. Foundation (Service) | 1.1-1.6 (6 sub-tasks) | 1.5 hours |
| 2. API Endpoint | 2.1-2.3 (3 tasks) | 1.0 hour |
| 3. Tests | 3.1-3.6 (6 sub-tasks, 10 tests) | 2.5 hours |
| 4. Validation | 4.1 (1 task) | 0.5 hours |
| **Total** | **15 tasks** | **~5.5 hours** |
