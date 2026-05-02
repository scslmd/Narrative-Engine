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

- [`app/api/projects.py`](app/api/projects.py): project endpoints, artifact/projection reads, story import, pattern extraction
- [`app/api/jobs.py`](app/api/jobs.py): job lifecycle endpoints, status, and retry flows
- [`app/api/models.py`](app/api/models.py): model and provider availability endpoints
- [`app/api/role_model_checker.py`](app/api/role_model_checker.py): checker execution and inspect endpoints
- [`app/api/story_development.py`](app/api/story_development.py): thin story-development routes for decision review, review routing reads, planning reads, drafting reads, and branching reads or mutations
- [`app/api/story_generation.py`](app/api/story_generation.py): canon generation runs, fork preview/project, gate results (8 endpoints under `/v1/story-generation`)
- [`app/api/health.py`](app/api/health.py): liveness, readiness, and metrics endpoints
- [`app/api/auth.py`](app/api/auth.py): API key management endpoints
- [`app/api/backup.py`](app/api/backup.py): database backup and restore endpoints

### Service Layer

- [`app/services/authentication.py`](app/services/authentication.py): API key authentication and key management
- [`app/services/authorization.py`](app/services/authorization.py): permission checking and resource access control
- [`app/services/circuit_breaker.py`](app/services/circuit_breaker.py): circuit breaker pattern for external service calls
- [`app/services/idempotency.py`](app/services/idempotency.py): idempotency key checking and response caching
- [`app/services/backup.py`](app/services/backup.py): operations database backup and restore
- [`app/services/file_permissions.py`](app/services/file_permissions.py): file permission validation and directory safety checks
- [`app/services/config_validator.py`](app/services/config_validator.py): configuration validation and health checks
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
- [`app/services/editable_flow_persistence.py`](app/services/editable_flow_persistence.py): editable flow persistence operations
- [`app/services/brainstorm.py`](app/services/brainstorm.py): brainstorming service slice and promotion behavior
- [`app/services/braindump.py`](app/services/braindump.py): brain-dump session management and LLM-powered text categorization
- [`app/services/foundation.py`](app/services/foundation.py): foundation profile revision/history service and downstream review-cue generation
- [`app/services/story_knowledge.py`](app/services/story_knowledge.py): character, world-bible, arc-selection, and story-decision-aware knowledge services
- [`app/services/planning.py`](app/services/planning.py): canonical planning-object and chapter-packet service layer
- [`app/services/sequence_plans.py`](app/services/sequence_plans.py): sequence plan service and lineage registration
- [`app/services/chapter_packets.py`](app/services/chapter_packets.py): chapter packet service and lineage registration
- [`app/services/storyboard_cards.py`](app/services/storyboard_cards.py): storyboard card management and lineage registration
- [`app/services/drafting.py`](app/services/drafting.py): draft-artifact, manuscript, continuation, variant, and revision-suggestion service layer
- [`app/services/manuscript_review.py`](app/services/manuscript_review.py): manuscript document review and scoring service
- [`app/services/story_decision_review.py`](app/services/story_decision_review.py): decision-node timeline and parent-path review helpers
- [`app/services/review_routing.py`](app/services/review_routing.py): review finding routing, review-decision recording, and inspect-link service layer
- [`app/services/story_branching.py`](app/services/story_branching.py): story-branch creation, branch comparison, active-branch selection, and merge-decision service layer
- [`app/services/story_import.py`](app/services/story_import.py): story import service for parsing and importing existing stories
- [`app/services/chapter_summarizer.py`](app/services/chapter_summarizer.py): LLM-based chapter summarization, extracts PriorChapterSummary from completed chapters
- [`app/services/canon_packet_builder.py`](app/services/canon_packet_builder.py): deterministic canon packet builder with budget-aware truncation for story generation
- [`app/services/story_forking.py`](app/services/story_forking.py): project forking, canon copying with ID remapping, provenance tracking
- [`app/services/story_generation_orchestrator.py`](app/services/story_generation_orchestrator.py): full generation lifecycle orchestration (G-200/G-300/G-350/G-400 job pipeline)
- [`app/services/generation_gates.py`](app/services/generation_gates.py): canon consistency gate checks, repair prompt builder, policy enforcement

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
- [`app/schemas/story_import.py`](app/schemas/story_import.py): story import request/response schemas
- [`app/schemas/story_development.py`](app/schemas/story_development.py): canonical story-development objects and typed contracts

### Inference Layer

- [`app/inference/base.py`](app/inference/base.py): provider interface definitions
- [`app/inference/factory.py`](app/inference/factory.py): provider selection and runtime construction
- [`app/inference/openai_compatible.py`](app/inference/openai_compatible.py): OpenAI-compatible inference implementation
- [`app/inference/stub.py`](app/inference/stub.py): stub provider for deterministic tests and fallback paths

### Middleware

- [`app/middleware/auth.py`](app/middleware/auth.py): API key authentication middleware
- [`app/middleware/rate_limit.py`](app/middleware/rate_limit.py): per-client rate limiting middleware
- [`app/middleware/path_traversal.py`](app/middleware/path_traversal.py): path traversal protection middleware

### Utils

- [`app/settings.py`](app/settings.py): environment-driven app settings and path configuration
- [`app/request_identity.py`](app/request_identity.py): request identity helpers for deterministic tracing
- [`app/workflow_preferences.py`](app/workflow_preferences.py): workflow-level preference helpers
- [`app/database.py`](app/database.py): shared raw SQLite connection utility
- [`app/utils/input_validation.py`](app/utils/input_validation.py): input sanitization and validation helpers
- [`app/utils/constants.py`](app/utils/constants.py): shared constants (MAX_BODY_SIZE, etc.)

## Frontend

The React + Vite frontend is rooted at [`frontend/`](frontend/) and the application source lives under [`frontend/src/`](frontend/src/).

**Directory structure (flat, no nested src folders)**:
- [`frontend/index.html`](frontend/index.html): HTML entry point
- [`frontend/src/main.tsx`](frontend/src/main.tsx): React application entry
- [`frontend/src/App.tsx`](frontend/src/App.tsx): Root component with routing
- [`frontend/src/components/`](frontend/src/components): Reusable UI components (layout, planning, editor, etc.)
- [`frontend/src/views/`](frontend/src/views): Page-level view components
- [`frontend/src/hooks/`](frontend/src/hooks): Custom React hooks for data fetching and business logic
- [`frontend/src/lib/`](frontend/src/lib): API clients, utilities, and configuration (Axios, TanStack Query)
- [`frontend/src/stores/`](frontend/src/stores): Zustand stores for client state management
- [`frontend/src/theme/`](frontend/src/theme): Theme configuration and CSS variables

**Configuration files**:
- `frontend/package.json`: Dependencies and scripts
- `frontend/vite.config.ts`: Vite bundler with React plugin and API proxy to backend port 8000
- `frontend/tsconfig.json`: TypeScript compiler options
- `frontend/tailwind.config.js`: Tailwind CSS configuration with stage-based theme colors

**Build commands**:
```bash
cd frontend
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
  - [`tests/test_local_executor_compiler_runtime.py`](tests/test_local_executor_compiler_runtime.py)
  - [`tests/test_executor_integration.py`](tests/test_executor_integration.py)
  - [`tests/test_executor_e2e_runtime.py`](tests/test_executor_e2e_runtime.py)
  - [`tests/test_role_model_checker_runtime.py`](tests/test_role_model_checker_runtime.py)
  - [`tests/test_orchestration_integration.py`](tests/test_orchestration_integration.py)

- Persistence and inspect tests:
  - [`tests/test_persistence.py`](tests/test_persistence.py)
  - [`tests/test_persistence_runtime_expansion.py`](tests/test_persistence_runtime_expansion.py)
  - [`tests/test_step_record_spec.py`](tests/test_step_record_spec.py)
  - [`tests/test_step_record_persistence.py`](tests/test_step_record_persistence.py)
  - [`tests/test_projection_endpoints.py`](tests/test_projection_endpoints.py)
  - [`tests/test_projection_endpoints_impl.py`](tests/test_projection_endpoints_impl.py)
  - [`tests/test_projection_runtime_failure_modes.py`](tests/test_projection_runtime_failure_modes.py)
  - [`tests/test_attempt_lineage.py`](tests/test_attempt_lineage.py)
  - [`tests/test_attempt_persistence.py`](tests/test_attempt_persistence.py)
  - [`tests/test_attempt_history_endpoints.py`](tests/test_attempt_history_endpoints.py)
  - [`tests/test_lineage_artifact_reads.py`](tests/test_lineage_artifact_reads.py)
  - [`tests/test_story_bible_lineage.py`](tests/test_story_bible_lineage.py)
  - [`tests/test_lineage_aware_artifacts.py`](tests/test_lineage_aware_artifacts.py)

- Story-development backend tests:
  - [`tests/test_story_development_schemas.py`](tests/test_story_development_schemas.py)
  - [`tests/test_story_development_persistence.py`](tests/test_story_development_persistence.py)
  - [`tests/test_story_development_api.py`](tests/test_story_development_api.py)
  - [`tests/test_story_development_integration_flow.py`](tests/test_story_development_integration_flow.py)
  - [`tests/test_editable_flow_service.py`](tests/test_editable_flow_service.py)
  - [`tests/test_editable_flow_persistence.py`](tests/test_editable_flow_persistence.py)
  - [`tests/test_editable_flow_api.py`](tests/test_editable_flow_api.py)
  - [`tests/test_brainstorm_service.py`](tests/test_brainstorm_service.py)
  - [`tests/test_braindump_service.py`](tests/test_braindump_service.py)
  - [`tests/test_foundation_service.py`](tests/test_foundation_service.py)
  - [`tests/test_story_knowledge_service.py`](tests/test_story_knowledge_service.py)
  - [`tests/test_planning_service.py`](tests/test_planning_service.py)
  - [`tests/test_drafting_service.py`](tests/test_drafting_service.py)
  - [`tests/test_story_decision_review_service.py`](tests/test_story_decision_review_service.py)
  - [`tests/test_review_routing_service.py`](tests/test_review_routing_service.py)
  - [`tests/test_review_routing_post.py`](tests/test_review_routing_post.py)
  - [`tests/test_story_branching_service.py`](tests/test_story_branching_service.py)
  - [`tests/test_story_branching_lifecycle_integration.py`](tests/test_story_branching_lifecycle_integration.py)
  - [`tests/test_storyboard_cards.py`](tests/test_storyboard_cards.py)
  - [`tests/test_story_import_service.py`](tests/test_story_import_service.py)

- Drafting and manuscript tests:
  - [`tests/test_drafter_post_endpoints.py`](tests/test_drafter_post_endpoints.py)
  - [`tests/test_manuscript_aid_integration.py`](tests/test_manuscript_aid_integration.py)
  - [`tests/test_manuscript_aid_endpoints.py`](tests/test_manuscript_aid_endpoints.py)
  - [`tests/test_manuscript_aid_contracts.py`](tests/test_manuscript_aid_contracts.py)
  - [`tests/test_manuscript_review_service.py`](tests/test_manuscript_review_service.py)
  - [`tests/test_manuscript_review_api.py`](tests/test_manuscript_review_api.py)
  - [`tests/test_manuscript_update_api.py`](tests/test_manuscript_update_api.py)

- Security and reliability tests:
  - [`tests/test_input_validation.py`](tests/test_input_validation.py)
  - [`tests/test_authentication.py`](tests/test_authentication.py)
  - [`tests/test_auth_middleware.py`](tests/test_auth_middleware.py)
  - [`tests/test_authorization.py`](tests/test_authorization.py)
  - [`tests/test_circuit_breaker.py`](tests/test_circuit_breaker.py)
  - [`tests/test_idempotency.py`](tests/test_idempotency.py)
  - [`tests/test_backup.py`](tests/test_backup.py)
  - [`tests/test_file_permissions.py`](tests/test_file_permissions.py)
  - [`tests/test_config_validator.py`](tests/test_config_validator.py)
  - [`tests/test_rate_limiting.py`](tests/test_rate_limiting.py)
  - [`tests/test_path_traversal.py`](tests/test_path_traversal.py)
  - [`tests/test_request_size_limits.py`](tests/test_request_size_limits.py)
  - [`tests/test_audit_logging.py`](tests/test_audit_logging.py)
  - [`tests/test_thread_safety.py`](tests/test_thread_safety.py)
  - [`tests/test_exception_hierarchy.py`](tests/test_exception_hierarchy.py)
  - [`tests/test_job_payload_validation.py`](tests/test_job_payload_validation.py)

- Deferred mutations and integration:
  - [`tests/test_deferred_mutations.py`](tests/test_deferred_mutations.py)

- Health and quality:
  - [`tests/test_smoke.py`](tests/test_smoke.py)
  - [`tests/test_failure_modes.py`](tests/test_failure_modes.py)
  - [`tests/test_health_api.py`](tests/test_health_api.py)
  - [`tests/test_jobs_schemas.py`](tests/test_jobs_schemas.py)
  - [`tests/test_qc.py`](tests/test_qc.py)
  - [`tests/test_quality_check_skill.py`](tests/test_quality_check_skill.py)

- [`tests/fixtures/step_record_contract_v0_1.json`](tests/fixtures/step_record_contract_v0_1.json): locked contract fixture for step-record shape

## Documentation

The specification and planning docs live under [`docs/`](docs/). The single source of truth for development guidelines, API patterns, and feature documentation is [`AGENTS.md`](../AGENTS.md).

- Active reference:
  - [`docs/QUALITY_GUIDELINES.md`](docs/QUALITY_GUIDELINES.md) — code review scoring rubrics
  - [`docs/Orchestrator Deterministic Task Spec v0.1.md`](docs/Orchestrator%20Deterministic%20Task%20Spec%20v0.1.md) — task decomposition process template
  - [`docs/Frontend Workspace Behavior Contract v0.1.md`](docs/Frontend%20Workspace%20Behavior%20Contract%20v0.1.md) — frontend routing and state rules
- User-facing:
  - [`docs/User Guide v1.3.md`](docs/User%20Guide%20v1.3.md) — end-user onboarding guide
  - [`docs/Narrative Engine User Walkthrough v1.3.md`](docs/Narrative%20Engine%20User%20Walkthrough%20v1.3.md) — interactive walkthrough
- Future blueprints (not yet implemented):
  - [`docs/manuscript-editor-llm-assist-blueprint-2026-05-02.md`](docs/manuscript-editor-llm-assist-blueprint-2026-05-02.md) — LLM-assisted manuscript editing
  - [`docs/frontend-canon-customization-enhancement-blueprint-2026-05-02.md`](docs/frontend-canon-customization-enhancement-blueprint-2026-05-02.md) — canon customization UI enhancements
- Implemented feature blueprints (architecture reference):
  - [`docs/story-generation-orchestration-blueprint-2026-05-02.md`](docs/story-generation-orchestration-blueprint-2026-05-02.md) — canon packets, forking, gates, wizard UI
- Domain knowledge:
  - [`docs/Story Arc Paradigm Blueprint v0.1.md`](docs/Story%20Arc%20Paradigm%20Blueprint%20v0.1.md) — story arc types and classification
- Historical material:
  - [`docs/archive/`](docs/archive) — completed task lists, superseded specs, resolved analyses (30+ files)

## Data And Runtime State

- [`data/state/`](data/state): SQLite operational database and related runtime state
- [`data/projects/`](data/projects): per-project local data and generated artifacts
- [`data/role_model_checker_runs/`](data/role_model_checker_runs): checker-run output artifacts and local runtime records

These directories are runtime state, not source-controlled feature code.

## Working Notes

- If you are changing product behavior, consult the relevant doc in [`docs/`](docs/) before editing code.
- If you are changing story-development backend behavior, keep [`app/schemas/story_development.py`](app/schemas/story_development.py) and [`app/persistence/story_development.py`](app/persistence/story_development.py) aligned.
- If you are adding a new backend slice, prefer the pattern already used here: schema contract, persistence support, service logic, and focused tests.
