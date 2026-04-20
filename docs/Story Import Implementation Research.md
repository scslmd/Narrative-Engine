# Story Import Feature - Implementation Research & Design

> This document captures the full implementation research for the Story Import feature.
> Written: April 2026
> Reference: `docs/Story Import Research & Architecture.md` (high-level overview)
> Status: Research complete, adversarial plan approved, ready for implementation

## 1. Feature Overview

**Goal**: Allow users to paste/upload an existing completed story, then have the LLM review, classify, and "fill out all the blanks" (create the full project structure including foundation, characters, world bible, arcs, planning, and drafts) in one automated workflow.

**Entry Point**: `POST /v1/projects/import-story` - accepts `project_name`, `story_text`, optional `project_id`
**Response**: **201 Created** with `project_id`, `status: "completed"` or `status: "failed"`
**Processing**: Synchronous in-process via `StoryImportService` (like `ManuscriptReviewService`), NOT via the job system. The HTTP request blocks while the LLM analyzes and data is persisted.

**Existing Schema**: `app/schemas/story_import.py` already defines request/response models:
- `StoryImportRequest` (project_name, story_text, optional project_id/genre/tone)
- `StoryImportResponse` (project_id, status, message, warnings)
- `StoryImportAnalysis` (full parsed JSON structure for LLM output)
- `StoryImportCharacterRequest`, `StoryImportWorldEntry`, `StoryImportArc`, `StoryImportSequence`

## 2. Architecture Decision: Direct Service vs Job System

**Decision**: Use direct service (NOT the job system).

**Rationale**:
- Only job phases P-100 to P-400 exist; no custom phases allowed
- Import is fundamentally different from P-100..P-400 (it's a multi-step extraction + creation flow, not a pipeline phase)
- `ManuscriptReviewService` is the pattern to follow: uses `InferenceBackend` directly, no job system
- The job system is designed for sequential phases with file-based artifacts; import needs atomic transactional creation

## 3. Adversarial Review Findings & Corrections

The original research had several critical issues that were identified through adversarial review of the codebase and flow logic. The following corrections have been applied:

### Finding 1: Status Code Misalignment
**Original Research**: Return 202 Accepted for async processing.
**Correction**: Return **201 Created** for success. The service is **synchronous** (blocks HTTP request). The "processing" status field is misleading since there's no actual async background processing. `ManuscriptReviewService` returns results directly, not 202.

**Evidence**: `POST /projects/create` in `app/api/projects.py:22` returns 201. `StoryImportResponse.status` should be `"completed"` or `"failed"`, not `"processing"`.

### Finding 2: Transaction Management - `BEGIN IMMEDIATE` is Wrong
**Original Research**: Use `BEGIN IMMEDIATE` on raw SQLite connection.
**Correction**: Use **`BEGIN`** (not `BEGIN IMMEDIATE`) on a single direct connection, executing all SQL statements without using the repository wrapper methods.

**Evidence**: `StoryDevelopmentRepository` methods each use `with connect(self.db_path)` which opens new connections. Using `BEGIN IMMEDIATE` on one connection while repo methods use their own connections creates a race condition. The repo methods already have `ON CONFLICT DO UPDATE` support. The import service must use **one direct connection** that executes all SQL directly, not via repo methods.

**Implementation**: 
```python
conn = sqlite3.connect(db_path, timeout=30)
conn.execute("BEGIN")
try:
    # Direct INSERT statements for all entities
    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
```

### Finding 3: Service Dependency Injection Not Present
**Original Research**: `import_service: StoryImportService` parameter in FastAPI route function.
**Correction**: FastAPI in this codebase does **NOT** use dependency injection for services. Services are created in `build_app()` and passed to router builders.

**Evidence**: `build_projects_router(project_service)` takes `project_service` as constructor parameter. The service is created once during router construction, not per-request.

**Implementation**: Add `import_service` parameter to `build_projects_router(project_service, import_service=None)`, create `StoryImportService` in `build_app()`, pass it to the router.

### Finding 4: Project Creation Flow Ambiguity
**Original Research**: Unclear whether to use `ProjectService.create_project()` or call `initialize_project_artifacts()` directly.
**Correction**: Use `ProjectService.create_project()` for new projects, skip to entity creation when reusing an existing `project_id`.

**Evidence**: `ProjectService.create_project()` calls `initialize_project_artifacts()` + `repository.register_project_dir()`. Reusing the existing method avoids duplication.

### Finding 5: Runtime Prompts Pattern Mismatch
**Original Research**: `build_import_analysis_request(manifest, payload, default_model)` following existing patterns.
**Correction**: Import has **no manifest** (project may not exist yet). Function signature must be different:

```python
def build_import_analysis_request(
    *,
    story_text: str,
    genre_hint: str | None = None,
    tone_hint: str | None = None,
    default_model: str | None,
) -> InferenceRequest:
```

**Evidence**: Existing functions take `manifest: Manifest` which requires a project. The import analysis happens before project foundation is created.

## 4. System Components to Create

### 4.1 `app/services/story_import.py` - StoryImportService

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
        1. Validate request (text length, project_id)
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

### 4.2 `app/api/projects.py` - Import Endpoint

**Correction**: Service is passed via router construction, NOT FastAPI DI.

```python
def build_projects_router(
    project_service: ProjectService,
    import_service: StoryImportService | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["projects"])

    # ... existing endpoints ...

    if import_service is not None:
        @router.post("/import-story", response_model=StoryImportResponse, status_code=201)
        def import_story(request: StoryImportRequest) -> StoryImportResponse:
            try:
                return import_service.import_story(request)
            except StoryImportError as exc:
                raise HTTPException(status_code=400, detail=str(exc))
            except Exception as exc:
                raise HTTPException(status_code=500, detail=str(exc))

    return router
```

### 4.3 `app/services/runtime_prompts.py` - Import Prompt Builder

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

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are a story analysis AI for Narrative-Engine. Analyze completed stories "
                    "and extract structured metadata. Return ONLY valid JSON. No markdown, no explanation."
                ),
            ),
            InferenceMessage(
                role="user",
                content=(
                    f"Analyze this completed story and extract all structured metadata:\n\n"
                    f"{truncated_text}"
                    f"\n\n{'Additional context: ' + context if context else ''}"
                ),
            ),
        ],
        metadata={
            "mode": "story_import",
            "role": "import_analyzer",
        },
    )
```

## 5. Prompt Design

### 5.1 System Prompt

```
You are a story analysis AI for Narrative-Engine. You analyze completed stories
and extract structured metadata that fills out all project elements.

Your output MUST be valid JSON with these exact top-level keys:
- project_name (string, required)
- genre (string, required)
- tone (string, required)
- pov (string: FIRST, SECOND, THIRD_LIMITED, THIRD_OMNI, THIRD_OBJECTIVE, THIRD_MULTIPLE, OTHER)
- story_structure (string: SAVE_THE_CAT, THREE_ACT, HERO_JOURNEY, FREYTAGS_PYRAMID, KISHOTENKETSU, FICHTEAN_CURVE, SEVEN_POINT_STRUCTURE, SEVEN_KEY_STEPS, SNOWFLAKE_METHOD, BRAINDUMP, OTHER)
- premise (string, required, up to 10000 chars)
- logline (string, required, up to 500 chars)
- thematic_spine (string, required, up to 2000 chars)
- emotional_promise (string, required, up to 2000 chars)
- target_audience (string, required, up to 500 chars)
- complexity_level (string, required: LOW, MEDIUM, HIGH)
- characters (array of objects, required, min 1 item, each with: name, role, archetype, external_goal, internal_need, core_fear, primary_strength, fatal_flaw, backstory, voice_notes, change_axis)
- world_bible (array of objects with: entry_type, title, summary, canonical_facts)
- story_arcs (array of objects with: name, summary, stage_map, tags)
- sequences (array of objects with: title, summary, chapters)
- narrative_constraints (array of strings)
- success_definition (string)

CRITICAL: Return ONLY the JSON object. No markdown, no explanation, no code blocks.
```

### 5.2 User Prompt

```
Analyze this completed story and extract all structured metadata:

{story_chunk}

{genre_hint}
{tone_hint}
```

## 6. Transaction Management (Adversarial Correction)

### 6.1 The Problem

`StoryDevelopmentRepository` methods each open their own connection and commit:
```python
def upsert_character_profile(self, *, character_id: str, ...) -> CharacterProfileRecord:
    with connect(self.db_path) as connection:
        connection.execute(...)
        connection.commit()
    return self.get_character_profile(character_id)
```

Creating N entities = N separate commits. If step 7 fails, steps 1-6 are already committed.

### 6.2 Corrected Solution: Single Direct Connection

**Do NOT use repo methods** during transactional import. Use a single raw SQLite connection:

```python
import sqlite3
import json

def _transactional_import(self, project_id: str, analysis: StoryImportAnalysis) -> None:
    """Execute entire entity creation in a single database transaction."""
    now = datetime.now(timezone.utc)
    conn = sqlite3.connect(self._repository.db_path, timeout=30)
    conn.execute("BEGIN")
    try:
        # 1. Foundation profile + revision
        conn.execute(
            "INSERT INTO foundation_profiles (project_id, current_revision_id, created_at, updated_at) VALUES (?, NULL, ?, ?) ON CONFLICT(project_id) DO UPDATE SET updated_at = excluded.updated_at",
            (project_id, now.isoformat(), now.isoformat()),
        )
        cursor = conn.execute(
            "INSERT INTO foundation_revisions (project_id, revision_number, premise, logline, thematic_spine, emotional_promise, tone_direction, target_audience, narrative_constraints_json, complexity_level, success_definition, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, 1, analysis.premise, analysis.logline, analysis.thematic_spine, analysis.emotional_promise, None, analysis.target_audience, json.dumps(analysis.narrative_constraints), analysis.complexity_level, analysis.success_definition, now.isoformat(), now.isoformat()),
        )
        revision_id = cursor.lastrowid
        conn.execute("UPDATE foundation_profiles SET current_revision_id = ?, updated_at = ? WHERE project_id = ?", (revision_id, now.isoformat(), project_id))

        # 2. Character profiles
        for char in analysis.characters:
            char_id = _hash_id("character", char.name)
            conn.execute(
                "INSERT INTO character_profiles (character_id, project_id, display_name, role_in_story, archetype, external_goal, internal_need, misbelief_or_wound, core_fear, primary_strength, fatal_flaw_or_limitation, contradictions_json, backstory_summary, voice_notes, relationship_map_json, secrets_json, values_json, taboos_json, change_axis, arc_stage_notes, continuity_facts_json, writer_notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (char_id, project_id, char.name, char.role, char.archetype, char.external_goal, char.internal_need, None, char.core_fear, char.primary_strength, char.fatal_flaw, json.dumps(char.contradictions), char.backstory, char.voice_notes, json.dumps([]), json.dumps(char.secrets), json.dumps(char.values), json.dumps(char.taboos), char.change_axis, None, json.dumps(char.continuity_facts), None, now.isoformat(), now.isoformat()),
            )

        # 3. World bible entries
        for i, entry in enumerate(analysis.world_bible):
            entry_id = f"bible-{entry.entry_type}-{entry.title.lower().replace(' ', '-')}"
            conn.execute(
                "INSERT INTO world_bible_entries (project_id, entry_type, title, summary, canonical_facts_json, related_character_ids_json, visibility_scope, source_artifacts_json, continuity_warnings_json, writer_notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(project_id, entry_type, title) DO UPDATE SET summary = excluded.summary, canonical_facts_json = excluded.canonical_facts_json, related_character_ids_json = excluded.related_character_ids_json, visibility_scope = excluded.visibility_scope, source_artifacts_json = excluded.source_artifacts_json, continuity_warnings_json = excluded.continuity_warnings_json, writer_notes = excluded.writer_notes, updated_at = excluded.updated_at",
                (project_id, entry.entry_type, entry.title, entry.summary, json.dumps(entry.canonical_facts), json.dumps(entry.related_character_ids), "project", json.dumps([]), json.dumps([]), None, now.isoformat(), now.isoformat()),
            )

        # 4. Arc candidates
        for i, arc in enumerate(analysis.story_arcs):
            arc_id = f"arc-{arc.name.lower().replace(' ', '-')}-{i:03d}"
            conn.execute(
                "INSERT INTO arc_candidates (arc_id, project_id, name, summary, stage_map_notes_json, fit_notes_json, tags_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(arc_id) DO UPDATE SET project_id = excluded.project_id, name = excluded.name, summary = excluded.summary, stage_map_notes_json = excluded.stage_map_notes_json, fit_notes_json = excluded.fit_notes_json, tags_json = excluded.tags_json, updated_at = excluded.updated_at",
                (arc_id, project_id, arc.name, arc.summary, json.dumps(arc.stage_map), json.dumps([]), json.dumps(arc.tags), now.isoformat(), now.isoformat()),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### 6.3 Critical Notes

- **Column names must match exactly**: Every column name must be verified against the actual repository INSERT statements in `app/persistence/story_development.py`. Characterize the columns from `upsert_character_profile`, `upsert_world_bible_entry`, `upsert_arc_candidate`, and `upsert_foundation_profile`.
- **JSON helpers**: Use inline `json.dumps(values or [], ensure_ascii=True, sort_keys=True)` since `_json_list()` is not importable from the persistence module.
- **ID generation**: SHA-256 hash-based IDs (`import-{prefix}-{hash[:12]}`) for stable, order-independent, deduplicated identity. `ON CONFLICT DO UPDATE` makes retries safe.

## 7. Error Handling & Retry Pattern

### 7.1 LLM Call Failure Handling

Pattern from `local_executor.py`:

```python
try:
    inference_response = self._inferencer.generate_text(inference_request)
except InferenceBackendError as exc:
    raise StoryImportError(f"LLM analysis failed: {exc.code}: {exc}") from exc
```

Circuit breaker is already wired into `OpenAICompatibleInferenceBackend`.

### 7.2 JSON Parsing from LLM Response

```python
def _parse_llm_json(content: str) -> dict[str, Any]:
    """Parse JSON from LLM response content.

    Handles:
    - Raw JSON string
    - Markdown code blocks (```json ... ```)
    - Trailing text after JSON
    - Empty or whitespace-only content
    """
    if not content or not content.strip():
        raise StoryImportError("LLM returned empty content.")

    content = content.strip()

    # Strip markdown code fences if present
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first and last lines (code fence markers)
        content = "\n".join(lines[1:-1]) if len(lines) > 2 else ""
        content = content.strip()

    if not content:
        raise StoryImportError("LLM returned empty JSON after stripping code fences.")

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from response (find first { and last })
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(content[start:end + 1])
            except json.JSONDecodeError:
                pass
        raise StoryImportError(f"Failed to parse LLM response as JSON: {content[:500]}...")
```

### 7.3 Pydantic Validation

```python
try:
    analysis = StoryImportAnalysis.model_validate(llm_parsed)
except ValidationError as exc:
    raise StoryImportError(f"LLM output failed validation: {exc}")
```

### 7.4 Recovery Strategy

If import fails mid-way:
1. Project is already created (via `ProjectService.create_project()` or reusing existing project)
2. Foundation/characters/world bible may be partially created
3. **Critical**: The partial data is harmless - the user can retry import on the same project
4. Each retry will overwrite (ON CONFLICT DO UPDATE) since entities use deterministic IDs
5. The transaction ensures all entities are created atomically - either all succeed or none do

### 7.5 Complete import_story Flow

```python
def import_story(self, request: StoryImportRequest) -> StoryImportResponse:
    project_id = ""
    try:
        # Step 1: Create or validate project
        project_id = self._create_project(request)

        # Step 2: Analyze story via LLM
        analysis = self._analyze_story(request.story_text, request.genre, request.tone)

        # Step 3: Import into database (transactional, all-or-nothing)
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

## 8. ID Generation Strategy

Use deterministic IDs based on content to support ON CONFLICT:

```python
def _generate_character_id(char_name: str, index: int) -> str:
    """Generate stable character ID."""
    return f"char-{char_name.lower().replace(' ', '-')}-{index:03d}"

def _generate_world_entry_id(entry_type: str, title: str) -> str:
    """Generate stable world bible entry ID."""
    return f"bible-{entry_type.lower()}-{title.lower().replace(' ', '-')}"

def _generate_arc_id(arc_name: str, index: int) -> str:
    """Generate stable arc ID."""
    return f"arc-{arc_name.lower().replace(' ', '-')}-{index:03d}"
```

**Adversarial edge case**: Two characters with the same name at different indices get different IDs (`char-aria-000`, `char-aria-001`). Two different names could collide after normalization (e.g., "John Doe" -> "char-john-doe"). The `index` suffix prevents this.

## 9. Atomic Implementation Tasks

### Phase 1: Foundation (Tasks 1-6) -- 1.5 hours

#### Task 1: Create `StoryImportService` class skeleton
**File**: `app/services/story_import.py` (NEW)
**What to implement**:
- `StoryImportError(ValueError)` base exception
- `StoryImportService` class with `__init__(self, *, project_service, repository, inferencer, root_dir=None)`
- `_normalize_text()` helper (pattern from `ManuscriptReviewService`)
- `_generate_id()` helper using `uuid.uuid4().hex[:12]`

**Verify**: File has `from __future__ import annotations`, correct import ordering, no circular imports. Run `python -c "from app.services.story_import import StoryImportService"` -- succeeds with no errors.

#### Task 2: Implement `_create_project()` method
**File**: `app/services/story_import.py`
**What to implement**:
- If `request.project_id` is None: generate new UUID, call `ProjectService.create_project()`
- If `request.project_id` is provided: call `project_service.get_project()` to validate existence
- Returns `project_id: str`

**Edge case**: If `project_id` is provided but project doesn't exist, raise `StoryImportError`.

**Verify**: No new project created when reusing existing ID.

#### Task 3: Implement `build_import_analysis_request()` in `runtime_prompts.py`
**File**: `app/services/runtime_prompts.py` (MODIFY)
**What to implement**:
```python
def build_import_analysis_request(
    *,
    story_text: str,
    genre_hint: str | None = None,
    tone_hint: str | None = None,
    default_model: str | None,
) -> InferenceRequest:
```
- Returns `InferenceRequest` with system prompt + user prompt
- System prompt: instructs LLM to return JSON matching `StoryImportAnalysis` schema
- User prompt: includes `story_text` (truncated to 24,000 chars for first chunk)
- `temperature=0.1`, `max_tokens=16000`
- `metadata={"mode": "story_import", "role": "import_analyzer"}`

**Verify**: Returns valid `InferenceRequest` with correct fields.

#### Task 4: Implement `_parse_llm_json()` and `_analyze_story()` methods
**File**: `app/services/story_import.py`
**What to implement**:
- `_parse_llm_json(content: str) -> dict`: strips markdown fences, extracts JSON, raises `StoryImportError` on failure
- `_analyze_story(story_text: str, genre_hint, tone_hint) -> StoryImportAnalysis`:
  1. Calls `build_import_analysis_request()`
  2. Calls `self._inferencer.generate_text()`
  3. Parses JSON from response
  4. Validates via `StoryImportAnalysis.model_validate()`
  5. Returns validated analysis

**Edge cases**:
- LLM returns empty content
- LLM returns non-JSON content
- LLM returns valid JSON but missing required fields
- Circuit breaker is open (catch `InferenceBackendError`)

#### Task 5: Implement `_transactional_import()` method
**File**: `app/services/story_import.py`
**What to implement**:
- Single raw SQLite connection (NOT using repo methods)
- `conn = sqlite3.connect(db_path, timeout=30)`
- `conn.execute("BEGIN")` (NOT `BEGIN IMMEDIATE`)
- Execute direct INSERT statements for:
  1. `foundation_profiles` + `foundation_revisions` (use inline `json.dumps()`, `ON CONFLICT(project_id, revision_number)`)
  2. `character_profiles` (loop, generate IDs as `_hash_id("character", name)`)
  3. `world_bible_entries` (loop, generate IDs using `ON CONFLICT(project_id, entry_type, title)`)
  4. `arc_candidates` (loop, generate IDs as `_hash_id("arc", name)`)
- `conn.commit()` on success, `conn.rollback()` on failure
- `conn.close()` in `finally`

**CRITICAL**: Must match exact column names from existing repo methods. Verify against:
- `upsert_foundation_profile` (lines 1017-1077 in story_development.py)
- `upsert_character_profile` (lines 1129-1220 in story_development.py)
- `upsert_world_bible_entry` (lines 1343-1394 in story_development.py)
- `upsert_arc_candidate` (lines 1396-1439 in story_development.py)

**Adversarial test**: Run two imports in rapid succession -- second should succeed via `ON CONFLICT DO UPDATE`.

#### Task 6: Implement `import_story()` main method
**File**: `app/services/story_import.py`
**What to implement**:
```python
def import_story(self, request: StoryImportRequest) -> StoryImportResponse:
    project_id = ""
    try:
        project_id = self._create_project(request)
        analysis = self._analyze_story(request.story_text, request.genre, request.tone)
        self._transactional_import(project_id, analysis)
        return StoryImportResponse(project_id=project_id, status="completed", message=..., warnings=[])
    except StoryImportError as exc:
        return StoryImportResponse(project_id=project_id, status="failed", message=str(exc), warnings=[...])
    except InferenceBackendError as exc:
        return StoryImportResponse(project_id=project_id, status="failed", message=..., warnings=[...])
```

**Verify**: All code paths return `StoryImportResponse`. No unhandled exceptions escape.

### Phase 2: API Endpoint (Tasks 7-9) -- 1 hour

#### Task 7: Add import endpoint to `build_projects_router()`
**File**: `app/api/projects.py` (MODIFY)
**What to implement**:
- Add `import_service` parameter to `build_projects_router(project_service, import_service=None)`
- Add `@router.post("/import-story", response_model=StoryImportResponse, status_code=201)`
- Route function calls `import_service.import_story(request)` directly
- Catches `StoryImportError` -> 400, generic `Exception` -> 500

**Adversarial**: The service is passed at router construction time, not per-request.

#### Task 8: Wire `StoryImportService` in `build_app()`
**File**: `app/main.py` (MODIFY)
**What to implement**:
- Import `StoryImportService` from `app.services.story_import`
- After creating `story_development_repository`, instantiate `StoryImportService(project_service=project_service, repository=story_development_repository, inferencer=inferencer)`
- Pass `import_service` to `build_projects_router(project_service, import_service)`

#### Task 9: Update `build_projects_router` signature in `app/api/__init__.py`
**File**: `app/api/__init__.py` (MODIFY)
**What to implement**:
- Update `build_projects_router` import signature to include `import_service` parameter
- No functional change needed here, just type signature

### Phase 3: Tests (Tasks 10-14) -- 2.5 hours

#### Task 10: Create test fixtures
**File**: `tests/test_story_import_service.py` (NEW)
**What to implement**:
- `FakeImportInferenceBackend(InferenceBackend)` -- returns configurable JSON content
- `_build_service(tmp_path, inferencer)` -- sets up `ProjectService`, `StoryDevelopmentRepository`, `StoryImportService` with `tmp_path`
- `_seed_project(db_path, project_id)` -- inserts project record
- JSON fixtures: valid analysis JSON for small story

**Pattern**: Follow `test_local_executor_architect_runtime.py` fake backend and `_build_executor` fixture patterns.

#### Task 11: Test happy path -- project creation + all entities
**Test**: `test_import_story_creates_project_and_all_entities`
- Setup: fake backend returns complete `StoryImportAnalysis` JSON
- Act: call `import_story(request)`
- Assert:
  - Response status == "completed"
  - Project exists (via `project_service.get_project()`)
  - Foundation revision exists with correct premise/logline
  - Character profiles exist with correct names/roles
  - World bible entries exist
  - Arc candidates exist
  - All entity IDs are deterministic based on content

#### Task 12: Test edge cases
**Tests**:
- `test_import_story_reuses_existing_project` -- provide existing `project_id`
- `test_import_story_rejects_invalid_project_id` -- non-existent `project_id`
- `test_import_story_handles_malformed_json` -- backend returns non-JSON
- `test_import_story_handles_missing_fields` -- backend returns JSON missing required fields
- `test_import_story_handles_inference_backend_error` -- backend raises `InferenceBackendError`

#### Task 13: Test JSON parsing
**Tests**:
- `test_parse_llm_json_handles_markdown_code_fences` -- ` ```json { ... } ``` `
- `test_parse_llm_json_handles_trailing_text` -- JSON followed by explanation
- `test_parse_llm_json_handles_raw_json` -- plain JSON
- `test_parse_llm_json_raises_on_invalid_json`

#### Task 14: Test idempotent retry
**Test**: `test_import_story_is_idempotent_on_retry`
- Act: call `import_story()` twice with same request
- Assert: second call returns "completed", no duplicate entities (character_profiles count is 1, not 2)

### Phase 4: Validation (Task 15) -- 0.5 hours

#### Task 15: Run full validation suite
**Commands**:
```bash
python -m pytest tests/test_story_import_service.py -v
python -m pytest -q -p no:cacheprovider
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
```

## 10. Token Management & Chunking Strategy

### 10.1 Challenge

- Story text can be up to 5,000,000 characters (per `StoryImportRequest.story_text` max_length)
- Typical LLM context limits: 4K-128K tokens
- ~1 token per 0.75 English word, so 5M chars ≈ 2M tokens
- Cannot fit full story in single LLM call

### 10.2 Phase 1 Approach: Truncation

**For Phase 1 only**: Truncate story text to 24,000 characters. This handles short stories (flash fiction, short stories up to ~20K words). Full chunking is deferred to Phase 2.

### 10.3 Phase 2: Two-Pass Chunking Strategy (Future)

**Pass 1: Metadata Extraction (Small Story < 24K chars)**
- Send full story in one prompt
- LLM returns complete `StoryImportAnalysis` JSON
- Fast path for short stories

**Pass 2: Chunked Analysis (Large Story >= 24K chars) -- Future**
- Split story into chunks by chapter/scene breaks or fixed 25K-char windows
- First chunk: Full analysis prompt
- Subsequent chunks: Focused extraction (characters, world entries, arcs mentioned)
- Aggregate results from all chunks
- Final pass: Resolve conflicts, deduplicate characters, merge sequences

### 10.4 Token Budget Estimation

For a single LLM call:
- System prompt: ~1500 tokens
- User prompt: truncated story (~24,000 chars ≈ 32,000 tokens)
- max_tokens for output: 16000 (for JSON)
- Total: ~33,500 tokens input + 16,000 tokens output

## 11. Test Patterns

### 11.1 Fake Inference Backend for Tests

```python
class FakeImportInferenceBackend(InferenceBackend):
    def __init__(self, *, content: str, model: str = "import-fake-model") -> None:
        self.requests: list[InferenceRequest] = []
        self._content = content
        self._model = model
        self._descriptor = InferenceProviderDescriptor(
            backend="stub",
            display_name="Fake Import Backend",
            transport="stub",
            base_url=None,
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
            backend="stub",
            model=self._model,
            content=self._content,
            finish_reason="stop",
            usage=InferenceUsage(prompt_tokens=100, completion_tokens=500, total_tokens=600),
            raw_response={},
        )
```

### 11.2 Test Structure

```python
def test_import_story_creates_project_and_all_entities(tmp_path: Path) -> None:
    # 1. Setup: Create fake inference backend with JSON response
    json_content = json.dumps({
        "project_name": "Test Story",
        "genre": "fantasy",
        "tone": "dark",
        "pov": "THIRD_LIMITED",
        "story_structure": "THREE_ACT",
        "premise": "A hero saves the world",
        "logline": "One hero against all odds",
        "thematic_spine": "courage over fear",
        "emotional_promise": "satisfying victory",
        "target_audience": "young adults",
        "complexity_level": "MEDIUM",
        "characters": [
            {"name": "Aria", "role": "protagonist", "archetype": "hero"}
        ],
        "world_bible": [
            {"entry_type": "location", "title": "The Kingdom", "summary": "A magical kingdom"}
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

    inferencer = FakeImportInferenceBackend(content=json_content)

    # 2. Setup: Create services with tmp_path
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 3. Act: Import story
    request = StoryImportRequest(
        project_name="Test Story",
        story_text="Once upon a time...",
    )
    response = import_service.import_story(request)

    # 4. Assert: Response
    assert response.status == "completed"
    assert response.project_id is not None

    # 5. Assert: Project exists
    project = project_service.get_project(response.project_id)
    assert project.project_name == "Test Story"

    # 6. Assert: Foundation created
    foundation_revisions = repository.list_foundation_revisions(response.project_id)
    assert len(foundation_revisions) == 1
    assert foundation_revisions[0].premise == "A hero saves the world"

    # 7. Assert: Character created
    characters = repository.list_character_profiles(response.project_id)
    assert len(characters) == 1
    assert characters[0].display_name == "Aria"

    # 8. Assert: Arc created
    arcs = repository.list_arc_candidates(response.project_id)
    assert len(arcs) == 1
    assert arcs[0].name == "Hero's Journey"
```

### 11.3 Test Cases to Cover (Final)

1. `test_import_story_creates_project_and_all_entities` - Happy path
2. `test_import_story_with_existing_project_id` - Reuse existing project
3. `test_import_story_rejects_invalid_project_id` - Non-existent project
4. `test_import_story_handles_malformed_json` - JSON parsing failure
5. `test_import_story_handles_missing_fields` - Pydantic validation failure
6. `test_import_story_handles_inference_backend_error` - LLM service unavailable
7. `test_import_story_handles_markdown_code_fences` - JSON parsing edge case
8. `test_import_story_handles_trailing_text` - JSON parsing edge case
9. `test_import_story_is_idempotent_on_retry` - Deterministic IDs + ON CONFLICT
10. `test_import_story_story_text_truncation` - >24K chars gets truncated

## 12. Files to Create/Modify

### New Files:
1. `app/services/story_import.py` - Main service implementation
2. `tests/test_story_import_service.py` - Comprehensive tests

### Modified Files:
3. `app/services/runtime_prompts.py` - Add `build_import_analysis_request()`
4. `app/api/projects.py` - Add `POST /v1/projects/import-story` endpoint, update `build_projects_router` signature
5. `app/api/__init__.py` - Update `build_projects_router` import signature
6. `app/main.py` - Wire `StoryImportService` and pass to router

### Already Exist (use as-is):
7. `app/schemas/story_import.py` - Request/response/analysis schemas
8. `app/schemas/story_development.py` - FoundationProfile, CharacterProfile, etc.
9. `app/persistence/story_development.py` - Repository methods (reference for column names)
10. `app/services/projects.py` - ProjectService
11. `app/services/project_bootstrap.py` - initialize_project_artifacts()
12. `app/inference/base.py` - InferenceBackend ABC
13. `app/inference/openai_compatible.py` - Production backend
14. `app/inference/stub.py` - Stub backend
15. `app/settings.py` - Settings for inference config
16. `app/constants.py` - MAX_BODY_SIZE constant

## 13. Existing Schema Validation Rules to Reference

The `StoryImportAnalysis` schema already has validators:
- `_normalize_pov`: Validates and normalizes POV to valid enum values
- `_normalize_structure`: Validates and normalizes story_structure to valid enum values
- `StoryImportCharacterRequest._normalize_role`: Validates character role

Field constraints:
- `story_text`: max 5,000,000 characters
- `premise`: max 10,000 characters
- `logline`: max 500 characters
- `characters`: required, min 1
- All character fields have individual max_length limits

## 14. Status Code Conventions (Corrected)

**Corrected per adversarial review**:
- `POST /projects/import-story` returns **201 Created** on success
- `StoryImportResponse.status` is `"completed"` or `"failed"` (not `"processing"`)
- LLM errors return 400 with detail in response
- Service errors return 500
- `InferenceBackendError` returns 201 with `status="failed"` in response body (non-HTTP error)

## 15. Security Considerations

- Input validation: `StoryImportRequest` already limits `story_text` to 5M chars
- Project creation: Uses existing `ProjectService` (no new permissions needed)
- Database: Uses existing SQLite (no new injection surface -- raw SQL uses parameterized queries)
- LLM response: Validated via Pydantic before database insertion
- No files written to project directory (entities go only into SQLite)
- Circuit breaker prevents cascade failures on inference backend

## 16. Key Implementation Notes

1. **No Job System**: Direct service call, NOT via LocalExecutor/job manager
2. **Transaction Safety**: Single raw SQLite connection with `BEGIN` (NOT `BEGIN IMMEDIATE`), direct SQL only (NOT repo wrapper methods)
3. **Deterministic IDs**: Generate stable IDs for characters/world/arcs to support retry (`ON CONFLICT DO UPDATE`)
4. **Pydantic Validation**: Always validate LLM output before database insertion
5. **24K Char Truncation**: Phase 1 truncates story text to 24K chars for single-pass analysis
6. **Synchronous Processing**: HTTP request blocks -- no async/202
7. **Fake Inference Backend**: Use pattern from `test_local_executor_architect_runtime.py` for testing
8. **tmp_path**: Use pytest's tmp_path fixture (already configured via conftest.py)
9. **Status Field**: Response `status` is `"completed"` or `"failed"`
10. **Warnings Field**: Response includes `warnings` list for non-fatal issues

## 17. Estimated Timeline

| Phase | Tasks | Time |
|-------|-------|------|
| 1. Foundation (Service) | 6 tasks | 1.5 hours |
| 2. API Endpoint | 3 tasks | 1.0 hour |
| 3. Tests | 5 tasks (10 test functions) | 2.5 hours |
| 4. Validation | 1 task (full suite) | 0.5 hours |
| **Total** | **15 tasks** | **~5.5 hours** |

## 18. Validation Baseline

After implementation, baseline should update from `554 passed` to `~564 passed` (10 new tests in `test_story_import_service.py`).

## 19. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Raw SQL column mismatches | HIGH | Compare every column name against existing repo methods character-by-character |
| Transaction isolation / concurrent writes | MEDIUM | Use `BEGIN` (not `BEGIN IMMEDIATE`), short transaction, no repo wrapper calls |
| LLM JSON output unreliability | HIGH | Robust `_parse_llm_json()` with multiple extraction strategies |
| Pydantic validation strictness | MEDIUM | `StoryImportAnalysis` has `@model_validator(mode="before")` -- ensure LLM output is normalized |
| Large story handling | LOW (Phase 1) | Defer to Phase 2, truncate to 24K chars for single-pass |
| Circuit breaker open | LOW | `InferenceBackendError` caught, returns `status="failed"` response |
