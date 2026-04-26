# TODO

## Current Truth

- The active documentation surface is `README.md`, `AGENTS.md`, `docs/BACKEND_API_REFERENCE.md`, and the current docs under `docs/`.
- Latest verified validation baseline:
  - `python -m pytest -q -p no:cacheprovider` -> `802 passed, 9 skipped` (0 pre-existing failures. Remaining 9 skips are platform-specific.)
  - `cd frontend && npm run lint` -> passed
  - `cd frontend && npm run typecheck` -> passed
  - `cd frontend && npm run build` -> passed
- The React frontend is merged and is now the default shipped frontend surface.
- Inspect deep links and review-driven "Jump to Source" navigation are route-based and renderable through the existing inspect screen.
- Temporary review notes, executor task dumps, and stale readiness checklists belong under `docs/archive/`, not in the active docs surface.

## Active Backlog

### Pending Work

#### Persistence and Runtime Expansion

- [x] Persist chapter-packet, sequence, and storyboard cards through lineage-aware registration.
  - Completed: `ChapterPacketService.register_packet_as_lineage()`, `SequencePlanService.register_plan_as_lineage()`, `StoryboardCardService.register_card_as_lineage()` now tested with 12 integration tests in `tests/test_lineage_aware_artifacts.py`. Bugfixes: added missing `StoryArtifactLifecycleState` import to `storyboard_cards.py`, moved `get_packet` call inside try block in `chapter_packets.py`.
- [x] Expand manuscript-aid integration tests.
  - Completed: 15 integration tests in `tests/test_manuscript_aid_integration.py` covering manuscript document CRUD, revision suggestion CRUD, cross-project isolation, and document filtering.
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
- Validation: 802 passed, 9 skipped, typecheck passed, build passed, lint passed, qc.py adverse review passed with 0 findings
- Dead code cleanup reduced exports from 112 to 75 across all service files

## Completed Milestones (Summary)

Full details archived in `docs/archive/TODO_Completed_Milestones_Archive.md`.

### Multi-Chapter Generation Completion (2026-04-26)

- ChapterSummarizerService: LLM-based chapter summarization with error tolerance
- Batch multi-chapter mode: `chapter_ids` list payload triggers sequential drafting in single job
- Prior context propagation: summaries injected into subsequent chapters (capped at 3)
- ManuscriptDocument auto-creation: persisted after each chapter draft
- Test coverage: 907 passed, 9 skipped (+7 tests for summarizer + prompt builder)

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
- 802 tests passing across the full suite. Bugfix: `create_inspect_link` incorrectly normalized `object_kind` to `StoryObjectType`, rejecting free-form strings like "job", "checker", "manuscript". Rewrote `test_review_routing_post.py` with proper `tmp_path` DB isolation.

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

### Testing
- Smoke coverage, persistence coverage, contract coverage, failure-mode coverage
- CI runs full suite on push and pull request
