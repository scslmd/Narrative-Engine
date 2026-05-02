# Story Import - Implementation Plan v1.0

## Goal

Allow users to paste/upload an existing completed story, then have the LLM review it, classify it, and "fill out all the blanks" (create the full project structure including foundation, characters, world bible, arcs, planning, and drafts) in one automated workflow.

---

## Architecture Decision

**Approach**: Service-based (not job-based) analysis.

The story import service will use the `InferenceBackend` directly (like `ManuscriptReviewService`), not the P-100 through P-400 job pipeline. This is because:

1. Import is a one-shot workflow, not part of the regular pipeline
2. No job phase needed - just inference + DB writes
3. Simpler error handling and retry logic
4. User gets a single API response (202 accepted) with progress tracking

---

## Task S1: Pydantic Models for LLM Output Parsing

**File**: `app/schemas/story_import.py` (new)

Create Pydantic models that match the LLM output JSON structure. These models will validate and parse the LLM response.

```python
class StoryImportCharacterRequest(StrictModel):
    name: str
    role: str  # protagonist, antagonist, mentor, deuteragonist, foil, supporting
    archetype: str
    external_goal: str
    internal_need: str
    core_fear: str
    primary_strength: str
    fatal_flaw: str
    backstory: str
    voice_notes: str
    change_axis: str
    contradictions: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    taboos: list[str] = Field(default_factory=list)
    continuity_facts: list[str] = Field(default_factory=list)

class StoryImportWorldEntry(StrictModel):
    entry_type: str  # location, culture, magic_system, item, concept
    title: str
    summary: str
    canonical_facts: list[str] = Field(default_factory=list)
    related_character_ids: list[str] = Field(default_factory=list)

class StoryImportArc(StrictModel):
    name: str
    summary: str
    stage_map: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

class StoryImportSequence(StrictModel):
    title: str
    summary: str
    chapters: list[str] = Field(default_factory=list)

class StoryImportAnalysis(StrictModel):
    project_name: str
    genre: str
    tone: str
    pov: str  # FIRST, THIRD_LIMITED, etc.
    story_structure: str  # THREE_ACT, HERO_JOURNEY, etc.
    premise: str
    logline: str
    thematic_spine: str
    emotional_promise: str
    target_audience: str
    complexity_level: str
    characters: list[StoryImportCharacterRequest]
    world_bible: list[StoryImportWorldEntry]
    story_arcs: list[StoryImportArc]
    sequences: list[StoryImportSequence]
    narrative_constraints: list[str] = Field(default_factory=list)
    success_definition: str
    raw_story_text: str = ""  # Optional, for manuscript creation
```

**Key decisions**:
- Use `StrictModel` from Pydantic to reject unknown fields
- Keep field names matching CharacterProfile/FoundationProfile for easy mapping
- `pov` and `story_structure` are strings that map to enum values
- All fields are required (LLM should provide defaults)

---

## Task S2: Prompt Builder for Story Import

**File**: `app/services/runtime_prompts.py` (modify)

Add a new prompt builder function:

```python
def build_import_analysis_request(
    *,
    story_text: str,
    project_name: str,
    default_model: str | None,
    max_tokens: int = 8000,  # Large output needed
    temperature: float = 0.3,  # Slightly higher for creativity
) -> InferenceRequest:
    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are a Story Analyst for Narrative-Engine. "
                    "Given a complete story text, analyze it and produce structured metadata as strict JSON. "
                    "Return ONLY a JSON object matching this schema - no markdown, no explanation, no code fences. "
                    "Use defaults for fields you cannot determine: role='supporting', archetype='unknown', "
                    "stage_map=['status_quo', 'inciting_incident', 'rising_action', 'crisis', 'climax', 'resolution'], "
                    "tags=[], canonical_facts=[], related_character_ids=[], narrative_constraints=[], "
                    "secrets=[], values=[], taboos=[], continuity_facts=[], contradictions=[]."
                ),
            ),
            InferenceMessage(
                role="user",
                content=(
                    f"Analyze this story and extract all metadata:\n\n"
                    f"Story title/name hint: {project_name}\n\n"
                    f"STORY TEXT:\n{story_text}\n\n"
                    f"Return the analysis as JSON."
                ),
            ),
        ],
        metadata={
            "mode": "story_import",
            "project_name": project_name,
        },
    )
```

**Token management**:
- `max_tokens=8000` for large JSON output
- `temperature=0.3` for structured output
- Story text should be truncated if too large (see S3)

---

## Task S3: Core Story Import Service

**File**: `app/services/story_import.py` (new)

```python
class StoryImportError(ValueError):
    """Base error for story import operations."""
    pass

class StoryImportInferenceError(StoryImportError):
    """LLM inference failed."""
    pass

class StoryImportValidationError(StoryImportError):
    """LLM output failed validation."""
    pass

class StoryImportService:
    def __init__(
        self,
        repository: StoryDevelopmentRepository,
        project_service: ProjectService,
        inferencer: InferenceBackend,
    ) -> None:
        self.repository = repository
        self.project_service = project_service
        self.inferencer = inferencer
    
    def analyze_and_import(
        self,
        *,
        project_name: str,
        story_text: str,
        project_id: str | None = None,
        genre: str | None = None,
        tone: str | None = None,
    ) -> tuple[str, str]:
        """
        Analyze story text via LLM and create full project structure.
        
        Returns: (project_id, status_message)
        Status message indicates success or partial success with errors.
        """
        # 1. Generate project_id if not provided
        if project_id is None:
            project_id = str(uuid4())
        
        # 2. Create project with minimal config
        manifest_config = self._build_manifest_config(genre, tone)
        manifest = Manifest(
            project_id=project_id,
            project_name=project_name,
            config=manifest_config,
        )
        initialize_project_artifacts(project_id, manifest=manifest)
        self.project_service.repository.register_project_dir(
            self.project_service.projects_dir / project_id
        )
        
        # 3. Truncate story text if needed (respect context window)
        truncated_text = self._prepare_story_text(story_text, max_chars=50_000)
        
        # 4. Call LLM for analysis
        analysis = self._analyze_with_llm(project_name, truncated_text)
        
        # 5. Create project entities
        self._create_foundation(project_id, analysis)
        characters = self._create_characters(project_id, analysis)
        self._create_world_bible(project_id, analysis, characters)
        arcs = self._create_arcs(project_id, analysis)
        self._create_planning(project_id, analysis, characters)
        self._create_manuscript(project_id, story_text)
        
        return project_id, "Import complete"
    
    def _build_manifest_config(self, genre: str | None, tone: str | None) -> ManifestConfig:
        """Build manifest config from analysis or defaults."""
        ...
    
    def _prepare_story_text(self, story_text: str, *, max_chars: int = 50_000) -> str:
        """Truncate story text if it exceeds token limits."""
        if len(story_text) <= max_chars:
            return story_text
        # Keep beginning and end for context
        head = story_text[:max_chars // 2]
        tail = story_text[-max_chars // 2:]
        return f"{head}\n\n... [truncated for analysis] ...\n\n{tail}"
    
    def _analyze_with_llm(self, project_name: str, story_text: str) -> StoryImportAnalysis:
        """Call LLM and parse JSON response."""
        inference_request = build_import_analysis_request(
            story_text=story_text,
            project_name=project_name,
            default_model=self.inferencer.descriptor.default_model,
        )
        
        try:
            response = self.inferencer.generate_text(inference_request)
        except InferenceBackendError as exc:
            raise StoryImportInferenceError(str(exc)) from exc
        
        # Parse JSON - try to extract from possible markdown code blocks
        content = response.content.strip()
        json_str = self._extract_json_from_response(content)
        
        try:
            raw_data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise StoryImportValidationError(f"LLM returned invalid JSON: {exc}")
        
        try:
            return StoryImportAnalysis.model_validate(raw_data)
        except ValidationError as exc:
            raise StoryImportValidationError(f"LLM output failed validation: {exc}")
    
    def _extract_json_from_response(self, content: str) -> str:
        """Extract JSON from possible markdown code blocks or raw text."""
        # Try to find JSON between ```json ... ``` or ``` ... ```
        if '```' in content:
            parts = content.split('```')
            for part in parts:
                if part.strip().startswith('json'):
                    continue
                # Try this part as JSON
                stripped = part.strip()
                if stripped.startswith('{'):
                    return stripped
            # Fall back to last part
            return parts[-1].strip()
        return content
    
    def _create_foundation(self, project_id: str, analysis: StoryImportAnalysis) -> None:
        """Create foundation profile from analysis."""
        self.repository.upsert_foundation_profile(
            project_id=project_id,
            premise=analysis.premise,
            logline=analysis.logline,
            thematic_spine=analysis.thematic_spine,
            emotional_promise=analysis.emotional_promise,
            tone_direction=analysis.tone,
            target_audience=analysis.target_audience,
            narrative_constraints=analysis.narrative_constraints,
            complexity_level=analysis.complexity_level,
            success_definition=analysis.success_definition,
        )
    
    def _create_characters(
        self,
        project_id: str,
        analysis: StoryImportAnalysis,
    ) -> dict[str, str]:
        """Create character profiles. Returns {display_name: character_id} mapping."""
        name_to_id: dict[str, str] = {}
        for char_data in analysis.characters:
            character_id = f"char:{uuid4().hex[:8]}"
            # Generate a slug for relationship mapping
            slug = char_data.name.lower().replace(' ', '_')
            character_id = f"char:{slug}"
            
            self.repository.upsert_character_profile(
                project_id=project_id,
                character_id=character_id,
                display_name=char_data.name,
                role_in_story=char_data.role,
                archetype=char_data.archetype,
                external_goal=char_data.external_goal,
                internal_need=char_data.internal_need,
                misbelief_or_wound=char_data.core_fear,  # Map core_fear to misbelief_or_wound
                core_fear=char_data.core_fear,
                primary_strength=char_data.primary_strength,
                fatal_flaw_or_limitation=char_data.fatal_flaw,
                contradictions=char_data.continuidties,
                backstory_summary=char_data.backstory,
                voice_notes=char_data.voice_notes,
                secrets=char_data.secrets,
                values=char_data.values,
                taboos=char_data.taboos,
                change_axis=char_data.change_axis,
                arc_stage_notes=[],
                continuity_facts=char_data.continuity_facts,
            )
            name_to_id[char_data.name] = character_id
        
        return name_to_id
    
    def _create_world_bible(
        self,
        project_id: str,
        analysis: StoryImportAnalysis,
        characters: dict[str, str],
    ) -> None:
        """Create world bible entries."""
        for entry_data in analysis.world_bible:
            # Map character names to IDs
            related_ids = [
                characters[name] for name in entry_data.related_character_ids
                if name in characters
            ]
            
            self.repository.upsert_world_bible_entry(
                project_id=project_id,
                entry_type=entry_data.entry_type,
                title=entry_data.title,
                summary=entry_data.summary,
                canonical_facts=entry_data.canonical_facts,
                related_character_ids=related_ids,
            )
    
    def _create_arcs(
        self,
        project_id: str,
        analysis: StoryImportAnalysis,
    ) -> list[str]:
        """Create arc candidates and selections. Returns list of arc_ids."""
        arc_ids = []
        for arc_data in analysis.story_arcs:
            arc_id = f"arc:{uuid4().hex[:8]}"
            
            self.repository.upsert_arc_candidate(
                project_id=project_id,
                arc_id=arc_id,
                name=arc_data.name,
                summary=arc_data.summary,
                stage_map_notes=arc_data.stage_map,
                fit_notes=arc_data.tags,
                tags=arc_data.tags,
            )
            
            if arc_data.stage_map:
                self.repository.upsert_arc_stage_map(
                    project_id=project_id,
                    arc_id=arc_id,
                    stage_kinds=arc_data.stage_map,
                    arc_stage_map_id=f"arcmap:{arc_id}",
                )
            
            # Record as selected (no comparison needed for import)
            self.repository.upsert_arc_selection(
                project_id=project_id,
                selection_id=f"selection:{arc_id}",
                selected_arc_id=arc_id,
                selected_arc=arc_data.model_dump(mode='json'),
            )
            
            arc_ids.append(arc_id)
        
        return arc_ids
    
    def _create_planning(
        self,
        project_id: str,
        analysis: StoryImportAnalysis,
        characters: dict[str, str],
    ) -> None:
        """Create sequence and chapter plans."""
        for seq_data in analysis.sequences:
            sequence_id = f"seq:{uuid4().hex[:8]}"
            
            self.repository.upsert_sequence_plan(
                sequence_id=sequence_id,
                project_id=project_id,
                title=seq_data.title,
                summary=seq_data.summary,
                chapter_ids=seq_data.chapters,
            )
    
    def _create_manuscript(self, project_id: str, story_text: str) -> None:
        """Create manuscript document with the story text."""
        self.repository.upsert_manuscript_document(
            document_id="manuscript:001",
            project_id=project_id,
            title="Imported Story",
            content=story_text,
            version=1,
        )
```

**Key design decisions**:
- No transaction wrapping (each repo call commits individually)
- If LLM fails, project exists but may be empty - user can retry
- Character IDs use slug from name for consistency
- No arc comparison (import is a one-shot, not competitive)
- All text fields will be normalized by repository layer

---

## Task S4: API Endpoint

**File**: `app/api/projects.py` (modify)

Add a new import endpoint:

```python
@router.post(
    "/import-story",
    response_model=StoryImportResponse,
    status_code=202,
)
def import_story(payload: StoryImportRequest) -> StoryImportResponse:
    """Import a story by pasting/uploading text.
    
    The LLM analyzes the story and creates the full project structure.
    This returns 202 Accepted - processing happens asynchronously.
    """
    try:
        project_id, status = import_service.analyze_and_import(
            project_name=payload.project_name,
            story_text=payload.story_text,
            project_id=payload.project_id,
            genre=payload.genre,
            tone=payload.tone,
        )
    except StoryImportInferenceError as exc:
        raise HTTPException(status_code=503, detail="LLM service unavailable.")
    except StoryImportValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except StoryImportError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    
    return StoryImportResponse(
        project_id=project_id,
        status="completed",
        message=status,
    )
```

**Request/Response schemas** (in `app/schemas/story_import.py`):
```python
class StoryImportRequest(StrictModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    story_text: str = Field(..., min_length=1, max_length=5_000_000)  # 5MB limit
    project_id: str | None = Field(None, max_length=255)
    genre: str | None = None  # Override LLM-determined genre
    tone: str | None = None   # Override LLM-determined tone

class StoryImportResponse(StrictModel):
    project_id: str
    status: str  # "completed", "failed", "partial"
    message: str
    warnings: list[str] = Field(default_factory=list)
```

---

## Task S5: Router Registration

**File**: `app/api/projects.py` (modify)

Register the import service in the router initialization:
```python
from app.services.story_import import StoryImportService

# In router factory
import_service = StoryImportService(
    repository=repository,
    project_service=project_service,
    inferencer=inferencer,  # from app settings
)
```

---

## Task S6: Backend Tests

**File**: `tests/test_story_import_service.py` (new)

Test cases:
1. `test_analyze_and_import_creates_project` - verifies project exists after import
2. `test_analyze_and_import_creates_foundation` - verifies foundation profile created
3. `test_analyze_and_import_creates_characters` - verifies character count matches
4. `test_analyze_and_import_creates_world_bible` - verifies world entries
5. `test_analyze_and_import_creates_arcs` - verifies arc candidates and selections
6. `test_analyze_and_import_creates_manuscript` - verifies manuscript document
7. `test_analyze_story_raises_on_invalid_json` - LLM returns garbage
8. `test_analyze_story_raises_on_validation_error` - Missing required fields
9. `test_prepare_story_text_truncates_long_text` - Token limit handling
10. `test_extract_json_from_response_handles_markdown` - Code block parsing

---

## Task S7: Frontend (Future)

When frontend work is ready:
1. Import view with textarea + file upload
2. Progress indicator for async processing
3. Preview/edit of extracted data before committing

---

## Implementation Order

1. S1: Pydantic models for LLM output
2. S2: Prompt builder
3. S3: Core service (with mocks for tests)
4. S4: API endpoint + schemas
5. S5: Router registration
6. S6: Backend tests

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| LLM output doesn't match schema | Strict Pydantic validation, clear system prompt with defaults |
| Story too large for context window | Truncate to 50K chars, warn user |
| Partial import on failure | Project created but empty - user can retry |
| Character name conflicts | Use UUID + slug, check for duplicates |
| Slow LLM response | Return 202, allow async polling (future) |
| LLM hallucinates data | System prompt asks for defaults, user can review |

---

## Token Budget Estimate

For a ~50K character story (roughly 10K-15K tokens):

- Prompt tokens: ~15K (story text + prompt + schema)
- Completion tokens: ~4K-6K (JSON analysis)
- Total: ~20K tokens

This requires a model with at least 32K context window. Most local models (Llama 3 8B, Qwen 2.5 14B) support this.

If story is larger, consider:
1. Chunked analysis (first pass: summary, second pass: details)
2. Story segmentation (break into acts/chapters, analyze each)
3. Two-pass approach (metadata only first, then character/world details)
