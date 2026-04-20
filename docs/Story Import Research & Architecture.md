# Story Import - Research & Architecture Document

## Goal

Allow users to paste/upload an existing completed story, then have the LLM review it, classify it, and "fill out all the blanks" (create the full project structure including foundation, characters, world bible, arcs, planning, and drafts) in one automated workflow.

---

## 1. Project Creation Flow

### 1.1 Entry Points

**API**: `POST /projects/create` (201 Created)
- **Service**: `app/services/projects.py::ProjectService.create_project()`
- **Schema**: `ProjectCreateRequest` (in `app/schemas/projects.py`)

```python
class ProjectCreateRequest(StrictSchemaModel):
    project_id: str
    project_name: str
    config: ManifestConfig | None          # Full config object (genre, tone, structure, etc.)
    constraints: list[str]
    premise_text: str | None
    idempotency_key: str | None
    project_kind: str = "standard"
    # Legacy fields
    genre: str | None = None
    tone_profile: str | None = None
    story_structure: str | None = None
```

### 1.2 Project Bootstrap

**Service**: `app/services/project_bootstrap.py::bootstrap_project()`

Creates per-project directory structure:
```
data/projects/{project_id}/
  manifest.json           # Project config (JSON)
  bible.db                # Project-local SQLite metadata
  sequences.json          # Story structure/sequence
  chapter.md              # Chapter 1 draft
  exports/                # Generated artifacts directory
  .telemetry              # Telemetry data
  .structured_log         # Structured event log
```

### 1.3 Database Registration

**Service**: `app/persistence/projects.py::ProjectRepository.register_project_dir()`

Registers in operations DB:
- `projects` table: `project_id`, `project_name`, `manifest_path`, `db_path`, timestamps
- `project_artifacts` table: per-artifact path tracking
- Initializes project-local `bible.db` with `project_metadata` and `artifacts` tables

### 1.4 Manifest & Config

**Schema**: `app/schemas/manifest.py`

```python
class ManifestConfig(StrictSchemaModel):
    genre: str
    tone_profile: str
    pov: PovMode = PovMode.THIRD_LIMITED
    primary_language: str = "English"
    secondary_language: str | None = None
    story_structure: StoryStructure

class Manifest(StrictModel):
    project_id: str
    project_name: str
    config: ManifestConfig
    constraints: list[str]
    premise_text: str | None
```

**Enums** (`app/schemas/enums.py`):
```python
class StoryStructure(str, Enum):
    SAVE_THE_CAT, THREE_ACT, HERO_JOURNEY, FREYTAGS_PYRAMID,
    KISHOTENKETSU, FICHTEAN_CURVE, SEVEN_POINT_STRUCTURE,
    SEVEN_KEY_STEPS, SNOWFLAKE_METHOD, BRAINDUMP, OTHER

class PovMode(str, Enum):
    FIRST, SECOND, THIRD_LIMITED, THIRD_OMNI,
    THIRD_OBJECTIVE, THIRD_MULTIPLE, OTHER
```

---

## 2. Story Development Entities

All created via `StoryDevelopmentRepository` (single-threaded, no bulk insert).

### 2.1 Foundation Profile

**Table**: `foundation_profiles` + `foundation_revisions`
**Schema**: `FoundationProfile` (in `app/schemas/story_development.py:194`)

```python
class FoundationProfile(StrictModel):
    foundation_id: str
    project_id: str
    premise: str                  # One-paragraph story core
    logline: str                  # One-sentence summary
    thematic_spine: str           # Central theme
    emotional_promise: str        # What reader experiences
    tone_and_voice_direction: str # Narrative voice/tone
    target_audience: str          # Demographic
    narrative_constraints: list[str]
    complexity_level: str
    success_definition: str
    version: int
```

**Service**: `FoundationService` (in `app/services/foundation.py`)
- Creates revisions on every change
- Tracks downstream impact via `IMPACT_RULES` (maps field changes to affected areas)

### 2.2 Characters

**Table**: `character_profiles` + `relationship_edges`
**Schema**: `CharacterProfile` (in `app/schemas/story_development.py:288`)

```python
class CharacterProfile(StrictModel):
    character_id: str
    project_id: str
    display_name: str
    role_in_story: str              # protagonist, antagonist, mentor, etc.
    archetype: str                  # hero, trickster, shadow, etc.
    external_goal: str              # What they want
    internal_need: str              # What they need
    misbelief_or_wound: str         # Past trauma/wrong belief
    core_fear: str
    primary_strength: str
    fatal_flaw_or_limitation: str
    contradictions: list[str]
    backstory_summary: str
    voice_notes: str
    secrets: list[str]
    values: list[str]
    taboos: list[str]
    change_axis: str               # Arc of transformation
    arc_stage_notes: list[str]
    continuity_facts: list[str]
    writer_notes: str | None
    # NOTE: relationship_edges auto-populated from separate table
```

### 2.3 World Bible

**Table**: `world_bible_entries`
**Schema**: `WorldBibleEntry` (in `app/schemas/story_development.py:344`)

```python
class WorldBibleEntry(StrictModel):
    entry_id: str
    project_id: str
    entry_type: str              # location, item, concept, culture, magic_system, etc.
    title: str
    summary: str
    canonical_facts: list[str]
    related_character_ids: list[str]
    source_artifacts: list[str]
    visibility_scope: str = "project"
    continuity_warnings: list[str]
    writer_notes: str | None
```

### 2.4 Story Arcs

Three tables: `arc_candidates`, `arc_stage_maps`, `arc_selections`

**ArcCandidate**:
```python
class ArcCandidate(StrictModel):
    arc_id: str
    project_id: str
    name: str
    summary: str
    stage_map_notes: list[str]
    fit_notes: list[str]
    tags: list[str]
```

**ArcStageMap**:
```python
class ArcStageMap(StrictModel):
    arc_stage_map_id: str
    project_id: str
    arc_id: str
    stage_kinds: list[str]    # e.g., ["status_quo", "catalyst", "trial", "crisis", "resolution"]
    notes: str | None
```

**ArcSelection**:
```python
class ArcSelection(StrictModel):
    selection_id: str
    project_id: str
    selected_arc: ArcCandidate
    rejected_arc_ids: list[str]
    comparison_notes: list[str]
    comparison_record_ids: list[str]
    stage_map: ArcStageMap | None
```

### 2.5 Planning

Four tables: `sequence_plans`, `chapter_plans`, `scene_plans`, `beat_plans`

**SequencePlan**:
```python
class SequencePlan(StrictModel):
    sequence_id: str
    project_id: str
    title: str
    summary: str
    beat_ids: list[str]
    chapter_ids: list[str]
    status: str
    position: int
```

### 2.6 Drafting

**DraftArtifact**: Generated draft content
**ManuscriptDocument**: Finalized manuscript content (linked to chapters/scenes)

---

## 3. Database Persistence Layer

### 3.1 Architecture

Two SQLite databases:

| Database | Path | Purpose |
|----------|------|---------|
| Operations DB | `settings.operations_db_path` | Central registry (projects, jobs, story dev data, etc.) |
| Project DB | `data/projects/{project_id}/bible.db` | Project-local metadata |

### 3.2 Operations DB Tables (40+ tables)

**Key tables for story import**:
- `projects` - project registry
- `foundation_profiles` / `foundation_revisions` - story foundation
- `character_profiles` - character data
- `relationship_edges` - character relationships
- `world_bible_entries` - world lore
- `arc_candidates` / `arc_stage_maps` / `arc_selections` - story arcs
- `sequence_plans` / `chapter_plans` / `scene_plans` / `beat_plans` - planning
- `draft_artifacts` / `manuscript_documents` - drafting content

### 3.3 Repository Pattern

**File**: `app/persistence/story_development.py::StoryDevelopmentRepository`

All methods are single-row operations with no bulk/batch support. Each call opens its own connection and commits immediately. Creating a project with full sub-entities requires **N separate calls**:

```
register_project_dir()          -> 1 call
upsert_foundation_profile()     -> 2 rows (profile + revision)
upsert_character_profile()      -> 1 row per character
upsert_relationship_edge()      -> 1 row per edge
upsert_world_bible_entry()      -> 1 row per entry
upsert_arc_candidate()          -> 1 row per candidate
upsert_arc_stage_map()          -> 1 row per arc
upsert_arc_selection()          -> 2-3 rows
upsert_sequence_plan()          -> 1 row per sequence
upsert_chapter_plan()           -> 1 row per chapter
upsert_manuscript_document()    -> 1 row per manuscript
```

### 3.4 No Bulk Insert

No `executemany()` usage anywhere. Each row is a separate INSERT/UPDATE with its own commit. Transaction wrapping exists per-method but not across methods.

---

## 4. LLM Inference System

### 4.1 Architecture

```
InferenceBackend (ABC)
    |
    +-- OpenAICompatibleInferenceBackend  (production)
    +-- StubInferenceBackend              (testing)
```

**Factory**: `app/inference/factory.py::build_inference_backend()`

### 4.2 Supported Providers

| Provider | Env Backend | Default URL |
|----------|-------------|-------------|
| llama.cpp | `llama.cpp` | `http://127.0.0.1:8080` |
| LM Studio | `lmstudio` | `http://127.0.0.1:1234` |
| vLLM | `vllm` | `http://127.0.0.1:8000` |
| OpenAI | `openai_compatible` | `http://127.0.0.1:8000` |
| Stub | `stub` | N/A |

All non-stub providers use the same `OpenAICompatibleInferenceBackend` - they differ only in display name and default URL.

### 4.3 Inference API Contract

```python
class InferenceBackend(ABC):
    @abstractmethod
    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        ...
```

**Request** (from `app/schemas/inference.py`):
```python
class InferenceRequest(StrictModel):
    model: str
    system_prompt: str
    user_prompt: str
    temperature: float = 0.2
    max_tokens: int = 1200
    metadata: dict[str, str] = Field(default_factory=dict)
```

**Response**:
```python
class InferenceResponse(StrictModel):
    model: str
    content: str
    backend: str
    finish_reason: str
    usage: dict[str, int]
    metadata: dict[str, str] = Field(default_factory=dict)
```

### 4.4 How LocalExecutor Calls Inference

**File**: `app/services/local_executor.py`

Pattern used in each phase (`_run_p100_phase`, `_run_p200_phase`, etc.):

```python
# 1. Build inference request from runtime prompt
inference_request = build_p100_architect_request(manifest, payload)

# 2. Call the backend (with circuit breaker)
inference_response = self._inferencer.generate_text(inference_request)

# 3. Write response to file
staged_file.write_text(inference_response.content, encoding="utf-8")
staged_file.replace(output_file)  # Atomic replace

# 4. Create step record + artifact lineage
self._step_records.create_step_record(state="COMPLETED", ...)
self._lineage.create_artifact_lineage(status="PROPOSED", ...)
```

### 4.5 Existing Prompt Patterns (from `app/services/runtime_prompts.py`)

Each prompt follows a role-based system message pattern:

**P-100 Architect** (system: "You are the Architect role... Produce deterministic markdown"):
- Output: Logline, Core Premise, Story Engine, World Anchors, Character Arcs, Constraints, Open Questions
- temperature: 0.2, max_tokens: 1200

**P-200 Sequencer** (system: "You are the Sequencer role... Produce deterministic JSON"):
- Input: manifest + optional architect_output
- Output: JSON structure with sequences/beats

**P-300 Drafter** (system: "You are the Drafter role... Produce deterministic markdown"):
- Input: manifest + sequence_output + architect_output
- Output: chapter markdown

**P-400 Compiler** (system: "You are the Compiler role... Produce deterministic JSON"):
- Input: manifest + all previous outputs
- Output: story bible JSON

### 4.6 Settings

| Env Variable | Property | Default |
|--------------|----------|---------|
| `NARRATIVE_INFERENCE_BACKEND` | `inference_backend` | `"stub"` |
| `NARRATIVE_INFERENCE_BASE_URL` | `inference_base_url` | provider-specific |
| `NARRATIVE_INFERENCE_API_KEY` | `inference_api_key` | `None` |
| `NARRATIVE_INFERENCE_MODEL` | `inference_default_model` | `None` |
| `NARRATIVE_INFERENCE_TIMEOUT_SECONDS` | `inference_timeout_seconds` | `120.0` |

---

## 5. Job System

### 5.1 Job Phases (P-100 to P-400 only)

**Schema**: `app/schemas/enums.py::JobPhase`

```python
class JobPhase(str, Enum):
    P_100 = "P-100"
    P_200 = "P-200"
    P_300 = "P-300"
    P_400 = "P-400"
```

**There are NO custom job phases.** Only P-100 through P-400 are supported. New phases must go through the executor's `_require_supported_job_phase()` validation.

### 5.2 Job Lifecycle

**Manager**: `app/services/job_manager.py::JobManager`

```
PENDING -> PROCESSING -> COMPLETED
PENDING -> PROCESSING -> FAILED
```

**Worker**: `app/services/local_executor.py::LocalExecutor`

Two daemon threads:
- `_job_loop` - claims and processes P-100 through P-400 jobs
- `_checker_loop` - processes role-model checker runs

### 5.3 Job Schema

```python
class JobCreateRequest(StrictModel):
    phase: JobPhase
    payload: dict[str, Any]          # Must contain project_id
    idempotency_key: str | None
```

---

## 6. Existing Services for Reference

### 6.1 ManuscriptReviewService (NEW - from manuscript word processor)

**File**: `app/services/manuscript_review.py`

```python
class ManuscriptReviewService:
    def __init__(self, repository: StoryDevelopmentRepository)
    
    def analyze_manuscript(self, project_id: str, *, document_id: str) -> tuple[RevisionSuggestion, ...]
        # Rule-based checks:
        # - Repetition detection (3+ lines with 15+ chars)
        # - Blank paragraph detection (4+ consecutive newlines)
        # - Potential new character detection (proper nouns vs known characters)
```

Uses `ManuscriptReviewError` exception. Persists findings as `RevisionSuggestion` records.

### 6.2 DraftingService

**File**: `app/services/drafting.py`

Key methods:
- `save_manuscript_document()` - upsert with auto-version-increment
- `promote_draft_to_manuscript()` - draft -> manuscript conversion
- `create_revision_suggestion()` - create suggestion record
- `list_revision_suggestions_for_document()` - get suggestions linked to a doc

### 6.3 FoundationService

**File**: `app/services/foundation.py`

- Creates/updates FoundationProfile with revision history
- Tracks downstream impact (IMPACT_RULES)
- `FoundationProfileInput` dataclass for creation, `FoundationProfilePatch` for updates

### 6.4 StoryKnowledgeService

**File**: `app/services/story_knowledge.py`

- Character profiles CRUD
- World Bible CRUD
- Arc candidate management (create, compare, select)
- Uses `entry_type + title` as unique key for world bible entries

---

## 7. What This Means for Story Import

### 7.1 The Workflow

```
User pastes story text
    |
    v
[LLM] Analyze story -> extract metadata
    |                 - genre, tone, POV, structure
    |                 - premise, logline, thematic_spine
    |                 - character list with details
    |                 - world bible entries
    |                 - story arcs
    |                 - sequence/structure
    v
[Service] Parse LLM response into structured data
    |
    v
[Service] Create project (register in DB)
    |
    v
[Service] Create foundation profile
    |
    v
[Service] Create character profiles (N calls)
    |
    v
[Service] Create world bible entries (N calls)
    |
    v
[Service] Create arc candidates + selections
    |
    v
[Service] Create planning records (sequences, chapters)
    |
    v
[Service] Create manuscript document (story text)
    |
    v
Done - project ready with full structure
```

### 7.2 Key Design Decisions

**1. One API call to start, async processing**
- User sends `POST /projects/import-story` with story text
- Server creates project with minimal config, returns 202
- A background job (or service) processes the story text via LLM
- User polls status or gets webhook notification

**2. Use existing LLM infrastructure**
- Reuse `InferenceBackend` for all analysis
- Create a new prompt builder (e.g., `build_import_analysis_request`)
- No new job phase needed - just a service that calls inference directly
- Similar to how `ManuscriptReviewService` works (non-job-based analysis)

**3. Single structured LLM call or multi-step?**
- **Option A (single call)**: One massive prompt with story text + structured output schema (JSON). Faster but may hit token limits.
- **Option B (multi-step)**: Break analysis into phases (e.g., character extraction, world extraction, structure extraction). More reliable but slower.
- **Recommendation**: Start with single call for stories under ~50K tokens. Multi-step for larger texts.

**4. Parse LLM output**
- Use Pydantic models for validation of LLM output
- `ManuscriptDocumentUpdateRequest` pattern shows how to handle strict validation
- LLM returns JSON -> validate with Pydantic -> create DB records

**5. Transaction safety**
- Each repository method commits individually
- If LLM fails mid-way, partial project exists
- **Solution**: Either wrap in a manual transaction (open connection once, commit at end) or allow partial imports with recovery

**6. Token management**
- Story text could be very large (novels = 50K-100K+ words)
- Need to chunk or summarize for LLM context window
- Consider: first pass for metadata (small summary), second pass for detailed extraction
- The `runtime_prompts.py` `_runtime_prompt_context` shows how to structure prompt inputs

### 7.3 New Components Needed

**Backend**:
1. `app/services/story_import.py` - `StoryImportService` class
   - `analyze_story()` - calls LLM to parse story
   - `create_project_from_analysis()` - builds all entities
2. `app/schemas/story_import.py` - request/response schemas
   - `StoryImportRequest` - story_text, project_name, project_kind
   - `StoryImportResponse` - project_id, status, findings
3. `app/api/projects.py` - new endpoint `POST /projects/import-story`
4. Prompt builder in `runtime_prompts.py` - `build_import_analysis_request()`

**Frontend** (future):
1. Import view with textarea/file upload
2. Progress indicator for async processing
3. Preview/edit of extracted data before committing

### 7.4 LLM Prompt Design

The import analysis prompt needs to extract all project entities from raw story text:

```
System: "You are a Story Analyst. Given a complete story text, analyze it and produce structured metadata as JSON."

User prompt includes:
1. Story text (chunked if needed)
2. Output schema (all fields required)

Output JSON structure:
{
  "project_name": string,
  "genre": string,
  "tone": string,
  "pov": "FIRST" | "THIRD_LIMITED" | ...,
  "story_structure": "THREE_ACT" | "HERO_JOURNEY" | ...,
  "premise": string,
  "logline": string,
  "thematic_spine": string,
  "emotional_promise": string,
  "target_audience": string,
  "complexity_level": string,
  "characters": [
    {
      "name": string,
      "role": "protagonist" | "antagonist" | "mentor" | "deuteragonist" | "foil" | "supporting",
      "archetype": string,
      "external_goal": string,
      "internal_need": string,
      "core_fear": string,
      "primary_strength": string,
      "fatal_flaw": string,
      "backstory": string,
      "voice_notes": string,
      "change_axis": string,
      ...
    }
  ],
  "world_bible": [
    {
      "type": "location" | "culture" | "magic_system" | "item" | "concept",
      "title": string,
      "summary": string,
      "canonical_facts": [string],
      "related_characters": [string]
    }
  ],
  "story_arcs": [
    {
      "name": string,
      "summary": string,
      "stage_map": ["status_quo", "inciting_incident", "rising_action", "crisis", "climax", "resolution"],
      "tags": [string]
    }
  ],
  "sequences": [
    {
      "title": string,
      "summary": string,
      "chapters": [string]
    }
  ],
  "narrative_constraints": [string],
  "success_definition": string
}
```

### 7.5 Error Handling Strategy

- **LLM timeout/failure**: Allow retry, show partial results if available
- **Invalid LLM output**: Use fallback defaults, show user for manual review
- **Duplicate project**: Use idempotency key
- **Token limit exceeded**: Implement chunked processing
- **Database error**: Rollback what was inserted (if using transaction wrapping)

---

## 8. File Paths Reference

### Project Creation
| Purpose | File |
|---------|------|
| Project API | `app/api/projects.py` |
| Project service | `app/services/projects.py` |
| Project bootstrap | `app/services/project_bootstrap.py` |
| Project schemas | `app/schemas/projects.py` |
| Manifest/Config | `app/schemas/manifest.py` |
| Enums | `app/schemas/enums.py` |
| Project repo | `app/persistence/projects.py` |

### Story Development
| Purpose | File |
|---------|------|
| Story dev API | `app/api/story_development.py` |
| Story dev repo | `app/persistence/story_development.py` |
| Foundation service | `app/services/foundation.py` |
| Story knowledge | `app/services/story_knowledge.py` |
| Drafting service | `app/services/drafting.py` |
| Manuscript review | `app/services/manuscript_review.py` |
| Story dev schemas | `app/schemas/story_development.py` |

### LLM/Inference
| Purpose | File |
|---------|------|
| Base class | `app/inference/base.py` |
| OpenAI backend | `app/inference/openai_compatible.py` |
| Stub backend | `app/inference/stub.py` |
| Factory | `app/inference/factory.py` |
| Inference schemas | `app/schemas/inference.py` |
| Runtime prompts | `app/services/runtime_prompts.py` |
| Settings | `app/settings.py` |
| Executor | `app/services/local_executor.py` |
| Job manager | `app/services/job_manager.py` |
| Job schemas | `app/schemas/jobs.py` |

### Database
| Purpose | File |
|---------|------|
| SQLite utilities | `app/persistence/sqlite.py` |
| DB helper | `app/database.py` |
| Operations schema | `app/persistence/sqlite.py` (OPERATIONS_SCHEMA) |
| Constants | `app/constants.py` |
