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
- research management: catalog books, articles, papers, and reference notes with source URLs, genre tags, and citations
- revision workflow: structured revision passes (structural, character, scene, line_edit, copy_edit) with default checklists and status tracking
- polish analysis: document readability scoring (Flesch), passive voice detection, repetitive word analysis, style issue detection, and multi-format export

## Runtime Requirements

For real writing/generation output, configure a non-stub inference backend (`llama.cpp`, LM Studio, `vLLM`, or a compatible cloud provider).

When inference is set to `stub`, the app remains functional for UI and integration testing, but generated narrative output is placeholder-grade.

### Inference Configuration

Configure your inference backend via environment variables (in `.env` at project root):

| Variable | Default | Description |
|----------|---------|-------------|
| `NARRATIVE_INFERENCE_BACKEND` | `llama.cpp` | Backend type: `llama.cpp`, `lmstudio`, `vllm`, `openai_compatible`, or `stub` |
| `NARRATIVE_INFERENCE_BASE_URL` | `http://127.0.0.1:8080` | URL of the inference server |
| `NARRATIVE_INFERENCE_MODEL` | *(none)* | Model name to use |
| `NARRATIVE_INFERENCE_TIMEOUT_SECONDS` | `120` | Request timeout in seconds |

**Token budget (max_tokens):** Each pipeline phase has a default token limit. Override via `.env`:

| Variable | Default | Phase |
|----------|---------|-------|
| `NARRATIVE_MAX_TOKENS_DEFAULT` | `4096` | Fallback for all phases |
| `NARRATIVE_MAX_TOKENS_ARCHITECT` | `4096` | P-100 (architecture) |
| `NARRATIVE_MAX_TOKENS_SEQUENCER` | `4096` | P-200 (sequencing) |
| `NARRATIVE_MAX_TOKENS_DRAFTER` | `8000` | P-300 (drafting) |
| `NARRATIVE_MAX_TOKENS_COMPILER` | `4096` | P-400 (compilation) |
| `NARRATIVE_MAX_TOKENS_PLANNER` | `4096` | G-200 (generation planning) |
| `NARRATIVE_MAX_TOKENS_CHAPTER` | `8000` | G-300 (chapter drafting) |
| `NARRATIVE_MAX_TOKENS_GUIDED_SETUP` | `8192` | Guided setup wizard |

If a job fails with `INFERENCE_TRUNCATED`, increase the relevant `NARRATIVE_MAX_TOKENS_*` value and restart the server. The Job Launch panel shows expandable error details with fix guidance for all inference errors.

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
- research capability: research item CRUD with soft delete, genre tags, citations, and source tracking (`research_items` table)
- revision capability: revision pass lifecycle with default checklists per pass type, status tracking, and 409 conflict on mutation after completion (`revision_passes` table)
- polish capability: document analysis (readability, passive voice, repetitive words, style issues) and async export with status polling (`polish_reports`, `export_statuses` tables)
- studio desk: 19-panel floating workspace with 5-stage rail reorganization (Ideation, Planning, Drafting, Revision, Polish)
- narrative launcher: Windows tray launcher with service management, health monitoring, and system tray icon (NE-01 through NE-06)
- thread-local SQLite connection cache: per-thread per-path connection reuse to reduce connection churn (NE-15)
- backup path traversal protection: backup_id format validation rejecting absolute paths, '..', and path separators (NE-17)
- import prompt user content fencing: <![USER_CONTENT_START]> delimiters around story text to prevent prompt injection (NE-18)
- story forking batch inserts: shared connection with BEGIN IMMEDIATE for batch character/relationship/world entry copies (NE-19)

## Quickstart

### Backend

1. Create or use a local Python 3.12 environment in this folder.
2. Install dependencies with `pip install -e .[dev]`.
3. Start the app with `start_narrative_core.cmd` or `start_narrative_core.ps1`.
4. Open [http://127.0.0.1:8000/role-model-checker-ui](http://127.0.0.1:8000/role-model-checker-ui).
5. Validate the current baseline with `python -m pytest -q -p no:cacheprovider` or run targeted subsets such as `tests/test_story_import_service.py`, `tests/test_story_branching_service.py`, `tests/test_input_validation.py`, `tests/test_authentication.py`, `tests/test_circuit_breaker.py`.

Current verified baseline:

- Parallel cluster: `pytest -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py --ignore=tests/test_smoke.py --ignore=tests/test_local_executor_manuscript_assist.py --ignore=tests/test_story_generation_e2e.py` -> 1637 passed, 6 skipped (~38s)
- Serial tests: `pytest -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records tests/test_smoke.py tests/test_local_executor_manuscript_assist.py tests/test_story_generation_e2e.py tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters tests/test_discovery_api.py::test_patch_returns_updated tests/test_story_bible_lineage.py::TestStoryBibleLineageContentHash::test_story_bible_content_hash_matches_file_content` -> 53 passed (~28s)
- Full baseline: ~1690 tests, ~66s total

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

- Parallel cluster: 1637 passed, 6 skipped (~38s)
- Serial tests: 53 passed (~28s)
- `cd frontend && npm run lint` -> passed (2 pre-existing errors only)
- `cd frontend && npm run typecheck` -> passed
- `cd frontend && npm run build` -> passed, 2049 modules
- `cd frontend && npm run test` -> 787 passed (~14s, 97 test files)

**Frontend Quality Gate**: Full score achieved with production-grade improvements to routing/state synchronization, structured error handling, type safety, and ESLint compliance. 2026-04-23 integration audit: removed 37 dead service functions (42% of exports), added Story Import UI. 2026-05-01: added Story Generation wizard. 2026-05-02: added Canon Workshop and Manuscript Assist, all 17/17 feature areas linked. 2026-05-08: added Guided Setup Wizard with LLM-generated story planning (sequences + chapters). 2026-05-24: added Research, Revision, Polish capabilities (19-panel Studio Desk, 5-stage rail). 2026-05-30: compact rail mode, deterministic entity count badges, typed rail icons, removed dangerouslySetInnerHTML.

## Core Docs

- [AGENTS.md](AGENTS.md) - development guidelines, API patterns, feature documentation, and merge readiness checks (single source of truth)
- [docs/STRUCTURE.md](docs/STRUCTURE.md) - project structure overview
- [docs/User Guide v1.9.0.md](docs/User%20Guide%20v1.9.0.md) - user-facing guide
- [docs/Narrative Engine User Walkthrough v1.9.0.md](docs/Narrative%20Engine%20User%20Walkthrough%20v1.9.0.md) - complete step-by-step walkthrough of all features (includes Phase 0 sample stories)
- [docs/QUALITY_GUIDELINES.md](docs/QUALITY_GUIDELINES.md) - code review scoring rubrics

## Planning Docs

- [TODO.md](TODO.md) - active backlog and implementation notes
- [docs/archive/story-generation-orchestration-blueprint-2026-05-02.md](docs/archive/story-generation-orchestration-blueprint-2026-05-02.md) - story generation architecture (implemented)

## Archive

Historical documentation (completed task lists, superseded specs, resolved analyses): [docs/archive/](docs/archive/)

- [docs/archive/](docs/archive) - superseded docs, review dumps, and historical task materials
