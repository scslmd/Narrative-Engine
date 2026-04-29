# Mythos Extraction & Pattern-Based Story Generation — Design Spec

**Date:** 2026-04-26
**Status:** Approved by user
**Complexity:** Medium — new service, new schema, prompt engineering, generation integration

## Goal

Enable users to paste mythology texts (Greek, Norse, Egyptian, etc.), have the LLM extract archetypal patterns, narrative structures, cosmic rules, and symbolic motifs, then generate original stories that follow those mythological storytelling DNA — either in the same world, transposed to a new setting, or as pure pattern application.

## Architecture

Dedicated `MythosExtractionService` with its own endpoint. Pattern-focused extraction (archetypes, narrative structures, thematic constraints) rather than entity cataloging. Extracted mythos becomes project foundation data. Generation mode (`same_world`, `transposed`, `pure_pattern`) stored in manifest, controls how P-100/P-300 apply constraints.

```
User pastes mythology texts or uploads file
    ↓
POST /projects/import-mythos (synchronous)
    ↓
MythosExtractionService.extract()
    ├─ build_mythos_analysis_request() → LLM call
    ├─ Parse JSON → MythosExtractionAnalysis
    └─ _transactional_import() → persist entities
    ↓
Project created with:
  - FoundationProfile (thematic spine, narrative constraints from mythos)
  - World Bible (cosmic rules, symbolic motifs as entries)
  - Character archetypes (pattern profiles, not specific gods)
  - Manifest: generation_mode + source_corpus
    ↓
User selects generation mode at import time:
  - same_world: Keep mythological setting, create original characters/plot
  - transposed: Map archetypes to new setting
  - pure_pattern: Apply narrative structures only, free-form world/genre
    ↓
P-100 Architect runs with mythos context injected per generation mode
    ↓
P-200 Sequencer creates chapter plans aligned to extracted patterns
    ↓
P-300 batch mode drafts chapters following mythos DNA
```

## API Contract

### Input

**Endpoint:** `POST /projects/import-mythos`
**Content-Type:** `multipart/form-data` (file) or `application/json` (paste)
**Returns:** 201 Created with extraction summary

**JSON mode:**
```json
{
  "text": "<raw mythology texts, up to 5M chars>",
  "source_corpus": "Greek Mythology",    // optional — AI extracts if omitted
  "generation_mode": "same_world"        // required: same_world | transposed | pure_pattern
}
```

**File mode:**
```json
{
  "file": "<.txt/.md file, up to 5M chars>",
  "source_corpus": null,                 // AI will identify
  "generation_mode": "transposed"
}
```

**Response (201):**
```json
{
  "status": "completed",
  "project_id": "<uuid>",
  "extraction": {
    "source_corpus": "Greek Mythology",
    "archetypal_patterns": 4,
    "narrative_structures": 2,
    "cosmic_rules": 5,
    "symbolic_motifs": 3
  },
  "error": null
}
```

### Source Corpus Identification

When `source_corpus` is omitted or null, the LLM identifies it from the text. Known traditions: Greek, Norse, Egyptian, Roman, Hindu, Japanese, Chinese, Celtic, Mesopotamian, African, Native American, Slavic, Persian. Falls back to `"Other: <custom label>"` for unrecognized traditions.

## Extraction Schema

### Core Pattern Layer

```python
@dataclass
class ArchetypalPattern:
    name: str                    # "hubris-fall-redemption", "trickster"
    description: str             # How it manifests in source texts
    character_type: str          # Archetype carrier: "hubristic hero", "cunning trickster"
    narrative_beats: list[str]   # ["rise", "transgression", "punishment", "suffering", "apotheosis"]
    examples_from_text: list[str]  # References from source material


@dataclass
class NarrativeStructure:
    name: str                    # "cyclical tragedy", "quest with escalating trials"
    phases: list[str]            # ["call", "transgression", "punishment", "redemption"]
    tension_curve: str           # "escalating divine retribution"
    resolution_type: str         # "bittersweet apotheosis", "tragic closure"


@dataclass
class CosmicRule:
    rule: str                    # "Fate cannot be escaped, only fulfilled"
    enforcement: str             # "Gods act as agents of moira (fate)"
    exceptions: list[str]        # ["prophecies can be misinterpreted"]


@dataclass
class SymbolicMotif:
    symbol: str                  # "serpent", "crossroads", "underworld journey"
    meaning: str                 # "transformation, hidden knowledge"
    narrative_function: str      # "marks threshold between worlds"
```

### Top-Level Analysis

```python
@dataclass
class MythosExtractionAnalysis:
    source_corpus: str           # AI-identified or user-provided
    generation_mode: str         # same_world | transposed | pure_pattern

    # Pattern layer (core)
    archetypal_patterns: list[ArchetypalPattern]
    narrative_structures: list[NarrativeStructure]
    cosmic_rules: list[CosmicRule]
    symbolic_motifs: list[SymbolicMotif]

    # Thematic layer (foundation)
    thematic_spine: str          # "hubris and divine retribution"
    emotional_promise: str       # "catharsis through tragic downfall"
    tone_and_voice_direction: str  # "epic, fatalistic, mythic register"

    # Entity layer (light — for same_world mode)
    key_entities: list[MythosEntity]   # Gods/places with archetypal roles
    entity_relationships: list[Relationship]  # Power dynamics, alliances
```

### MythosEntity (Minimal)

```python
@dataclass
class MythosEntity:
    name: str                    # "Zeus", "Underworld"
    entity_type: str             # deity | location | concept | force
    archetype: str               # "sky father", "threshold guardian"
    domain_or_power: str         # "oaths, hospitality, strangers"
    canonical_facts: list[str]   # Immutable facts from source texts
```

## Persistence Mapping

Extracted data maps to existing tables:

| Extracted Field | Persisted As | Table |
|----------------|--------------|-------|
| `thematic_spine`, `emotional_promise`, `tone` | FoundationProfile fields | foundation_profiles |
| `cosmic_rules[]` | World Bible entries (type: "concept") | world_bible_entries |
| `symbolic_motifs[]` | World Bible entries (type: "concept") | world_bible_entries |
| `archetypal_patterns[].character_type` | Character archetypes | character_profiles |
| `key_entities[]` | Characters or World Bible entries | character_profiles / world_bible_entries |
| `entity_relationships[]` | Relationship edges | relationship_edges |
| `narrative_structures[]`, `archetypal_patterns[]` | Stored in FoundationProfile `narrative_constraints` as JSON | foundation_profiles |

Generation mode and source corpus stored in ManifestConfig:
```python
class ManifestConfig(StrictSchemaModel):
    # ... existing fields ...
    mythos_source_corpus: str = ""
    mythos_generation_mode: str = ""  # same_world | transposed | pure_pattern
```

## Generation Integration

### P-100 Architect Prompt Adaptation

New `mythos_context` block injected based on generation mode:

**same_world:**
```
MYTHOS CONTEXT (Same World Mode):
Source tradition: {source_corpus}
Setting: Use the mythological world as-is. Gods, places, and cosmic rules exist.
Your task: Create original characters and a fresh storyline that follows these patterns.

Archetypal Patterns to Follow:
{archetypal_patterns}

Cosmic Rules (must be obeyed):
{cosmic_rules}
```

**transposed:**
```
MYTHOS CONTEXT (Transposed Mode):
Source tradition: {source_corpus}
Your task: Map these archetypal patterns to a new setting. The trickster becomes X, cosmic rules become Y.

Archetypal Patterns to Transpose:
{archetypal_patterns}

Structural Rules (adapt to new world):
{cosmic_rules}
```

**pure_pattern:**
```
MYTHOS CONTEXT (Pure Pattern Mode):
Source tradition: {source_corpus}
Your task: Follow these narrative structures and thematic constraints. World, genre, and setting are free-form.

Narrative Structures to Follow:
{narrative_structures}

Thematic Constraints:
{thematic_spine}
```

### P-300 Drafter Prompt Adaptation

SceneContextService already injects character anchors + world bible facts. New `mythos_constraints` block adds cosmic rules as hard constraints during drafting. Archetypal patterns guide character behavior per chapter.

### Consistency Critic Adaptation

New `mythos_consistency` check verifies the story obeys cosmic rules. If a character tries to escape fate in a Greek mythos story, the critic flags it unless the resolution shows them failing (per the cosmic rule).

## Components

### New Files

| File | Responsibility |
|------|---------------|
| `app/services/mythos_extraction.py` | MythosExtractionService (follows StoryImportService pattern) |
| `app/schemas/mythos_extraction.py` | MythosExtractionAnalysis + supporting dataclasses |
| `tests/test_mythos_extraction.py` | Unit tests for extraction, parsing, persistence |

### Modified Files

| File | Change |
|------|--------|
| `app/services/runtime_prompts.py` | Add `build_mythos_analysis_request()` prompt builder; adapt P-100/P-300 for mythos_context injection |
| `app/api/projects.py` | Add `POST /projects/import-mythos` endpoint |
| `app/main.py` | Wire MythosExtractionService, register route |
| `app/schemas/story_import.py` | Extend `_ENTRY_TYPE_SYNONYMS` with mythological types (deity, pantheon, realm, cosmic_law, prophecy) |
| `app/schemas/manifest.py` | Add `mythos_source_corpus`, `mythos_generation_mode` to ManifestConfig |
| `frontend/src/components/projects/StoryImportModal.tsx` | Add "Mythos Extraction" mode toggle with generation mode selector |

## Error Handling

- `MythosExtractionError(ValueError)` — caught, returns `status="failed"` response
- `InferenceBackendError` — caught, returns `status="failed"` with error code
- `pydantic.ValidationError` — caught, wrapped as `MythosExtractionError`
- LLM extraction failure never blocks project creation — partial results accepted with warning

## Testing Strategy

1. Mock LLM response with known Greek myth extraction output → verify schema parsing
2. Verify archetypal_patterns, narrative_structures, cosmic_rules parsed correctly
3. Verify entities persisted to correct tables (FoundationProfile, World Bible, Characters)
4. Verify generation_mode and source_corpus stored in manifest
5. Integration test: full pipeline from import through P-100 with mythos context injection
6. Test all three generation modes produce different prompt contexts
7. File upload mode: verify size validation, text extraction from .txt/.md files

## Out of Scope (Future)

- Curated mythology library (pre-loaded corpora)
- Multi-mythos blending (e.g., Greek + Norse hybrid)
- Frontend visualization of extracted patterns (pattern graph, archetype map)
- Mythos-specific consistency critic rules engine
