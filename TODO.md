# TODO

## Current Truth

- The active documentation surface is `README.md`, `AGENTS.md`, and the current docs under `docs/`.
- Latest verified validation baseline (2026-05-17):
  - Backend parallel: 1473 passed, 7 skipped (~34s)
  - Backend serial: 51 passed (~2s)
  - Frontend tests: 627 passed (~13s)
  - Frontend lint/typecheck/build: all green (2070 modules)
- The React frontend is merged and is now the default shipped frontend surface.
- Inspect deep links and review-driven "Jump to Source" navigation are route-based and renderable through the existing inspect screen.
- Temporary review notes, executor task dumps, and stale readiness checklists belong under `docs/archive/`, not in the active docs surface.

## Active Backlog

### Pending Work

#### AI Relationship Extraction — Frontend JSON Encoding Bug (2026-05-10)

The "AI Extract" button in the Relationships tab works end-to-end but has a subtle frontend encoding issue:

- **Root cause**: `ConvertTo-Json` in PowerShell adds UTF-8 BOM (`\ufeff`) and converts strings to objects with `"value"` keys. The browser's fetch sends malformed JSON, causing 422 errors on the backend.
- **Symptom**: Clicking "AI Extract" shows "Server error occurred" but the endpoint works via direct API calls (curl).
- **Fix applied**: Moved `RelationshipExtractRequest` class to module level in `story_development.py` (line 832) to resolve FastAPI's string annotation issue. Added `Body(...)`/`Query(...)` annotations. Passed `inferencer` to router build in `main.py`.
- **Remaining**: Frontend button may fail intermittently due to JSON encoding. Direct API calls work reliably. The extraction logic, LLM prompt, and persistence all work correctly.

#### Cytoscape.js Graph Visualization (https://js.cytoscape.org/, MIT license)

Replace SVG-based `RelationshipMapGraph` and `ArcStageMapFlow` with Cytoscape.js for interactive, force-directed graph visualization. Cytoscape provides zoom/pan, drag nodes, dynamic layouts, extension ecosystem, and performant rendering for large graphs — all unavailable in hand-rolled SVG.

**Use cases**:

1. **Character Relationship Graph** — replace existing `RelationshipMapGraph` (circular layout, no zoom/pan). Nodes = characters, edges = relationships with `relation_kind` styling. Force-directed layout reveals clusters (family, allies, enemies) organically.
2. **Story Timeline Graph** — nodes = scenes/chapters arranged chronologically. Edges = narrative dependencies (prerequisite events, concurrent plotlines). Multi-layer tracks per POV/character arc. Color-coded by narrative stage (exposition → climax → resolution).
3. **Arc Progression Graph** — nodes = story beats/stages per arc. Edges = sequential progression. Parallel arcs visualized as layered paths. Divergence points (branch decisions) shown as fork nodes.
4. **World Entity Relationship Graph** — nodes = world bible entries (locations, cultures, factions, species, magic systems). Edges = connections (faction A allied with faction B, location X part of culture Y, magic system Z used by species W). Reveals worldbuilding gaps and isolated elements.
5. **Scene Dependency Graph** — nodes = scenes. Edges = causal dependencies (scene B requires outcome of scene A). Highlights bottlenecks, parallelizable scenes, and ordering constraints for batch drafting.
6. **Canon Packet Graph** — nodes = characters, world entries, arcs, continuity threads included in generation packet. Edges = cross-references (character appears in arc, location tied to culture). Visualizes packet composition and budget distribution.
7. **Plotline Convergence Graph** — nodes = plot events. Edges = which plotlines converge/diverge at key moments. Identifies sagging middles (sparse connections) and climax density (high-degree nodes).
8. **Character Arc-over-Time Graph** — x-axis = chapter/scene position, y-axis = character state (goal progress, relationship changes, internal growth). Multiple characters plotted as paths. Reveals pacing issues where arcs stall or overlap excessively.

**Implementation plan**:
- `npm install cytoscape` (core library, ~35KB gzipped)
- Optional extensions: `cytoscape-dagre` (hierarchical layout for timelines), `cytoscape-cola` (force-directed with constraints), `cytoscape-popper` (tooltips)
- Shared `CytoscapeGraph` component accepting `nodes`, `edges`, `layout`, `extensions` props
- Replace `RelationshipMapGraph` first (highest impact, existing data model maps directly to Cytoscape)
- Add timeline graph as new component in PlanningView (no existing equivalent)

**Data models** (existing backend entities map naturally):
- Characters → nodes with `display_name`, `role_in_story` labels
- Relationships → edges with `relation_kind` determining color/style
- World bible entries → nodes grouped by `entry_type`
- Arc stage maps → sequential node chains with `stage_kind` styling
- Scenes/chapters → timeline nodes ordered by `sequence_position`
- Continuity threads → cross-cutting edges linking related elements

#### Feature Tiers: Basic vs Advanced (Onboarding Reduction)

Research showed competitors suffer from feature overload — Scrivener has 20+ features, Campfire has 18 modules, Plottr has 40+ templates. Reduce cognitive load by splitting features into tiers users unlock progressively.

**Basic tier** (minimally needed to generate and edit a story):
- **Project creation**: Guided setup wizard or manual manifest config (genre, tone, premise)
- **Foundation**: Core story premise, logline, thematic spine — the "what is this story about" document
- **Characters**: Character list with display name, role, goal, conflict — enough to populate canon packet
- **Planning**: Sequences → chapters → scenes hierarchy; ability to create/edit/reorder
- **Writing**: Draft editor with word count, chapter navigation, autosave
- **Generation**: Submit generation run (P-100 architect → P-300 drafter → P-400 compiler), view output
- **Review**: Read generated chapters, make edits, track changes

Hidden from basic users: arcs, branches, decisions, flow editor, world bible, relationships, canon customization, brainstorm, braindump, inspect/job lineage, role-model checker, backup management, API keys, pattern library, mythos library.

**Advanced tier** (unlocked when user needs more control):
- **World Bible**: Typed entries (locations, cultures, species, magic systems) with continuity tracking
- **Character Relationships**: Graph visualization showing connections between characters
- **Arcs**: Character/story arc candidates, stage maps, selection scoring
- **Story Branching**: Alternative story paths with comparison and merge decisions
- **Flow Editor**: Custom pipeline phase configuration (reorder, enable/disable stages)
- **Canon Customization**: Annotation system, profile management, packet preview for generation runs
- **Brainstorm**: Idea capture, clustering, promote-to-planning workflow
- **Braindump**: Freeform session capture with AI organization
- **Inspect/Job Lineage**: Execution timeline, step records, artifact lineage, attempt history
- **Role-Model Checker**: Per-role quality evaluation with retry and lineage tracking
- **Pattern Library**: Archetypal pattern extraction, CRUD management, injection into prompts
- **Mythos Library**: Mythological entry extraction, materialization to editable entries
- **Backup Management**: Create/list/restore/delete project backups
- **API Keys**: Key creation, permission management, revocation

**Unlock mechanism** (proposal):
- Start with 7 basic tabs visible in PlanningView sidebar (Manifest, Foundation, Characters, Planning, Writing, Generate, Review)
- "Advanced" toggle in settings reveals remaining tabs (World Bible, Relationships, Arcs, Branches, Flow, Canon, Brainstorm, Braindump, Inspect, Checker)
- Alternatively: auto-unlock advanced tabs when user creates content triggering them (e.g., creating 3+ characters unlocks Relationships tab; creating first world bible entry unlocks World Bible tab)
- Progress indicator shows "X of Y features unlocked" to encourage exploration without overwhelming

#### Persistence and Runtime Expansion

- [x] Persist chapter-packet, sequence, and storyboard cards through lineage-aware registration.
  - Completed: `ChapterPacketService.register_packet_as_lineage()`, `SequencePlanService.register_plan_as_lineage()`, `StoryboardCardService.register_card_as_lineage()` now tested with 12 integration tests in `tests/test_lineage_aware_artifacts.py`. Bugfixes: added missing `StoryArtifactLifecycleState` import to `storyboard_cards.py`, moved `get_packet` call inside try block in `chapter_packets.py`.
- [x] Expand manuscript-assist integration tests.
  - Completed: 15 integration tests in `tests/test_manuscript_assist_integration.py` covering manuscript document CRUD, revision suggestion CRUD, cross-project isolation, and document filtering.
- [x] Add broader integration coverage for orchestration and runtime behavior.
   - Completed: 14 new E2E tests across `tests/test_executor_e2e_runtime.py` and `tests/test_story_bible_lineage.py` covering: checker report persistence, deterministic critic, P-400 missing upstream artifacts, staged/backup file cleanup, project isolation, job status transitions, job retry attempts, P-400 empty output, full pipeline order guarantee, story-bible content hash stability, fallback file read, and supersession chain verification.

### Story Import LLM Prompt Robustness -- All Complete
- Rewrote `build_import_analysis_request()` system prompt with clean JSON template, POV identification guide, story structure guide, exact enum constraints, and 7-point validation checklist
- Implemented `_map_llm_fields()` post-processing mapper in `story_import.py` for known LLM field name substitutions:
  - `world_bible`: name->title, description->summary, significance->append to summary, missing entry_type inference from title keywords (40+ synonym mappings)
  - `story_arcs`: description->summary, type->tags, missing stage_map defaults
  - `sequences`: name->title, description->summary, missing chapters defaults
  - `characters`: string-to-array coercion for contradictions, secrets, values, taboos, continuity_facts
  - `narrative_constraints`: string-to-array coercion
- Integrated mapper into `_analyze_story()` pipeline before Pydantic validation
- Added 8 unit/integration tests (`TestLLMFieldMapper`, `TestMapperIntegration`) and 30 prompt content completeness tests
- LLM validation against real test story ("The Man Who Would Be King"): produces valid schema-compliant output with 3 characters, 3 world bible entries, 2 arcs, 3 sequences
- Updated test baseline: 802 -> 840 passed (+38 new tests)

### Frontend-Backend Integration Audit -- All Complete
- Comprehensive audit of all 18 frontend service files, 67+ components, 7 views, 8 backend routers
- Identified and removed 37 dead service functions (42% of exports) across 14 files
- Removed 7 duplicate relationship helper functions from both characters.ts and relationships.ts
- Added Story Import UI: StoryImportModal component with form, validation, loading/error states, integration into ProjectList
- Verified all 13/13 feature areas backend-to-frontend linked
- Validation (at time of completion): 802 passed, 9 skipped, typecheck passed, build passed, lint passed, qc.py adverse review passed with 0 findings
- Dead code cleanup reduced exports from 112 to 75 across all service files

## Completed Milestones (Summary)

Full details archived in `docs/archive/`.

### Studio Desk Serial Roadmap (2026-05-16)

5-stage serial implementation with verification gates (lint, typecheck, build, tests) passing before each stage advanced. All stages merged to `codex/main`.

- **Stage 1** (`fb5d912`): Studio shell with command bar (Capture/Write/Generate/Review/Inspect), project rail (Ideas/Characters/World Bible/Relationships/Canon/Jobs/Notes), and context panel shell. `studioStore` Zustand store with panel/rail state. Route registered at `/workspace/:projectId/studio`.
- **Stage 2** (`620240b`): `useMergedSuggestions` hook extraction — merges `RevisionSuggestion[]` and `LLMRevisionSuggestion[]`, routes accept/reject/archive to correct handler. `StudioSuggestionsPanel` wired into context panel. `WritingView` refactored to delegate suggestion merging to shared hook.
- **Stage 3** (`8ee6d5b`): Compact panels for generation/review/inspect. `StudioGenerationPanel` uses `useGenerationController`. `StudioReviewPanel` tab-based UI for Findings/Inspect Links. `StudioInspectPanel` shows guidance text when no run selected. Route views swapped for compact panels in `StudioContextPanel`.
- **Stage 4** (`85de3e4`): Canon annotation wiring for Characters/World Bible panels. `CharacterBuilder` and `WorldBibleWorkspace` already accept `canonAnnotations` and `onAnnoteField` props — no code changes needed, just prop threading.
- **Stage 5** (`b40db1e`): Responsive `xl:` breakpoint layout with absolute-positioned overlay drawers below xl width. Desktop grid preserved above xl. Mobile Project/Context drawer toggle buttons in header. Close drawers button with aria-label. Store helpers `toggleLeftRail`, `toggleContextPanel`, `closeDrawers`.

Components: 11 Studio components in `frontend/src/components/studio/`, 1 hook (`useMergedSuggestions`), 1 store (`studioStore`), 1 view (`StudioView`). 13 integration tests + 4 hook unit tests.

Design spec: `docs/superpowers/specs/2026-05-16-studio-desk-redesign-design.md`
Stage plans: `docs/superpowers/plans/2026-05-16-studio-desk-stage-{1-5}.md` + serial roadmap

### Guided Setup Planning Extension (2026-05-08)

- Conversational project creation wizard at `/setup-wizard` now generates story planning (sequences + chapters) alongside config, foundation, characters, world bible, and arcs
- Backend: `GuidedSequence` / `GuidedChapter` Pydantic schemas; `_parse_analyze_response` merge logic for sequences/chapters; `_insert_sequence`, `_insert_chapter` persistence with character name→ID resolution and sequence chapter_ids backfill; extended `_GUIDED_SETUP_SYSTEM_PROMPT` with category 10 (story structure)
- Frontend: `GuidedSequence` / `GuidedChapter` TypeScript interfaces; extended `ExtractedFields`, `emptyExtractedFields`, `GuidedSetupCreateResponse`; FieldPreview Sequences/Chapters collapsible panels with auto-open-on-first-data behavior
- Test coverage: 14 new tests across schema validation, parsing merge, persistence, FK resolution, response counts
- Design spec: `docs/superpowers/specs/2026-05-08-guided-setup-planning-design.md`
- Implementation plan: `docs/superpowers/plans/2026-05-08-guided-setup-planning.md`

### Extraction Services Consolidation (2026-04-28)

- Shared utilities: `app/utils/json_extract.py` (3-tier JSON parser, 27 tests), `app/utils/db_inserts.py` (SQL insert helpers, hash_id, json_safe, 30 tests), `app/utils/manifest.py` (manifest update helper, 6 tests)
- Race condition fixes: `BEGIN IMMEDIATE` for SQLite concurrent-write safety, atomic `next_revision_number()` helper
- Efficiency: repository load moved outside multi-chapter loop in `local_executor.py`
- Frontend: mythology generation modes fixed, union type replaced with `MythosExtractionResponse`
- Prompt quality: JSON guardrails added to narrative/mythos/story import prompts; P-100 pattern context typed with `PatternExtractionAnalysis`
- Minor cleanups: Protocol types for service injection, simplified `_has_pattern_content()`, removed unused import
- Net change: ~580 lines of duplicated code removed, +428 shared utility lines, -152 net production code
- Test coverage: 1103 collected (+72 new tests), 217/217 critical subset passed
- Completion report: `docs/Extraction Services Consolidation - Completion Report v1.0.md`

### Multi-Chapter Generation Completion (2026-04-26)

- ChapterSummarizerService: LLM-based chapter summarization with error tolerance
- Batch multi-chapter mode: `chapter_ids` list payload triggers sequential drafting in single job
- Prior context propagation: summaries injected into subsequent chapters (capped at 3)
- ManuscriptDocument auto-creation: persisted after each chapter draft
- Test coverage (at time of completion): 907 passed, 9 skipped (+7 tests for summarizer + prompt builder)

### v1.0 Release -- All Complete
All 14 v1.0 release items (V1-001 through V1-015) completed and scope-verified.
The product surface includes routed planning, writing, review, and inspect workspaces
with real API backing.

### Backend Security & Reliability -- All Complete
- SEC-01 through SEC-05: Input validation, CORS, request size limits, path traversal, rate limiting
- REL-01 through REL-10: Circuit breaker, idempotency, thread safety, backup, health checks,
  API key auth, authorization, telemetry, file permissions, audit logging
- All 319 security/reliability tests pass

### Core Runtime & Protocol -- All Complete
- Deterministic job orchestration with P-100 through P-400 phases
- Role-model checker with runtime-backed per-role evaluation
- Attempt lineage, step records, artifact lineage, supersession behavior
- Projection endpoints: GET /jobs/{id}/steps, /lineage, /attempts and /role-model-checker equivalents

### Story Development Backend -- All Complete
- BE-01 through BE-11E: Schemas, persistence, services, and API surface for branching,
  decisions, review, planning, drafting, characters, world bible, arcs, and brainstorm
- 802 tests passing across the full suite (at time of completion). Bugfix: `create_inspect_link` incorrectly normalized `object_kind` to `StoryObjectType`, rejecting free-form strings like "job", "checker", "manuscript". Rewrote `test_review_routing_post.py` with proper `tmp_path` DB isolation.

### FlowEditor Stage Editing -- All Complete
- Add stage: dialog with kind selector and name input
- Rename stage: inline dialog with save/cancel
- Disable/Enable toggle button on each stage
- Archive button (hidden for archived stages)
- Delete with confirmation guard (custom stages only, default stages hidden)
- Type drift fixed: ACTIVE->ENABLED, added OPTIONAL state, writer_notes field
- Fix: uppercase enum values (ENABLED/DISABLED/ARCHIVED) in frontend service

### Relationship Map Graph -- All Complete
- New `relationships` tab in PlanningView with graph visualization
- `RelationshipMapGraph` component: SVG-based graph with circular layout, curved edges, hover/click interactions, relation_kind color coding, delete button on edges, legend
- `RelationshipList` component: panel view showing relationships as a list with relation_kind badges, tension indicators, and delete actions
- Full CRUD service: `getRelationships`, `createRelationship`, `updateRelationship`, `deleteRelationship`
- Character name map integration for readable node labels
- Dark mode support throughout

### Arc Stage Map Flow -- All Complete
- New `ArcStageMapFlow` component: SVG-based sequential flow visualization for arc stage maps
- Horizontal node layout with directional arrows between stages
- Color-coded narrative stage types (exposition, rising action, climax, resolution, etc.)
- Multi-stage-map support with selector dropdown for projects with multiple arc candidates
- Active arc indicator badge, stage timeline footer, dark mode support
- Replaces plain text comma-separated stage map display in PlanningView arcs tab

### Deferred Mutations -- All Complete
- Arc selection mutations: POST /arcs/candidates, POST /arcs/comparisons, POST /arcs/selections, PATCH /arcs/selections/{id}, DELETE /arcs/selections/{id}, POST /arcs/stage-maps
- Character relationship mutations: GET /relationships (list-all), PATCH /relationships/{id}, DELETE /relationships/{id}
- Planning board reorder: POST /planning/reorder (supports sequence, chapter, scene plan kinds)
- 23 new integration tests across test_deferred_mutations.py

### Planning Inline Edit UI -- All Complete
- Added inline update/edit forms for sequence plans, chapter plans, scene plans, and beat plans
- Edit button on each card opens inline form pre-populated with current values
- Save/Cancel inline actions with optimistic invalidation
- Editable fields match backend update request schemas (no sequence_id/chapter_id on update - those are create-only)
- Dark mode support throughout

### ArcComparisonGraph Hook Fix -- All Complete
- Fixed pre-existing lint errors (React Hooks rules-of-hooks violations at lines 206, 219)
- Moved useMemo hooks before early return guard
- Converted early return to conditional render for empty state
- Uses useMemo with null guard for selectedComparison

### Arc Mutation Service Layer -- All Complete
- Added createArcCandidate, createArcComparison to frontend service layer
- Added createArcSelection, updateArcSelection, deleteArcSelection to frontend service layer
- Added createArcStageMap to frontend service layer
- Added corresponding request type definitions: ArcCandidateCreateRequest, ArcComparisonCreateRequest, ArcSelectionCreateRequest, ArcSelectionUpdateRequest, ArcStageMapCreateRequest
- Backend endpoints existed (deferred mutations milestone) but frontend service functions were missing

### Planning Reorder Service -- All Complete
- Added reorderPlanObjects service function to frontend planning service layer
- Added PlanningReorderRequest type: project_id, plan_kind ('sequence'|'chapter'|'scene'), ordered_plan_ids
- Backend endpoint POST /planning/reorder now has frontend service support

### Arc Management + Planning Reorder UI -- All Complete
- Arc candidates: + New Arc create form (arc_id, name, summary), Select/Deselect buttons on each card
- Stage Maps: create form with arc dropdown, stage kind chips (exposition, inciting_incident, rising_action, complication, crisis, climax, falling_action, resolution), optional notes
- Planning reordering: Chevron up/down buttons on sequence, chapter, and scene cards
- Bug fixes: arc_id required in ArcCandidateCreateRequest frontend type, deleteArcSelection project_id query param, ArcSelectionCreateRequest.selected_arc accepts string or object
- Removed unused getSelectedArc import, inlined logic in PlanningView
- Validation: 802 passed, 9 skipped, typecheck passed, build passed, lint passed

### Unwired API Exposure -- All Complete (2026-05-05)
- Shared infrastructure: `<InlineActions>` component (~40 lines, reuses Button variants + useApiMutation), `useConfirmation` hook
- Phase A (critical gaps): Archive suggestion wiring in AidsPanel, relationship update/delete wiring in RelationshipMapGraph, arc selection actions in ArcsTab
- Phase B (feature completeness): Mythos library CRUD with delete action, Pattern library CRUD with delete action, Foundation history + review cues tabs, Brainstorm promote workflow
- Phase C (admin features): Backup management in SettingsPanel (create/list/restore/delete), API key management in SettingsPanel (create/list/revoke)
- New hooks: useRelationships, useArcs, useMythosLibrary, usePatternLibrary, useFoundation, useBrainstorm, useBackups, useAuthKeys, useConfirmation, useApiQuery
- New types: BackupInfo (`frontend/src/types/backup.ts`), ApiKeyInfo (`frontend/src/types/authKeys.ts`)
- Backend restoration: `ProjectMaintenanceService` restored from `codex/project-maintenance` branch (orphan detection, cleanup, audit log truncation, database compaction)
- Validation: 1413 parallel + 51 serial backend tests, 522 frontend tests, lint/typecheck/build green

### Testing
- Smoke coverage, persistence coverage, contract coverage, failure-mode coverage
- CI runs full suite on push and pull request
