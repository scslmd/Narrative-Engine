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
- story import from existing completed stories
- beat-level planning and storyboard card management
- brain dump with LLM-powered text categorization
- manuscript review and scoring

## Current Architecture

The current codebase includes:

- a FastAPI backend for projects, jobs, models, role-model checking, auth, backup, and health
- SQLite-backed persistence for operational state, project artifacts, and story development entities
- a React + TypeScript frontend rooted at `frontend/` with application code in `frontend/src/`
- a mixed HTTP surface: versioned `/v1/...` routes for jobs, models, story-development, and checker flows, plus unversioned routes for projects, auth, backup, and health
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
- story import workflow (`POST /projects/import-story`) that parses existing stories and creates full project structure with foundation, characters, world bible, arcs, planning, and drafts
- beat plan management endpoints for detailed scene-level planning
- storyboard card management with Kanban-style column reindexing
- manuscript review and scoring service
- braindump session management with LLM-powered content organization
- latency telemetry in `/health/metrics` endpoint with average, min, and max latency fields for both jobs and role-model-checker runs (REL-05)
- operation field normalization in audit logging middleware with stable semantic names like `job.create`, `project_artifact.manifest.read`, `story_development.drafting.draft_artifacts.read` (REL-10)
- file permission validation with world-writable directory rejection and directory-safety checks (REL-09)

Still being built:

- richer runtime telemetry and latency diagnostics
- broader production-grade test coverage

## Quickstart

### Backend

1. Create or use a local Python 3.12 environment in this folder.
2. Install dependencies with `pip install -e .[dev]`.
3. Start the app with `start_narrative_core.cmd` or `start_narrative_core.ps1`.
4. Open [http://127.0.0.1:8000/role-model-checker-ui](http://127.0.0.1:8000/role-model-checker-ui).
5. Validate the current baseline with `python -m pytest -q -p no:cacheprovider` or run targeted subsets such as `tests/test_story_import_service.py`, `tests/test_story_branching_service.py`, `tests/test_input_validation.py`, `tests/test_authentication.py`, `tests/test_circuit_breaker.py`.

Current verified baseline:

- `python -m pytest -q -p no:cacheprovider` -> `802 passed, 9 skipped` (0 pre-existing failures)

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

- `python -m pytest -q -p no:cacheprovider` -> `802 passed, 9 skipped` (0 pre-existing failures)
- `cd frontend && npm run lint` -> passed
- `cd frontend && npm run typecheck` -> passed
- `cd frontend && npm run build` -> passed

**Frontend Quality Gate**: Full score achieved with production-grade improvements to routing/state synchronization, structured error handling, type safety, and ESLint compliance. 2026-04-23 integration audit: removed 37 dead service functions (42% of exports), added Story Import UI, verified all 13/13 feature areas linked.

## Core Docs

- [AGENTS.md](AGENTS.md) - development guidelines, API patterns, and merge readiness checks
- [docs/STRUCTURE.md](docs/STRUCTURE.md) - project structure overview
- [docs/BACKEND_API_REFERENCE.md](docs/BACKEND_API_REFERENCE.md) - backend API reference
- [docs/User Guide.md](docs/User%20Guide.md) - user-facing guide
- [docs/Narrative SRS v0.3.md](docs/Narrative%20SRS%20v0.3.md) - product spec
- [docs/Frontend Design SRS v0.5.md](docs/Frontend%20Design%20SRS%20v0.5.md) - frontend design spec
- [docs/Feature Reference.md](docs/Feature%20Reference.md) - feature reference

## Planning Docs

- [TODO.md](TODO.md) - active backlog and implementation notes

## Archive

- [docs/archive/](docs/archive) - superseded docs, review dumps, and historical task materials
