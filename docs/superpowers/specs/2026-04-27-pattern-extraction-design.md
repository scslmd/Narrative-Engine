# Pattern Extraction & Adventure Generation — Design Spec

**Date:** 2026-04-27
**Status:** Approved by user
**Complexity:** Medium-High — service generalization, new schema layer, prompt engineering, generation pipeline integration, UI features

## Goal

Enable users to import any completed story, have the LLM extract its full "storytelling DNA" (archetypal patterns, narrative structure, voice profile, thematic constraints, world rules), then generate original adventures — either in the same world with original characters, same world with new cast, or transposed to a completely new setting — guided by per-chapter author prompts.

## Architecture

Generalize `MythosExtractionService` into `PatternExtractionService` that works on any text type via a `source_type` parameter. The service selects the appropriate LLM prompt builder based on source type, extracts patterns, and persists them to existing project structures. Extracted pattern data flows into the P-100/P-300 generation pipeline via manifest fields and runtime context injection.

```
User imports completed story or pastes narrative text
    ↓
POST /projects/import-patterns (source_type: "narrative" | "mythology")
    ↓
PatternExtractionService.extract()
    ├─ source_type="narrative" → build_narrative_analysis_request()
    ├─ source_type="mythology" → build_mythos_analysis_request() (existing)
    ├─ Parse JSON → PatternExtractionAnalysis
    └─ _transactional_import() → persist entities + patterns
    ↓
Project created/enriched with:
  - FoundationProfile (thematic spine, narrative constraints as JSON)
  - World Bible (rules, motifs as concept entries)
  - Character archetypes (pattern carriers)
  - Voice profile + thematic constraints (narrative-specific)
    ↓
Author triggers generation from Planning workspace:
  1. Select generation mode (same_world | new_characters | transposed)
  2. Enter per-chapter author prompt
  3. System runs P-100 Architect with pattern context
  4. System runs P-300 Drafter with pattern guidance + author direction
    ↓
Original adventure generated following source story's patterns
```

## API Contract

### Import Patterns

**Endpoint:** `POST /projects/import-patterns`
**Returns:** 201 Created

**Request:**
```json
{
  "text": "<raw story text, up to 5M chars>",
  "source_type": "narrative",        // required: mythology | narrative
  "generation_mode": "same_world",   // optional: same_world | new_characters | transposed
  "project_id": null,                // optional — creates new project if omitted
  "source_corpus": "The Hobbit"      // optional — AI identifies if omitted
}
```

**Response (201):**
```json
{
  "status": "completed",
  "project_id": "<uuid>",
  "extraction": {
    "source_type": "narrative",
    "archetypal_patterns": 3,
    "narrative_structures": 2,
    "world_rules": 4,
    "symbolic_motifs": 2,
    "voice_profile": 1,
    "thematic_constraints": 3,
    "key_entities": 5
  },
  "error": null
}
```

### Post-Import Pattern Extraction

**Endpoint:** `POST /projects/{project_id}/extract-patterns`
**Returns:** 200 OK

Triggers pattern extraction on an already-imported project's story text. The service retrieves the source text from the project's draft artifacts (P-300 output chapters) or, if available, from the raw story text stored during initial import via Story Import. If no source text is found, returns `status="failed"` with error "no source text available for pattern extraction". Merges extracted patterns into the existing project's foundation revision as a new revision entry.

**Response (200):**
```json
{
  "status": "completed",
  "patterns_extracted": 14,
  "merged_into_project": true,
  "error": null
}
```

### Job Payload Extension

New fields for adventure generation jobs:
```python
{
    "phase": "P-100" | "P-300",
    "pattern_context": {
        "source_type": "narrative",
        "generation_mode": "same_world",
        "archetypal_patterns": [...],
        "narrative_structures": [...],
        "world_rules": [...],
        "voice_profile": {...},
        "thematic_constraints": [...]
    },
    "author_prompt": "Write an adventure where the hero discovers...",  # per-chapter
}
```

## Extraction Schema

### Narrative-Specific Patterns (NEW)

```python
@dataclass
class NarrativePattern:
    pacing: str                  # fast | slow | variable | episodic
    chapter_structure: str       # hook-middle-resolution | open-ended | cliffhanger
    conflict_type: str           # internal | external | both
    dialogue_style: str          # terse | descriptive | humorous | poetic | naturalistic
    scene_transition: str        # fade | cut | cliffhanger | thematic_bridge


@dataclass
class VoiceProfile:
    narrative_voice: str         # omniscient | intimate | detached | unreliable
    sentence_rhythm: str         # staccato | flowing | varied | rhythmic
    descriptive_density: str     # sparse | moderate | rich
    humor_level: str             # none | subtle | wry | overt | satirical
    emotional_temperature: str   # cold | warm | neutral | volatile


@dataclass
class ThematicConstraint:
    theme: str                   # "redemption through sacrifice"
    moral_stance: str            # "meritocracy fails; compassion prevails"
    recurring_questions: list[str]  # ["Can power be trusted?", "What is home?"]
    forbidden_elements: list[str]   # Things this story's DNA never does
```

### Existing Dataclasses (Reused/Generalized)

- `ArchetypalPattern` — unchanged
- `NarrativeStructure` — unchanged
- `CosmicRule` → generalized as `WorldRule` (same structure, broader naming)
- `SymbolicMotif` — unchanged
- `MythosEntity` → `StoryEntity` (same structure, broader naming)
- `Relationship` — unchanged

### Container Analysis

```python
@dataclass
class PatternExtractionAnalysis:
    source_type: str             # mythology | narrative
    source_corpus: str           # AI-identified or user-provided
    generation_mode: str         # same_world | new_characters | transposed

    # Shared pattern layer
    archetypal_patterns: list[ArchetypalPattern]
    narrative_structures: list[NarrativeStructure]
    world_rules: list[WorldRule]           # generalized from CosmicRule
    symbolic_motifs: list[SymbolicMotif]

    # Thematic layer
    thematic_spine: str
    emotional_promise: str
    tone_and_voice_direction: str

    # Narrative-specific additions
    narrative_pattern: NarrativePattern | None
    voice_profile: VoiceProfile | None
    thematic_constraints: list[ThematicConstraint]

    # Entity layer
    key_entities: list[StoryEntity]        # generalized from MythosEntity
    entity_relationships: list[Relationship]
```

## Persistence Mapping

| Extracted Field | Persisted As | Table |
|----------------|--------------|-------|
| `thematic_spine`, `emotional_promise`, `tone` | FoundationProfile fields | foundation_revisions |
| `world_rules[]` | World Bible entries (type: "concept") | world_bible_entries |
| `symbolic_motifs[]` | World Bible entries (type: "concept") | world_bible_entries |
| `archetypal_patterns[].character_type` | Character archetypes | character_profiles |
| `key_entities[]` | Characters or World Bible entries | character_profiles / world_bible_entries |
| `entity_relationships[]` | Relationship edges | relationship_edges |
| `narrative_structures[]`, `archetypal_patterns[]` | FoundationProfile `narrative_constraints_json` | foundation_revisions |
| `voice_profile`, `narrative_pattern`, `thematic_constraints` | New JSON fields in foundation_revisions | foundation_revisions |

ManifestConfig extended with:
```python
pattern_source_type: str = ""        # mythology | narrative
pattern_generation_mode: str = ""    # same_world | new_characters | transposed
pattern_source_corpus: str = ""      # source story/tradition name
```

## Generation Integration

### P-100 Architect Prompt Adaptation

New `pattern_context` block injected based on generation mode:

**same_world:**
```
PATTERN CONTEXT (Same World Mode):
Source: {source_corpus}
Setting: Use the established world and characters as-is.
Your task: Create a new adventure following these narrative patterns.

Archetypal Patterns to Follow:
{archetypal_patterns}

World Rules (must be obeyed):
{world_rules}

Voice & Style Guide:
{voice_profile}
```

**new_characters:**
```
PATTERN CONTEXT (New Characters Mode):
Source: {source_corpus}
Setting: Same world, but create original characters who fulfill these archetypal roles.

Archetypal Roles to Fill:
{archetypal_patterns}

World Rules (must be obeyed):
{world_rules}
```

**transposed:**
```
PATTERN CONTEXT (Transposed Mode):
Source: {source_corpus}
Your task: Map these archetypal patterns and narrative structures to a new setting.

Patterns to Transpose:
{archetypal_patterns}

Structural Rules (adapt to new world):
{world_rules}
```

### P-300 Drafter Prompt Adaptation

SceneContextService extended with `pattern_guidance` field. Injection order:
1. Character anchors (existing)
2. World facts (existing)
3. **Pattern guidance (NEW)** — world rules as hard constraints, voice profile as style guide
4. Prior chapter summaries (existing)
5. **Author prompt (NEW)** — "AUTHOR DIRECTION: {author_prompt}"

### Author Prompt Injection

Per-chapter author direction injected into P-300 system prompt after pattern context:
```
AUTHOR DIRECTION:
{author_prompt}

Follow the pattern context above while fulfilling this author direction.
```

## Components

### New Files

| File | Responsibility |
|------|---------------|
| `app/services/pattern_extraction.py` | PatternExtractionService (generalized from MythosExtractionService) |
| `app/schemas/pattern_extraction.py` | PatternExtractionAnalysis + narrative-specific dataclasses |
| `tests/test_pattern_extraction.py` | Unit tests for extraction, parsing, persistence, prompt builders |

### Modified Files

| File | Change |
|------|--------|
| `app/services/runtime_prompts.py` | Add `build_narrative_analysis_request()`; adapt P-100/P-300 for pattern_context injection |
| `app/api/projects.py` | Add `POST /projects/import-patterns` and `POST /projects/{id}/extract-patterns` |
| `app/main.py` | Wire PatternExtractionService, register routes |
| `app/schemas/manifest.py` | Add `pattern_source_type`, `pattern_generation_mode`, `pattern_source_corpus` |
| `app/services/scene_context.py` | Extend SceneContext with `pattern_guidance` field |
| `app/services/story_import.py` | MythosExtractionService becomes thin wrapper around PatternExtractionService |
| Frontend: StoryImportModal.tsx | Third tab: "Extract Patterns" |
| Frontend: Planning workspace | New "Generate Adventure" panel with mode selector and author prompt input |

## Error Handling

- `PatternExtractionError(ValueError)` — caught, returns `status="failed"` response
- `InferenceBackendError` — caught, returns `status="failed"` with error code
- `pydantic.ValidationError` — caught, wrapped as `PatternExtractionError`
- LLM extraction failure never blocks project creation — partial results accepted with warning
- Post-import extraction on project without story text returns clear error

## Testing Strategy

1. Mock LLM response with known narrative analysis output → verify schema parsing
2. Verify narrative_pattern, voice_profile, thematic_constraints parsed correctly
3. Verify entities persisted to correct tables alongside pattern data
4. Verify generation_mode and source_type stored in manifest
5. Integration test: full pipeline from import through P-100 with pattern context injection
6. Test all three generation modes produce different prompt contexts
7. Test author prompt injection into P-300
8. Backward compatibility: existing mythos extraction still works via wrapper

## Out of Scope (Future)

- Curated story library (pre-analyzed corpora)
- Multi-source blending (e.g., extract patterns from 3 stories, blend DNA)
- Frontend visualization of extracted patterns (pattern graph, archetype map)
- Automated pattern comparison between source and generated content
- Consistency critic pattern compliance check (dedicated narrative_consistency rules engine)
