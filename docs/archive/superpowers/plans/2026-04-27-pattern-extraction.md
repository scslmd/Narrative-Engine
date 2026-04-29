# Pattern Extraction & Adventure Generation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generalize mythos extraction into a pattern extraction service that works on any story type, extract narrative DNA (archetypes, voice profile, thematic constraints), and inject those patterns into the generation pipeline with per-chapter author prompts.

**Architecture:** New `PatternExtractionService` with `source_type` parameter selects LLM prompt builder (narrative vs mythology). Narrative-specific dataclasses extend existing pattern types. SceneContext extended with `pattern_guidance` field for P-300 injection. ManifestConfig stores pattern metadata.

**Tech Stack:** Python/FastAPI backend, Pydantic schemas, SQLite persistence, React frontend (third import tab).

---

### Task 1: Narrative-Specific Dataclasses

**Files:**
- Create: `app/schemas/pattern_extraction.py`
- Test: `tests/test_pattern_extraction.py`

- [ ] Step 1: Write failing test for NarrativePattern, VoiceProfile, ThematicConstraint dataclasses
- [ ] Step 2: Run test to verify it fails (ModuleNotFoundError)
- [ ] Step 3: Create schema module with narrative-specific dataclasses
- [ ] Step 4: Run test to verify it passes (3 tests)
- [ ] Step 5: Commit

### Task 2: PatternExtractionAnalysis Container & Pydantic Schemas

**Files:**
- Modify: `app/schemas/pattern_extraction.py` — add container + request/response schemas
- Test: `tests/test_pattern_extraction.py`

- [ ] Step 1: Write failing test for PatternExtractionAnalysis, PatternExtractionRequest, validation
- [ ] Step 2: Run test to verify it fails (ImportError/AttributeError)
- [ ] Step 3: Add container dataclass and Pydantic schemas with source_type/generation_mode validators
- [ ] Step 4: Run test to verify it passes (6 tests total)
- [ ] Step 5: Commit

### Task 3: PatternExtractionService Constructor & Error Class

**Files:**
- Create: `app/services/pattern_extraction.py`
- Test: `tests/test_pattern_extraction.py`

- [ ] Step 1: Write failing test for PatternExtractionError and service constructor
- [ ] Step 2: Run test to verify it fails (ImportError)
- [ ] Step 3: Create service with constructor, error class, mythos service delegation
- [ ] Step 4: Run test to verify it passes (8 tests total)
- [ ] Step 5: Commit

### Task 4: Narrative Prompt Builder

**Files:**
- Modify: `app/services/runtime_prompts.py` — add `build_narrative_analysis_request()`
- Test: `tests/test_pattern_extraction.py`

- [ ] Step 1: Write failing test for narrative prompt builder
- [ ] Step 2: Run test to verify it fails (ImportError)
- [ ] Step 3: Implement build_narrative_analysis_request with JSON schema in system prompt
- [ ] Step 4: Run test to verify it passes
- [ ] Step 5: Commit

### Task 5: PatternExtractionService.extract() Method

**Files:**
- Modify: `app/services/pattern_extraction.py` — add extract(), _parse_llm_json(), _build_analysis()
- Test: `tests/test_pattern_extraction.py`

- [ ] Step 1: Write failing test for extract() with mocked LLM response
- [ ] Step 2: Run test to verify it fails (AttributeError)
- [ ] Step 3: Implement extract() with source_type dispatch, LLM call, JSON parsing, analysis building
- [ ] Step 4: Run test to verify it passes
- [ ] Step 5: Commit

### Task 6: Transactional Import & Persistence

**Files:**
- Modify: `app/services/pattern_extraction.py` — add `_create_and_persist()`, `_update_manifest()`
- Test: `tests/test_pattern_extraction.py`

- [ ] Step 1: Write failing test for project creation and narrative-specific field persistence
- [ ] Step 2: Run test to verify it fails (AttributeError)
- [ ] Step 3: Implement transactional import with foundation_revisions, world_bible_entries, character_profiles, relationship_edges
- [ ] Step 4: Run test to verify it passes
- [ ] Step 5: Commit

### Task 7: ManifestConfig Extension & API Endpoints

**Files:**
- Modify: `app/schemas/manifest.py` — add pattern_source_type, pattern_generation_mode, pattern_source_corpus
- Modify: `app/api/projects.py` — add import-patterns and extract-patterns endpoints
- Test: `tests/test_pattern_extraction.py`

- [ ] Step 1: Write failing test for ManifestConfig pattern fields
- [ ] Step 2: Run test to verify it fails (TypeError)
- [ ] Step 3: Extend ManifestConfig with pattern fields
- [ ] Step 4: Run test to verify it passes
- [ ] Step 5: Write failing test for API endpoint
- [ ] Step 6: Add POST /projects/import-patterns and POST /projects/{id}/extract-patterns endpoints
- [ ] Step 7: Run test to verify it passes
- [ ] Step 8: Commit

### Task 8: Main.py Wiring & Backward Compatibility

**Files:**
- Modify: `app/main.py` — wire PatternExtractionService
- Test: `tests/test_pattern_extraction.py`

- [ ] Step 1: Write failing test for service wiring and mythos backward compatibility
- [ ] Step 2: Run test to verify it fails (AttributeError)
- [ ] Step 3: Wire PatternExtractionService in main.py
- [ ] Step 4: Run test to verify it passes
- [ ] Step 5: Commit

### Task 9: SceneContext Extension with Pattern Guidance

**Files:**
- Modify: `app/services/scene_context.py` — add PatternGuidance dataclass, extend SceneContext
- Test: `tests/test_pattern_extraction.py`

- [ ] Step 1: Write failing test for pattern guidance and author prompt in SceneContext
- [ ] Step 2: Run test to verify it fails (ImportError)
- [ ] Step 3: Add PatternGuidance dataclass, extend SceneContext with pattern_guidance and author_prompt fields
- [ ] Step 4: Update to_prompt_string() to include pattern guidance and author direction sections
- [ ] Step 5: Run test to verify it passes
- [ ] Step 6: Commit

### Task 10: P-100/P-300 Prompt Adaptation for Pattern Context Injection

**Files:**
- Modify: `app/services/runtime_prompts.py` — adapt P-100/P-300 prompts for pattern context
- Test: `tests/test_pattern_extraction.py`

- [ ] Step 1: Write failing test for P-100 prompt with pattern context and P-300 with author direction
- [ ] Step 2: Run test to verify it fails (TypeError)
- [ ] Step 3: Add pattern_context parameter to build_architect_request(), implement mode-specific blocks
- [ ] Step 4: Adapt build_drafter_request() to include scene context with pattern guidance
- [ ] Step 5: Run test to verify it passes
- [ ] Step 6: Commit

### Task 11: Frontend Types & Service

**Files:**
- Create: `frontend/src/types/patternExtraction.ts`
- Create: `frontend/src/services/patternExtraction.ts`

- [ ] Step 1: Create TypeScript types for PatternExtractionRequest, Summary, Response
- [ ] Step 2: Create service with importPatterns() and extractPatternsPostImport() functions
- [ ] Step 3: Verify typecheck passes
- [ ] Step 4: Commit

### Task 12: StoryImportModal Third Tab & Basic UI

**Files:**
- Modify: `frontend/src/components/projects/StoryImportModal.tsx` — add third tab for pattern extraction

- [ ] Step 1: Add "Extract Patterns" tab with source type selector, generation mode selector, corpus input, story textarea
- [ ] Step 2: Wire form to importPatterns service call with navigation on success
- [ ] Step 3: Verify lint passes
- [ ] Step 4: Commit

### Task 13: Full Validation Suite & AGENTS.md Update

**Files:**
- Modify: `AGENTS.md` — update test baseline, document new feature

- [ ] Step 1: Run full test suite — `python -m pytest -q -p no:cacheprovider`
- [ ] Step 2: Run frontend checks — lint, typecheck, build
- [ ] Step 3: Update AGENTS.md with pattern extraction documentation and test baseline
- [ ] Step 4: Commit

---

## Self-Review Checklist

### Spec Coverage
- [x] Narrative-specific dataclasses (NarrativePattern, VoiceProfile, ThematicConstraint) — Task 1
- [x] PatternExtractionAnalysis container + Pydantic schemas — Task 2
- [x] Prompt builder for narrative analysis — Task 4
- [x] PatternExtractionService with source_type dispatch — Tasks 3, 5
- [x] Transactional import with persistence — Task 6
- [x] ManifestConfig extension — Task 7
- [x] API endpoints (import-patterns, extract-patterns) — Task 7
- [x] Main.py wiring — Task 8
- [x] SceneContext extension with pattern_guidance — Task 9
- [x] P-100/P-300 prompt adaptation — Task 10
- [x] Frontend types and service — Task 11
- [x] StoryImportModal third tab — Task 12

### Placeholder Scan
- No TBD/TODO patterns found
- All tasks have complete step definitions

### Type Consistency
- WorldRule, StoryEntity used consistently across schema and persistence
- VoiceProfile, NarrativePattern, ThematicConstraint referenced correctly in all tasks
- SceneContext pattern_guidance field properly typed as PatternGuidance | None

## Execution Notes

1. Task order matters: Tasks 1-2 establish schema foundation. Tasks 3-6 build the service. Tasks 7-8 wire everything together. Tasks 9-10 integrate with generation pipeline. Tasks 11-12 add frontend.
2. Backward compatibility: MythosExtractionService remains functional via delegation in PatternExtractionService
3. Testing strategy: Each task includes failing tests first, then implementation
4. Commit frequency: Commit after each task completes (13 commits total)
