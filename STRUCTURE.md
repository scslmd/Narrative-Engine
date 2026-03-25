# Repository Structure

This file explains the purpose of the main folders and key files in this repository.

It is a practical orientation guide for contributors, not a full specification. For behavior and product contracts, start with the docs in [`docs/`](docs/).

## Root

- [`README.md`](README.md): high-level product intent, current status, quickstart, and core doc links
- [`TODO.md`](TODO.md): active delivery plan, deterministic backend tasks, and agent queue notes
- [`STRUCTURE.md`](STRUCTURE.md): this file
- [`pyproject.toml`](pyproject.toml): Python package metadata and dependencies
- [`pytest.ini`](pytest.ini): pytest configuration
- [`start_narrative_core.cmd`](start_narrative_core.cmd): Windows command launcher for the app
- [`start_narrative_core.ps1`](start_narrative_core.ps1): PowerShell launcher for the app
- [`.github/`](.github): CI and GitHub automation files
- [`.venv/`](.venv): local virtual environment, not part of the product code
- [`data/`](data): local runtime state, sample/generated artifacts, and SQLite data

## Backend App

The backend code lives under [`app/`](app/). The structure is layered:

- API layer: request and response handling
- Service layer: domain logic and orchestration
- Persistence layer: SQLite and stored-record operations
- Schema layer: typed contracts for requests, responses, and domain records
- Inference layer: provider abstraction for model execution

### App Entry And Configuration

- [`app/main.py`](app/main.py): FastAPI application entrypoint and route registration
- [`app/settings.py`](app/settings.py): environment-driven app settings and path configuration
- [`app/request_identity.py`](app/request_identity.py): request identity helpers for deterministic tracing and API behavior
- [`app/workflow_preferences.py`](app/workflow_preferences.py): workflow-level preference helpers and defaults

### API Layer

- [`app/api/projects.py`](app/api/projects.py): project endpoints and artifact/projection reads
- [`app/api/jobs.py`](app/api/jobs.py): job lifecycle endpoints, status, and retry flows
- [`app/api/models.py`](app/api/models.py): model and provider availability endpoints
- [`app/api/role_model_checker.py`](app/api/role_model_checker.py): checker execution and inspect endpoints
- [`app/api/story_development.py`](app/api/story_development.py): thin story-development routes for decision review, review routing reads, planning reads, drafting reads, and branching reads or mutations

### Service Layer

- [`app/services/projects.py`](app/services/projects.py): project-level read and artifact services
- [`app/services/project_bootstrap.py`](app/services/project_bootstrap.py): project initialization and seed setup
- [`app/services/job_manager.py`](app/services/job_manager.py): accepted-and-polled job orchestration
- [`app/services/local_executor.py`](app/services/local_executor.py): lease-claim execution path for runtime-backed phases
- [`app/services/role_model_checker.py`](app/services/role_model_checker.py): checker behavior and result shaping
- [`app/services/role_model_check_manager.py`](app/services/role_model_check_manager.py): checker-run orchestration and persistence coordination
- [`app/services/model_registry.py`](app/services/model_registry.py): available-model and provider lookup logic
- [`app/services/protocol.py`](app/services/protocol.py): async/protocol service helpers
- [`app/services/runtime_prompts.py`](app/services/runtime_prompts.py): prompt construction for runtime-backed roles/phases
- [`app/services/step_records.py`](app/services/step_records.py): step record and lineage shaping for inspect surfaces
- [`app/services/validation.py`](app/services/validation.py): validation helpers for backend contracts
- [`app/services/editable_flow.py`](app/services/editable_flow.py): story-development editable stage flow operations
- [`app/services/brainstorm.py`](app/services/brainstorm.py): brainstorming service slice and promotion behavior
- [`app/services/foundation.py`](app/services/foundation.py): foundation profile revision/history service and downstream review-cue generation
- [`app/services/story_knowledge.py`](app/services/story_knowledge.py): character, world-bible, arc-selection, and story-decision-aware knowledge services
- [`app/services/planning.py`](app/services/planning.py): canonical planning-object and chapter-packet service layer
- [`app/services/drafting.py`](app/services/drafting.py): draft-artifact, manuscript, continuation, variant, and revision-suggestion service layer
- [`app/services/story_decision_review.py`](app/services/story_decision_review.py): decision-node timeline and parent-path review helpers
- [`app/services/review_routing.py`](app/services/review_routing.py): review finding routing, review-decision recording, and inspect-link service layer
- [`app/services/story_branching.py`](app/services/story_branching.py): story-branch creation, branch comparison, active-branch selection, and merge-decision service layer

### Persistence Layer

- [`app/persistence/sqlite.py`](app/persistence/sqlite.py): SQLite connection helpers, schema bootstrap, and core DB setup
- [`app/persistence/projects.py`](app/persistence/projects.py): project metadata and artifact indexing reads/writes
- [`app/persistence/jobs.py`](app/persistence/jobs.py): job persistence, attempts, events, and retry state
- [`app/persistence/checker_runs.py`](app/persistence/checker_runs.py): checker-run persistence and state transitions
- [`app/persistence/steps.py`](app/persistence/steps.py): step-record and lineage persistence
- [`app/persistence/story_development.py`](app/persistence/story_development.py): story-development repository operations, including editable flow, planning, drafting, review, inspect, and branching persistence

### Schema Layer

- [`app/schemas/base.py`](app/schemas/base.py): shared schema base types
- [`app/schemas/enums.py`](app/schemas/enums.py): canonical enums used across runtime and story-development contracts
- [`app/schemas/projects.py`](app/schemas/projects.py): project API/domain models
- [`app/schemas/jobs.py`](app/schemas/jobs.py): job API/domain models
- [`app/schemas/models.py`](app/schemas/models.py): model registry and provider-facing schemas
- [`app/schemas/manifest.py`](app/schemas/manifest.py): project manifest and artifact-oriented structures
- [`app/schemas/inference.py`](app/schemas/inference.py): inference request/response contracts
- [`app/schemas/inspect.py`](app/schemas/inspect.py): inspect and projection response contracts
- [`app/schemas/role_model_checker.py`](app/schemas/role_model_checker.py): checker-specific request/response models
- [`app/schemas/story_development.py`](app/schemas/story_development.py): canonical story-development objects and typed contracts

### Inference Layer

- [`app/inference/base.py`](app/inference/base.py): provider interface definitions
- [`app/inference/factory.py`](app/inference/factory.py): provider selection and runtime construction
- [`app/inference/openai_compatible.py`](app/inference/openai_compatible.py): OpenAI-compatible inference implementation
- [`app/inference/stub.py`](app/inference/stub.py): stub provider for deterministic tests and fallback paths

## Frontend

The React + Vite frontend lives under [`frontend/src/`](frontend/src/). The vanilla JS prototype in `frontend/` root is legacy and being decommissioned.

**Directory structure (flat, no nested src folders)**:
- [`frontend/src/index.html`](frontend/src/index.html): HTML entry point
- [`frontend/src/main.tsx`](frontend/src/main.tsx): React application entry
- [`frontend/src/App.tsx`](frontend/src/App.tsx): Root component with routing
- [`frontend/src/components/`](frontend/src/components): Reusable UI components (layout, planning, editor, etc.)
- [`frontend/src/views/`](frontend/src/views): Page-level view components
- [`frontend/src/hooks/`](frontend/src/hooks): Custom React hooks for data fetching and business logic
- [`frontend/src/lib/`](frontend/src/lib): API clients, utilities, and configuration (Axios, TanStack Query)
- [`frontend/src/stores/`](frontend/src/stores): Zustand stores for client state management
- [`frontend/src/theme/`](frontend/src/theme): Theme configuration and CSS variables

**Configuration files**:
- `frontend/src/package.json`: Dependencies and scripts
- `frontend/src/vite.config.ts`: Vite bundler with React plugin and API proxy to backend port 8000
- `frontend/src/tsconfig.json`: TypeScript compiler options
- `frontend/src/tailwind.config.js`: Tailwind CSS configuration with stage-based theme colors

**Build commands**:
```bash
cd frontend/src
npm run dev      # Start development server at http://localhost:5173
npm run build    # Production build to dist/
npm run lint     # ESLint check
```

## Tests

The automated tests live under [`tests/`](tests/). They are organized mostly by behavior slice rather than by package mirror.

- [`tests/conftest.py`](tests/conftest.py): shared pytest fixtures and helpers
- Runtime and provider tests:
  - [`tests/test_inference_runtime.py`](tests/test_inference_runtime.py)
  - [`tests/test_inference_backend_failures.py`](tests/test_inference_backend_failures.py)
  - [`tests/test_runtime_error_mapping_failures.py`](tests/test_runtime_error_mapping_failures.py)
- Executor and checker tests:
  - [`tests/test_local_executor_architect_runtime.py`](tests/test_local_executor_architect_runtime.py)
  - [`tests/test_local_executor_sequencer_runtime.py`](tests/test_local_executor_sequencer_runtime.py)
  - [`tests/test_local_executor_drafter_runtime.py`](tests/test_local_executor_drafter_runtime.py)
  - [`tests/test_role_model_checker_runtime.py`](tests/test_role_model_checker_runtime.py)
- Persistence and inspect tests:
  - [`tests/test_persistence.py`](tests/test_persistence.py)
  - [`tests/test_step_record_spec.py`](tests/test_step_record_spec.py)
  - [`tests/test_step_record_persistence.py`](tests/test_step_record_persistence.py)
  - [`tests/test_projection_endpoints.py`](tests/test_projection_endpoints.py)
  - [`tests/test_projection_endpoints_impl.py`](tests/test_projection_endpoints_impl.py)
  - [`tests/test_projection_runtime_failure_modes.py`](tests/test_projection_runtime_failure_modes.py)
  - [`tests/test_attempt_lineage.py`](tests/test_attempt_lineage.py)
- Story-development backend tests:
  - [`tests/test_story_development_schemas.py`](tests/test_story_development_schemas.py)
  - [`tests/test_story_development_persistence.py`](tests/test_story_development_persistence.py)
  - [`tests/test_editable_flow_service.py`](tests/test_editable_flow_service.py)
  - [`tests/test_brainstorm_service.py`](tests/test_brainstorm_service.py)
  - [`tests/test_foundation_service.py`](tests/test_foundation_service.py)
  - [`tests/test_story_knowledge_service.py`](tests/test_story_knowledge_service.py)
  - [`tests/test_planning_service.py`](tests/test_planning_service.py)
  - [`tests/test_drafting_service.py`](tests/test_drafting_service.py)
  - [`tests/test_story_decision_review_service.py`](tests/test_story_decision_review_service.py)
  - [`tests/test_review_routing_service.py`](tests/test_review_routing_service.py)
  - [`tests/test_story_branching_service.py`](tests/test_story_branching_service.py)
  - [`tests/test_story_development_api.py`](tests/test_story_development_api.py)
- Smoke and failure coverage:
  - [`tests/test_smoke.py`](tests/test_smoke.py)
  - [`tests/test_failure_modes.py`](tests/test_failure_modes.py)
- [`tests/fixtures/step_record_contract_v0_1.json`](tests/fixtures/step_record_contract_v0_1.json): locked contract fixture for step-record shape

## Documentation

The specification and planning docs live under [`docs/`](docs/).

- Core navigation:
  - [`docs/Documentation Guide v0.1.md`](docs/Documentation%20Guide%20v0.1.md)
  - [`docs/Project Index v0.1.md`](docs/Project%20Index%20v0.1.md)
- Product and system contracts:
  - [`docs/Narrative SRS v0.3.md`](docs/Narrative%20SRS%20v0.3.md)
  - [`docs/Frontend Design SRS v0.4.md`](docs/Frontend%20Design%20SRS%20v0.4.md)
  - [`docs/Story Development Product Spec v0.1.md`](docs/Story%20Development%20Product%20Spec%20v0.1.md)
  - [`docs/Story Development Canonical Contract v0.1.md`](docs/Story%20Development%20Canonical%20Contract%20v0.1.md)
  - [`docs/Orchestrator Deterministic Task Spec v0.1.md`](docs/Orchestrator%20Deterministic%20Task%20Spec%20v0.1.md)
- Runtime and inspect contracts:
  - [`docs/Async Protocol Blueprint v0.1.md`](docs/Async%20Protocol%20Blueprint%20v0.1.md)
  - [`docs/Inference Runtime Blueprint v0.1.md`](docs/Inference%20Runtime%20Blueprint%20v0.1.md)
  - [`docs/Runtime Error Mapping Blueprint v0.1.md`](docs/Runtime%20Error%20Mapping%20Blueprint%20v0.1.md)
  - [`docs/Runtime Telemetry Contract v0.1.md`](docs/Runtime%20Telemetry%20Contract%20v0.1.md)
  - [`docs/Step Record Blueprint v0.1.md`](docs/Step%20Record%20Blueprint%20v0.1.md)
  - [`docs/Step and Lineage API Projection Blueprint v0.1.md`](docs/Step%20and%20Lineage%20API%20Projection%20Blueprint%20v0.1.md)
  - [`docs/Step and Lineage API Test Matrix v0.1.md`](docs/Step%20and%20Lineage%20API%20Test%20Matrix%20v0.1.md)
  - [`docs/Failure Mode Test Matrix v0.1.md`](docs/Failure%20Mode%20Test%20Matrix%20v0.1.md)
  - [`docs/Validation Notes v0.1.md`](docs/Validation%20Notes%20v0.1.md)
  - [`docs/Story Arc Paradigm Blueprint v0.1.md`](docs/Story%20Arc%20Paradigm%20Blueprint%20v0.1.md)
- Historical material:
  - [`docs/archive/`](docs/archive)

## Data And Runtime State

- [`data/state/`](data/state): SQLite operational database and related runtime state
- [`data/projects/`](data/projects): per-project local data and generated artifacts
- [`data/role_model_checker_runs/`](data/role_model_checker_runs): checker-run output artifacts and local runtime records

These directories are runtime state, not source-controlled feature code.

## Working Notes

- If you are changing product behavior, consult the relevant doc in [`docs/`](docs/) before editing code.
- If you are changing story-development backend behavior, keep [`app/schemas/story_development.py`](app/schemas/story_development.py) and [`app/persistence/story_development.py`](app/persistence/story_development.py) aligned.
- If you are adding a new backend slice, prefer the pattern already used here: schema contract, persistence support, service logic, and focused tests.
