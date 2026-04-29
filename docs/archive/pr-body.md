## Summary

Generalize `MythosExtractionService` into `PatternExtractionService` that works on any story type via `source_type` parameter (`narrative` | `mythology`). Extract narrative DNA — archetypal patterns, voice profile, thematic constraints, world rules — then inject those patterns into the P-100/P-300 generation pipeline with per-chapter author prompts.

## What Changed

### Backend (20 files, +10,677 / -85 lines)

**New:**
- `app/schemas/pattern_extraction.py` — NarrativePattern, VoiceProfile, ThematicConstraint dataclasses + PatternExtractionAnalysis container + Pydantic schemas with validators
- `app/services/pattern_extraction.py` — PatternExtractionService with LLM dispatch, JSON parsing, transactional persistence to foundation_revisions/world_bible/characters
- `tests/test_pattern_extraction.py` — 100 tests covering schema, prompt builder, service, persistence, API wiring, backward compatibility
- `tests/test_pattern_guidance_scene_context.py` — 13 tests for SceneContext pattern guidance

**Modified:**
- `app/services/runtime_prompts.py` — `build_narrative_analysis_request()` + P-100/P-300 pattern context injection for 3 generation modes (same_world, new_characters, transposed)
- `app/services/scene_context.py` — PatternGuidance dataclass, SceneContext extended with `pattern_guidance` and `author_prompt` fields
- `app/api/projects.py` — `POST /projects/import-patterns` (201), `POST /projects/{id}/extract-patterns` (201)
- `app/schemas/manifest.py` — `pattern_source_type`, `pattern_generation_mode`, `pattern_source_corpus` fields on ManifestConfig

### Frontend
- `frontend/src/types/patternExtraction.ts` — TypeScript interfaces aligned with backend contracts
- `frontend/src/services/patternExtraction.ts` — `importPatterns()`, `extractPatternsPostImport()` using shared API client
- `frontend/src/components/projects/StoryImportModal.tsx` — Third tab: "Extract Patterns" with source type/generation mode selectors, corpus input, story textarea

### Documentation
- 6 core docs advanced to **v1.3** with Pattern Extraction feature documentation
- AGENTS.md updated: test baseline 1031 passed, new API endpoints documented, Pattern Extraction feature section added

## Validation

| Command | Result |
|---------|--------|
| `pytest -q -p no:cacheprovider` | **1031 passed, 9 skipped** (+100 tests) |
| `npm run lint` | passed |
| `npm run typecheck` | passed |
| `npm run build` | 1973 modules |

## Architecture

```
User pastes story text
    ↓
POST /projects/import-patterns (source_type: "narrative" | "mythology")
    ↓
PatternExtractionService.extract()
    ├─ source_type="narrative" → build_narrative_analysis_request() → LLM → JSON parse
    ├─ source_type="mythology" → delegate to MythosExtractionService (backward compat)
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
  3. P-100 Architect with pattern context injection
  4. P-300 Drafter with pattern guidance + author direction
    ↓
Original adventure generated following source story's patterns
```

## Backward Compatibility

- `MythosExtractionService` remains fully functional via delegation in PatternExtractionService
- Existing `/projects/import-mythos` endpoint unchanged
- All new parameters default to `None` — existing callers work without modification
