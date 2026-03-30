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

## Current Architecture

The current codebase includes:

- a FastAPI backend for projects, jobs, models, and role-model checking
- SQLite-backed persistence for operational state and project artifact indexing
- a React + TypeScript frontend rooted at `frontend/` with application code in `frontend/src/`
- a mixed HTTP surface: versioned `/v1/...` routes for jobs, models, story-development, and checker flows, plus unversioned routes that still exist for projects, auth, backup, and health
- accepted-and-polled job and checker APIs backed by a local lease-claim executor
- runtime-backed role-model checker execution with inspectable step and lineage projections
- CORS middleware configured for localhost:5173 and localhost:3000

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
- routed flow stage visibility via `FlowEditor` showing current `StoryFlowStage[]` without shipped editable-flow mutations for v1.0
- character profile editing through `CharacterBuilder` with create/update workflows; relationship-map workflows deferred beyond v1.0
- arc support as read-only projections via `getArcCandidates`, `getArcSelections`, and `getArcStageMaps`; interactive arc-decision mutations deferred beyond v1.0
- routed write workspace at `/workspace/:projectId/write` with API-backed reads for `ManuscriptDocument`, `DraftArtifact`, and `RevisionSuggestion` records via existing GET routes (`getManuscriptDocuments`, `getDraftArtifacts`, `getRevisionSuggestions`)
- review-driven aids rail as a surface for viewing revision suggestions without backend-backed accept/reject workflow
- latency telemetry in `/health/metrics` endpoint with average, min, and max latency fields for both jobs and role-model-checker runs (REL-05)
- operation field normalization in audit logging middleware with stable semantic names like `job.create`, `project_artifact.manifest.read`, `story_development.drafting.draft_artifacts.read` (REL-10)

Still being built:

- runtime-backed generation for phases beyond the current `architect`, `sequencer`, and `drafter` slices
- full orchestrator/compiler flow
- runtime-backed job phases beyond `P-100`
- richer runtime telemetry
- broader production-grade tests
- editable-flow stage mutations (add/update/delete) via `FlowEditor`
- relationship-map workflows for character relationships
- interactive arc-decision mutation workflows

## Quickstart

### Backend

1. Create or use a local Python 3.12 environment in this folder.
2. Install dependencies with `pip install -e .[dev]`.
3. Start the app with `start_narrative_core.cmd` or `start_narrative_core.ps1`.
4. Open [http://127.0.0.1:8000/role-model-checker-ui](http://127.0.0.1:8000/role-model-checker-ui).
5. Validate the current baseline with `python -m pytest tests/test_inference_runtime.py tests/test_inference_backend_failures.py tests/test_smoke.py tests/test_local_executor_architect_runtime.py tests/test_local_executor_sequencer_runtime.py tests/test_local_executor_drafter_runtime.py tests/test_persistence.py tests/test_failure_modes.py tests/test_attempt_lineage.py tests/test_projection_endpoints.py tests/test_projection_endpoints_impl.py tests/test_projection_runtime_failure_modes.py tests/test_runtime_error_mapping_failures.py tests/test_role_model_checker_runtime.py tests/test_step_record_spec.py tests/test_step_record_persistence.py -q -p no:cacheprovider`.

Current verified baseline:

- see [docs/Validation Notes v0.1.md](F:/Dev/Narrative-Engine/docs/Validation%20Notes%20v0.1.md) for the latest checked command and scope

### Frontend

1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Copy environment: `cp .env.example .env.local`
4. Start dev server: `npm run dev`
5. Open [http://localhost:5173](http://localhost:5173)

Current verified frontend baseline:

- `npm run lint`
- `npm run typecheck`
- `npm run build`

See [docs/Documentation Guide v0.1.md](docs/Documentation%20Guide%20v0.1.md) for the current active doc set.

## Continuous Testing

- GitHub Actions runs the pytest baseline on `push`, `pull_request`, and manual dispatch.
- Matrix:
  - `ubuntu-latest` with Python `3.12`
  - `windows-latest` with Python `3.12`
- Workflow command:
  - `python -m pytest tests/test_inference_runtime.py tests/test_inference_backend_failures.py tests/test_smoke.py tests/test_local_executor_architect_runtime.py tests/test_local_executor_sequencer_runtime.py tests/test_local_executor_drafter_runtime.py tests/test_persistence.py tests/test_failure_modes.py tests/test_attempt_lineage.py tests/test_projection_endpoints.py tests/test_projection_endpoints_impl.py tests/test_projection_runtime_failure_modes.py tests/test_runtime_error_mapping_failures.py tests/test_role_model_checker_runtime.py tests/test_step_record_spec.py tests/test_step_record_persistence.py -q -p no:cacheprovider`

Latest local full-suite verification (March 29, 2026):

- `python -m pytest -q -p no:cacheprovider` -> `455 passed, 9 skipped`
- `cd frontend && npm run lint` -> passed
- `cd frontend && npm run typecheck` -> passed
- `cd frontend && npm run build` -> passed (390KB JS + 31KB CSS, gzipped: ~112KB + 5KB)

**Frontend Quality Gate**: Full score achieved with production-grade improvements to routing/state synchronization, structured error handling, type safety, and ESLint compliance.

## Core Docs

- [docs/Documentation Guide v0.1.md](docs/Documentation%20Guide%20v0.1.md)
- [docs/Project Index v0.1.md](docs/Project%20Index%20v0.1.md)
- [docs/Validation Notes v0.1.md](docs/Validation%20Notes%20v0.1.md)
- [docs/QUALITY_GUIDELINES.md](docs/QUALITY_GUIDELINES.md)
- [BACKEND_API_REFERENCE.md](BACKEND_API_REFERENCE.md)
- [docs/Narrative SRS v0.3.md](docs/Narrative%20SRS%20v0.3.md)
- [docs/Frontend Design SRS v0.5.md](docs/Frontend%20Design%20SRS%20v0.5.md)
- [docs/Async Protocol Blueprint v0.1.md](docs/Async%20Protocol%20Blueprint%20v0.1.md)
- [docs/Inference Runtime Blueprint v0.1.md](docs/Inference%20Runtime%20Blueprint%20v0.1.md)
- [docs/Step Record Blueprint v0.1.md](docs/Step%20Record%20Blueprint%20v0.1.md)
- [docs/Step and Lineage API Projection Blueprint v0.1.md](docs/Step%20and%20Lineage%20API%20Projection%20Blueprint%20v0.1.md)
- [docs/Story Arc Paradigm Blueprint v0.1.md](docs/Story%20Arc%20Paradigm%20Blueprint%20v0.1.md)
- [docs/Failure Mode Test Matrix v0.1.md](docs/Failure%20Mode%20Test%20Matrix%20v0.1.md)
- [docs/Runtime Error Mapping Blueprint v0.1.md](docs/Runtime%20Error%20Mapping%20Blueprint%20v0.1.md)
- [docs/Runtime Telemetry Contract v0.1.md](docs/Runtime%20Telemetry%20Contract%20v0.1.md)
- [docs/Step and Lineage API Test Matrix v0.1.md](docs/Step%20and%20Lineage%20API%20Test%20Matrix%20v0.1.md)

## Planning Docs

- [TODO.md](TODO.md) - active backlog and implementation notes
- [docs/Frontend API Alignment Issues.md](docs/Frontend%20API%20Alignment%20Issues.md) - detailed frontend/backend alignment analysis
- [docs/archive/](docs/archive) - superseded readiness checklists, review dumps, and temporary task materials
