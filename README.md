# Narrative-Engine

Narrative-Engine is a local-first narrative compilation system for long-form fiction development.

It is designed to help a writer move from premise to structured story assets, draft prose with local models, and review outputs through a deterministic multi-role workflow with durable backend progress tracking.

## Product Intent

Narrative-Engine supports:

- project-name-first story setup
- premise, tone, language, and constraint capture
- story bible and sequence generation
- role-based drafting and review workflows
- critic and checker feedback loops
- exact backend progress and status monitoring for long-running work
- story import from existing completed stories (single-pass and multi-pass for large works)
- guided setup wizard: conversational project creation at `/setup-wizard` — LLM extracts config, foundation, characters, world bible, arcs, sequences, and chapters through natural dialogue
- pattern extraction: extract storytelling DNA (voice, structure, archetypes) from any text to seed new projects
- beat-level planning and storyboard card management
- brain dump with LLM-powered text categorization
- manuscript review and scoring
- story generation orchestration: generate canon-congruent sequels or alternates from existing projects
- canon workshop: annotate source material, create reusable generation profiles, manage mythos/pattern libraries
- manuscript LLM assist: AI-powered line edits, expansions, rewrites, and developmental checks with version conflict protection

## Runtime Requirements

For real writing/generation output, configure a non-stub inference backend (`llama.cpp`, LM Studio, `vLLM`, or a compatible cloud provider).

When inference is set to `stub`, the app remains functional for UI and integration testing, but generated narrative output is placeholder-grade.

## Current Architecture

The current codebase includes:

- a FastAPI backend for projects, jobs, models, role-model checking, auth, backup, and health
- SQLite-backed persistence for operational state, project artifacts, and story development entities
- a React + TypeScript frontend rooted at `frontend/` with application code in `frontend/src/`
- a canonical HTTP surface at `/v1/...` for API routes, with unversioned `/health/*` probes by policy
- accepted-and-polled job and checker APIs backed by a local lease-claim executor
- runtime-backed role-model checker execution with inspectable step and lineage projections
- CORS middleware configured for localhost:5173 and localhost:3000
- middleware layer: API key auth, rate limiting, and path traversal protection
- security/reliability features: circuit breaker, idempotency, config validation, file permission checks, audit logging

## Current Status

Implemented and working now:

- project listing and artifact access
- persisted jobs and checker runs
- append-only event history and first-class attempt tables
- `202 Accepted` job and checker start flows with status polling and idempotent replay or conflict handling
- local lease-claim execution and stale-lease reclaim for accepted jobs and checker runs
- attempt-level executor telemetry for executor name, executor identity, queue delay, finish reasons, and reclaim context
- explicit operator retry flow for failed jobs and checker runs
- live SQLite persistence for step records and artifact lineage in the local executor path
- generalized inference provider configuration with a shared backend contract for `llama.cpp`, LM Studio, `vLLM`, and other OpenAI-compatible servers
- a real `P-100` `architect` execution path that builds an inference request, calls the configured inferencer, and persists canonical markdown output plus artifact lineage
- a real `P-200` `sequencer` execution path that builds an inference request, writes the canonical `sequence` artifact, and persists canonical artifact lineage
- a real `P-300` `drafter` execution path that builds an inference request, writes the canonical `chapter-1` artifact, and persists canonical artifact lineage
- **Multi-chapter book generation**: P-300 accepts `chapter_ids` list in job payload to draft multiple chapters sequentially within a single job. Each chapter gets its own output file (`chapters/{chapter_id}.md`), step record, and auto-created ManuscriptDocument. Prior chapter summaries (LLM-extracted key events, character states, unresolved threads) are injected into subsequent chapters for continuity (capped at last 3 chapters).
- persisted `P-100` runtime step telemetry for backend or model identity, prompt or input or output hashes, finish reason, and inspectable lineage linkage
- structured runtime error mapping for real `P-100` failures, including persisted error category and retryability
- runtime-backed checker execution for `architect`, `sequencer`, `drafter`, and `critic`, with deterministic fallback preserved when runtime is unavailable or intentionally skipped
- persisted checker-step runtime telemetry for inspectable backend identity, hashes, finish reasons, and token usage on runtime-backed checker rows
- public inspect endpoints for persisted step records and artifact lineage on jobs and checker runs
- route-driven inspect deep links that render directly from `/workspace/:projectId/inspect/:jobId`
- "Jump to Source" actions that open a renderable inspect route instead of a dead-end shell view
- routed planning workspace at `/workspace/:projectId/plan` with read-heavy tabs for sequence plans, chapter plans, scene plans, dependencies, and chapter packets
- routed flow stage visibility via `FlowEditor` with full editable-flow mutations (add/rename/disable/archive/delete stages)
- character profile editing through `CharacterBuilder` with create/update workflows; relationship-map graph visualization with full CRUD and inline edge actions
- arc candidate management with create/select/deselect actions, stage map creation with narrative progression chips, and arc comparison graph visualization
- routed write workspace at `/workspace/:projectId/write` with API-backed reads for `ManuscriptDocument`, `DraftArtifact`, and `RevisionSuggestion` records via existing GET routes (`getManuscriptDocuments`, `getDraftArtifacts`, `getRevisionSuggestions`)
- Brain Dump project type with distraction-free canvas, auto-save, and LLM-powered text categorization into structured brainstorm items via configured inference backend
- review-driven findings list with accept/reject/defer/escalate/refine decision recording backed by `POST /review/decisions`
- draft mutation service layer with `createDraftArtifact`, `continueDraft`, `createAlternateVariant`, and `promoteDraftToManuscript` API functions
- story import workflow (`POST /v1/projects/import-story`) that parses existing stories and creates full project structure with foundation, characters, world bible, arcs, planning, and drafts
- beat plan management endpoints for detailed scene-level planning
- storyboard card management with Kanban-style column reindexing
- manuscript review and scoring service
- braindump session management with LLM-powered content organization
- latency telemetry in `/health/metrics` endpoint with average, min, and max latency fields for both jobs and role-model-checker runs (REL-05)
- operation field normalization in audit logging middleware with stable semantic names like `job.create`, `project_artifact.manifest.read`, `story_development.drafting.draft_artifacts.read` (REL-10)
- file permission validation with world-writable directory rejection and directory-safety checks (REL-09)
- story generation orchestration: canon packet builder, project forking, consistency gates, 4-phase executor pipeline (G-200/G-300/G-350/G-400), wizard UI at `/workspace/:projectId/generate`
- canon workshop: field-level annotations (locked/mutable/forbidden), customization profiles, mythos/pattern libraries with materiality process, packet preview before submission
- manuscript LLM assist: selection-aware actions (line edits, expansion, compression, rewrites, continuations, forks), document-wide actions (developmental review, canon checks, voice checks, pacing, theme, continuity repair), version conflict protection with offset-based patching
- guided setup wizard with planning: conversational project creation at `/setup-wizard` generates sequences and chapters alongside config, foundation, characters, world bible, and arcs through natural dialogue
- pattern extraction: generalized extraction of archetypal patterns, narrative structure, voice profile, thematic constraints, and entities from any story text; supports Same World / New Characters / Transposed generation modes
- multi-pass story import: large stories (>30K chars) automatically chunked and analyzed per-chapter with LLM consolidation for characters, world bible, arcs, and planning
- sample stories: 4 curated stories (2 public domain from Project Gutenberg, 2 original) in `docs/sample-stories/` for walkthrough testing and feature demonstration

## Quickstart

### Backend

1. Create or use a local Python 3.12 environment in this folder.
2. Install dependencies with `pip install -e .[dev]`.
3. Start the app with `start_narrative_core.cmd` or `start_narrative_core.ps1`.
4. Open [http://127.0.0.1:8000/role-model-checker-ui](http://127.0.0.1:8000/role-model-checker-ui).
5. Validate the current baseline with `python -m pytest -q -p no:cacheprovider` or run targeted subsets such as `tests/test_story_import_service.py`, `tests/test_story_branching_service.py`, `tests/test_input_validation.py`, `tests/test_authentication.py`, `tests/test_circuit_breaker.py`.

Current verified baseline:

- Parallel cluster: `pytest -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py --ignore=tests/test_smoke.py --ignore=tests/test_local_executor_manuscript_assist.py --ignore=tests/test_story_generation_e2e.py` -> 1471 passed, 7 skipped (~33s)
- Serial tests: `pytest -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records tests/test_smoke.py tests/test_local_executor_manuscript_assist.py tests/test_story_generation_e2e.py tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters` -> 51 passed (~2s)
- Full baseline: ~1522 tests, ~65s total

### Frontend

1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Copy environment: `copy .env.example .env.local` (Windows) or `cp .env.example .env.local` (Unix)
4. Start dev server: `npm run dev`
5. Open [http://localhost:5173](http://localhost:5173)

Current verified frontend baseline:

- `npm run lint`
- `npm run typecheck`
- `npm run build`

See [AGENTS.md](AGENTS.md) for the current active dev guide and doc set.

## Continuous Testing

- GitHub Actions runs the pytest baseline on `push`, `pull_request`, and manual dispatch.
- Matrix:
  - `ubuntu-latest` with Python `3.12`
  - `windows-latest` with Python `3.12`
- Local full-suite verification:
  - `python -m pytest -q -p no:cacheprovider`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run build`

Latest local full-suite verification:

- Parallel cluster: 1471 passed, 7 skipped (~33s)
- Serial tests: 51 passed (~2s)
- `cd frontend && npm run lint` -> passed
- `cd frontend && npm run typecheck` -> passed
- `cd frontend && npm run build` -> passed, 2025 modules
- `cd frontend && npm run test` -> 554 passed (~13s)

**Frontend Quality Gate**: Full score achieved with production-grade improvements to routing/state synchronization, structured error handling, type safety, and ESLint compliance. 2026-04-23 integration audit: removed 37 dead service functions (42% of exports), added Story Import UI. 2026-05-01: added Story Generation wizard. 2026-05-02: added Canon Workshop and Manuscript Assist, all 17/17 feature areas linked. 2026-05-08: added Guided Setup Wizard with LLM-generated story planning (sequences + chapters).

## Core Docs

- [AGENTS.md](AGENTS.md) - development guidelines, API patterns, feature documentation, and merge readiness checks (single source of truth)
- [docs/STRUCTURE.md](docs/STRUCTURE.md) - project structure overview
- [docs/User Guide v1.7.0.md](docs/User%20Guide%20v1.7.0.md) - user-facing guide
- [docs/Narrative Engine User Walkthrough v1.7.0.md](docs/Narrative%20Engine%20User%20Walkthrough%20v1.7.0.md) - complete step-by-step walkthrough of all features (includes Phase 0 sample stories)
- [docs/QUALITY_GUIDELINES.md](docs/QUALITY_GUIDELINES.md) - code review scoring rubrics

## Planning Docs

- [TODO.md](TODO.md) - active backlog and implementation notes
- [docs/story-generation-orchestration-blueprint-2026-05-02.md](docs/story-generation-orchestration-blueprint-2026-05-02.md) - story generation architecture (implemented)

## Archive

Historical documentation (completed task lists, superseded specs, resolved analyses): [docs/archive/](docs/archive/)

- [docs/archive/](docs/archive) - superseded docs, review dumps, and historical task materials
