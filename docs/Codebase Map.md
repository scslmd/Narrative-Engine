# Narrative Engine — Codebase Map

> Living document. Last updated: 2026-05-08
> Total codebase: ~78,000 lines (43,555 Python backend + 14,043 TypeScript + 20,272 TSX frontend)

---

## 1. Directory Structure

```
narrative-engine/
├── app/                          # FastAPI backend (~43,555 lines)
│   ├── api/                      # API routers (14 files)
│   │   ├── __init__.py           # Router factory exports
│   │   ├── auth.py               # Authentication endpoints (SEC-02)
│   │   ├── backup.py             # Backup endpoints (REL-04)
│   │   ├── canon_customization.py # Canon annotation/profile endpoints
│   │   ├── health.py             # Health check & metrics (REL-05/06)
│   │   ├── jobs.py               # Job CRUD & lifecycle endpoints
│   │   ├── manuscript_assist.py  # Manuscript assist endpoints
│   │   ├── models.py             # Model catalog endpoints
│   │   ├── mythos_library.py     # Mythos library endpoints
│   │   ├── pattern_library.py    # Pattern library endpoints
│   │   ├── projects.py           # Project CRUD + import endpoints
│   │   ├── role_model_checker.py # Role model checker endpoints
│   │   ├── story_development.py  # Story development endpoints (LARGEST)
│   │   └── story_generation.py   # Story generation orchestrator endpoints
│   ├── inference/                # LLM inference abstraction layer
│   │   ├── base.py               # InferenceBackend ABC + error types
│   │   ├── factory.py            # Backend builder from settings
│   │   ├── openai_compatible.py  # OpenAI-compatible HTTP client
│   │   └── stub.py               # Stub backend for testing
│   ├── middleware/               # ASGI middleware stack
│   │   ├── auth.py               # Legacy AuthMiddleware (unused in production)
│   │   ├── path_traversal.py     # SEC-04: Path traversal protection
│   │   └── rate_limit.py         # SEC-05: Rate limiting
│   ├── persistence/              # Database access layer
│   │   ├── sqlite.py             # Schema definitions + migration (2,582 lines)
│   │   ├── jobs.py               # Job repository (732 lines)
│   │   ├── checker_runs.py       # Checker run repository
│   │   ├── projects.py           # Project artifact repository
│   │   ├── steps.py              # Step record & lineage repository
│   │   └── story_development.py  # Story development repository (6,689 lines)
│   ├── schemas/                  # Pydantic models & dataclasses
│   │   ├── base.py               # StrictModel base class
│   │   ├── enums.py              # JobPhase, JobStatus, etc.
│   │   ├── inference.py          # InferenceRequest/Response
│   │   ├── jobs.py               # Job schemas (292 lines)
│   │   ├── generation.py         # Story generation schemas (293 lines)
│   │   ├── story_development.py  # Story entity schemas (1,280 lines)
│   │   ├── story_import.py       # Import request/response schemas
│   │   └── ... (14 more schema files)
│   ├── services/                 # Business logic (~57 service modules)
│   │   ├── local_executor.py     # Job execution engine (2,486 lines)
│   │   ├── runtime_prompts.py    # LLM prompt builders (1,952 lines)
│   │   ├── story_import.py       # Story import service (1,588 lines)
│   │   ├── multi_pass_import.py  # Multi-pass import for large stories
│   │   └── ... (53 more service files)
│   ├── utils/                    # Shared utilities
│   │   ├── db_inserts.py         # Hash-based ID generation, DB helpers
│   │   ├── input_validation.py   # SEC-01: Input sanitization
│   │   ├── json_extract.py       # JSON extraction from LLM output
│   │   └── manifest.py           # Manifest parsing utilities
│   ├── constants.py              # Shared constants (MAX_BODY_SIZE, UUID_LENGTH)
│   ├── database.py               # Raw DB connection utility
│   ├── main.py                   # App factory + middleware chain (580 lines)
│   ├── request_identity.py       # Request hashing & scoping for idempotency
│   ├── settings.py               # Configuration dataclass (157 lines)
│   └── workflow_preferences.py   # User workflow preference storage
├── frontend/                     # Vite + React + TypeScript (~34,315 lines)
│   ├── src/
│   │   ├── App.tsx               # Root component + router config (63 lines)
│   │   ├── routes.ts             # Route helpers & WorkspaceMode type (21 lines)
│   │   ├── components/           # UI components (~40 subdirectories)
│   │   │   ├── aids/             # Manuscript assist UI components
│   │   │   ├── arcs/             # Arc comparison & stage map components
│   │   │   ├── bible/            # World Bible workspace components
│   │   │   ├── braindump/        # Brain dump session components
│   │   │   ├── brainstorm/       # Brainstorm workspace components
│   │   │   ├── branches/         # Story branching components
│   │   │   ├── canon/            # Canon workshop components
│   │   │   ├── characters/       # Character builder & relationship map
│   │   │   ├── checker/          # Role model checker UI
│   │   │   ├── common/           # Shared layout components
│   │   │   ├── drafting/         # Drafting workspace components
│   │   │   ├── flow/             # Flow editor components
│   │   │   ├── foundation/       # Foundation profile editor
│   │   │   ├── generation/       # Story generation wizard (9 files)
│   │   │   ├── inspect/          # Job inspection components
│   │   │   ├── jobs/             # Job management components
│   │   │   ├── layout/           # Layout shell components
│   │   │   ├── mythos/           # Mythos library UI
│   │   │   ├── patterns/         # Pattern library UI
│   │   │   ├── planning/         # Planning workspace tabs
│   │   │   ├── projects/         # Project list & creation forms
│   │   │   ├── review/           # Review workspace components
│   │   │   ├── skeleton/         # Loading skeleton components
│   │   │   ├── ui/               # Base UI primitives (Toast, etc.)
│   │   │   ├── workspace/        # Workspace shell & navigation
│   │   │   └── writing/          # Writing view components
│   │   ├── hooks/                # Custom React hooks (30 files)
│   │   │   ├── useApiMutation.ts # Generic mutation hook with error handling
│   │   │   ├── useApiQuery.ts    # Generic query hook with caching
│   │   │   ├── useRouteSync.ts   # Route-to-store sync (59 lines)
│   │   │   └── ... (26 more hooks)
│   │   ├── lib/                  # Shared utilities (11 files)
│   │   │   ├── api.ts            # Axios client + ApiError class (62 lines)
│   │   │   ├── queryClient.ts    # React Query client config
│   │   │   ├── storage.ts        # LocalStorage wrappers
│   │   │   └── ... (8 more utils)
│   │   ├── services/             # API service layer (29 service + 29 test files)
│   │   │   ├── storyGeneration.ts # Story generation API calls
│   │   │   ├── manuscriptAssist.ts # Manuscript assist API calls
│   │   │   └── ... (27 more service files)
│   │   ├── stores/               # Zustand stores (9 files)
│   │   │   ├── uiStore.ts        # UI mode, projectId, chapterId, jobId
│   │   │   ├── workspaceStore.ts # Workspace notes persistence
│   │   │   └── ... (7 more stores)
│   │   ├── types/                # TypeScript type definitions (34 files)
│   │   │   ├── storyGeneration.ts # Generation types (12 exports)
│   │   │   └── ... (33 more type files)
│   │   └── views/                # Page-level components (12 files)
│   │       ├── Workspace.tsx     # Workspace layout wrapper
│   │       ├── PlanningView.tsx  # Planning workspace (~575 lines)
│   │       ├── WritingView.tsx   # Writing workspace
│   │       └── ... (9 more views)
│   └── ... (config files: vite, tsconfig, tailwind, etc.)
├── tests/                        # Pytest suite (126 test files)
│   ├── conftest.py               # Shared fixtures + API key injection
│   ├── fixtures/                 # Test data fixtures
│   └── test_*.py                 # All test modules
├── scripts/                      # Development & CI scripts
│   ├── qc.py                     # Quality check review tool
│   ├── quality_check_engine.py   # QC engine implementation
│   ├── dispatcher.py             # Task dispatcher
│   └── run_validation.{bat,ps1,py} # Validation script runners
├── docs/                         # Documentation
│   ├── archive/                  # Archived historical docs
│   ├── superpowers/              # AI agent skill documentation
│   └── *.md                      # Active blueprints & guides
├── data/                         # Runtime data (gitignored)
│   ├── projects/                 # Project directories
│   ├── state/                    # Operations database
│   └── role_model_checker_runs/  # Checker run reports
├── AGENTS.md                     # AI agent development guidelines
├── pyproject.toml                # Python project config
├── pytest.ini                    # Pytest configuration
└── README.md                     # Project overview
```

---

## 2. Backend Architecture

### Request Flow

```
HTTP Request
    │
    ▼
PathTraversalMiddleware (SEC-04)     — Blocks .., %2e%2e, %00, backslash
    │
    ▼
CORSMiddleware (REL-06)              — Origin validation, preflight handling
    │
    ▼
RateLimitMiddleware (SEC-05)         — Per-IP rate limits by endpoint type
    │
    ▼
Audit Logging Middleware (REL-10)    — JSONL audit trail for /v1/* routes
    │
    ▼
API Key Gate (conditional)           — X-API-Key header validation
    │
    ▼
FastAPI Router                       — Route matching → endpoint handler
    │
    ▼
Service Layer                        — Business logic, validation, orchestration
    │
    ▼
Persistence Layer                    — Repository pattern → SQLite
    │
    ▼
SQLite Database                      — WAL mode, FK enforcement, 5s busy timeout
```

### App Factory (`app/main.py::build_app()`)

The `build_app()` function is the single entry point for constructing the FastAPI application:

1. **Config validation**: `validate_config_at_startup()` verifies all settings paths
2. **Service instantiation**: Creates all service instances with dependency injection
3. **Executor setup**: `LocalExecutor` with job loop + checker loop daemon threads
4. **Lifespan manager**: Starts/stops executor threads on app startup/shutdown
5. **Router registration**: Includes all API routers with dependency injection
6. **Static file serving**: Mounts frontend dist/ for SPA fallback

### Middleware Chain (execution order, innermost last)

| Order | Middleware | Purpose | Reference |
|-------|-----------|---------|-----------|
| 1 | `PathTraversalMiddleware` | Block path traversal attacks | SEC-04 |
| 2 | `CORSMiddleware` | Cross-origin request handling | REL-06 |
| 3 | `RateLimitMiddleware` | Per-IP rate limiting (3 tiers) | SEC-05 |
| 4 | `audit_logging_middleware` | JSONL audit trail for /v1/* | REL-10 |
| 5 | `versioned_api_key_gate` | API key validation (conditional) | SEC-02 |

### Executor Pattern (`LocalExecutor`)

The executor runs two daemon threads:

**Job Worker Thread** (`_job_loop`):
```
claim_next_pending() → _process_job(job_id)
    ├── P-100: Architect (story foundation)
    ├── P-200: Sequencer (chapter sequencing)
    ├── P-300: Drafter (chapter drafting, supports multi-chapter batch)
    ├── P-400: Compiler (final manuscript)
    ├── G-200: Generation planner (canon-congruent plan)
    ├── G-300: Generation drafter (multi-chapter with gates)
    ├── G-350: Generation gate (consistency checks)
    ├── G-400: Generation compiler (final assembly)
    ├── M-500: Manuscript assist (LLM-powered editing)
    └── M-550: Manuscript repair (gate-failure recovery)
```

**Checker Worker Thread** (`_checker_loop`):
```
claim_next_pending() → _process_checker(run_id)
    └── Multi-role model evaluation pipeline
```

### Inference Abstraction

```python
InferenceBackend (ABC)
    ├── OpenAICompatibleInferenceBackend  — Production: llama.cpp, lmstudio, vllm
    └── StubInferenceBackend              — Testing: deterministic responses
```

Factory: `build_inference_backend(settings)` selects backend from `NARRATIVE_INFERENCE_BACKEND`.

### Database Architecture

**Two SQLite databases:**

| Database | Path | Purpose | Schema Version |
|----------|------|---------|----------------|
| Operations DB | `data/state/narrative_ops.db` | Central registry, jobs, 60+ tables | v22 |
| Project DB | `data/projects/{id}/bible.db` | Project-local metadata | v1 |

**Operations DB tables (60+):**
- Core: `projects`, `project_artifacts`, `jobs`, `job_logs`, `job_attempts`, `job_events`
- Checkers: `checker_runs`, `checker_results`, `checker_run_attempts`, `checker_run_events`
- Inspect: `step_records`, `artifact_lineage`, `runtime_artifact_selections`
- Story Development: `foundation_profiles`, `character_profiles`, `world_bible_entries`, `arc_candidates`, `arc_stage_maps`, `arc_selections`, `story_flow_definitions`, `story_flow_stages`, `brainstorm_items`, `brain_dump_sessions`
- Planning: `sequence_plans`, `chapter_plans`, `scene_plans`, `beat_plans`, `chapter_packets`, `planning_dependencies`, `storyboard_cards`
- Drafting: `draft_artifacts`, `manuscript_documents`, `revision_suggestions`
- Branching: `story_decision_nodes`, `branch_points`, `story_branches`, `branch_state_refs`, `branch_comparisons`, `branch_merge_decisions`
- Review: `checker_findings`, `review_decisions`, `inspect_run_links`
- Generation: `canon_generation_runs`, `canon_generation_packets`, `generation_gate_results`
- Manuscript Assist: `manuscript_assist_runs`, `manuscript_assist_suggestions`, `manuscript_assist_gate_results`
- Canon: `canon_annotations`, `canon_customization_profiles`
- Libraries: `mythos_entries`, `pattern_entries`
- Continuity: `continuity_threads`, `continuity_states`, `continuity_findings`, `draft_briefs`, `drafting_context_packets`

**Connection settings:** WAL mode, FK enforcement, 5000ms busy timeout.

---

## 3. Frontend Architecture

### Routing Structure (React Router v6)

```
/                              → ProjectList (project browser)
/workspace/:projectId          → Workspace (layout shell)
    /plan                      → PlanningView (foundation, characters, arcs, planning)
    /write                     → WritingView (drafting workspace)
    /write/:chapterId          → WritingView (specific chapter)
    /review                    → ReviewView (quality review)
    /inspect                   → InspectView (job inspection)
    /inspect/:jobId            → InspectView (specific job)
    /braindump                 → BrainDumpView (raw idea capture)
    /canon                     → CanonView (mythos, patterns, customization)
    /generate                  → GenerationView (story generation wizard)
```

**Route-driven state**: The URL is the source of truth. `useRouteSync` synchronizes route params with Zustand stores on every navigation. This ensures deep links and browser refreshes work correctly.

### State Management

| Store | Purpose | Persistence |
|-------|---------|-------------|
| `uiStore` | mode, projectId, chapterId, jobId, inspectContext | Route-driven (no persistence) |
| `workspaceStore` | currentProjectId, notes | localStorage (debounced 1s) |
| `settingsStore` | User preferences | localStorage |
| `themeStore` | Dark/light theme | localStorage |
| `toastStore` | Toast notifications | In-memory |
| `selectionStore` | Multi-selection state | In-memory |
| `jobStore` | Job list cache | In-memory |
| `bibleStore` | World Bible entries | In-memory |
| `notesStore` | Workspace notes | localStorage |

**Server state**: React Query (`@tanstack/react-query`) with 5-minute stale time, 1 retry. All API calls go through the shared Axios client in `frontend/src/lib/api.ts`.

### Service Layer Pattern

```typescript
// Pattern: One service file per API domain
import api from '../lib/api';

export async function getBranches(projectId: string): Promise<StoryBranch[]> {
  const response = await api.get('/v1/story-development/branches', {
    params: { project_id: projectId },
  });
  return response.data;
}
```

**Key conventions:**
- Backend field names preserved in snake_case at service/type boundary
- Shared Axios client with `ApiError` interceptor (handles 400/401/403/404/409/5xx)
- One service file per API domain, one type file per domain
- 29 service files, 29 test files, 34 type files
- Frontend service exports are fully wired to hooks/views/components (validated 2026-05-08)

### Frontend Service Data Transformation (`checker.ts`)

The `getModelCatalog()` service function transforms the backend's `/models` response into the frontend's expected shape. The backend returns `discovered_models` as `list[str]` (plain model ID strings like `"Qwen3.6-27B-Q5_K_M-mtp.gguf"`), while the frontend's `ModelCatalog` type expects `Array<{role: string; model_id: string; name: string}>`. The transformation iterates over `workflow_order` roles and expands each discovered model into a per-role entry, deriving a human-readable name from the filename. Already-shaped objects (from tests) pass through unchanged. This transformation was added 2026-05-07 to fix a blank-screen bug in the Planning→Checker tab caused by the original mock-to-real-API switch (commit `a8d3e8f`) where the mock returned properly-shaped objects but the real backend returns strings.

### Component Hierarchy

```
App
├── QueryClientProvider
│   └── ToastProvider
│       └── BrowserRouter
│           ├── Layout (sidebar + header)
│           │   ├── Sidebar (project nav, mode tabs)
│           │   └── Routes
│           │       ├── ProjectList
│           │       └── Workspace
│           │           ├── WorkspaceShell (mode-aware layout)
│           │           ├── PlanningView
│           │           │   ├── FoundationEditor
│           │           │   ├── CharacterBuilder / RelationshipMapGraph
│           │           │   ├── WorldBibleWorkspace
│           │           │   ├── ArcsTab / ArcComparisonGraph / ArcStageMapFlow
│           │           │   ├── StoryboardCardsSection
│           │           │   └── PlanningSections (sequences, chapters, scenes, beats)
│           │           ├── WritingView
│           │           │   ├── ChapterReader
│           │           │   └── DraftingWorkspace
│           │           ├── ReviewView
│           │           ├── InspectView
│           │           ├── BrainDumpView
│           │           ├── CanonView (mythos, patterns, customization profiles)
│           │           └── GenerationView (wizard: mode, destination, scope, policy, submit)
│           └── ToastContainer
```

---

## 4. Data Flow

### Job Lifecycle (P-Phases)

```
POST /v1/jobs/create { phase: "P-100", payload: {...} }
    │
    ▼
JobManager.accept_job() → creates PENDING job in operations DB
    │
    ▼
LocalExecutor._job_loop() claims job via lease-claim
    │
    ▼
Process by phase:
    P-100 (Architect): manifest → story foundation (markdown)
        Output: data/projects/{id}/architect_p100.md
    │
    P-200 (Sequencer): architect + manifest → chapter sequence (JSON)
        Output: data/projects/{id}/sequences.json
        Input: architect_output (resolved from artifact lineage)
    │
    P-300 (Drafter): sequence + architect + scene context → chapter draft (markdown)
        Output: data/projects/{id}/chapters/{chapter_id}.md
        Input: sequence, architect_output
        Side effects: consistency critic check, entity intake, chapter summarization
        Multi-chapter mode: sequential loop with prior context propagation (last 3 summaries)
    │
    P-400 (Compiler): architect + sequence + chapter → story bible (JSON)
        Output: data/projects/{id}/story_bible.json
        Input: architect_output, sequence, chapter_1
    │
    ▼
Job status: PENDING → PROCESSING → COMPLETED | FAILED
```

### Story Generation Pipeline (G-Phases)

```
POST /v1/story-generation/runs { source_project_id, mode, destination, ... }
    │
    ▼
StoryGenerationOrchestrator.create_run()
    ├── Resolve destination (same project or new project)
    ├── CanonPacketBuilder.build_packet() → deterministic canon snapshot
    │   └── Budget-aware truncation (120K cap), scope filtering
    ├── Store packet in canon_generation_packets table
    ├── Queue G-200 job (generation plan)
    │
    ▼
G-200: Generation Planner
    ├── Load canon packet from DB
    ├── LLM generates generation plan with chapter outline
    └── Persist plan as artifact
    │
    ▼
G-300: Generation Drafter (multi-chapter loop)
    ├── For each chapter: draft with canon context + prior summaries
    ├── Consistency critic check per chapter
    ├── Entity intake per chapter
    └── Auto-create ManuscriptDocument per chapter
    │
    ▼
G-350: Generation Gate
    ├── Plan gate: known character obligations check
    ├── Draft gate: forbidden contradiction check
    └── Repair per policy (warn/block/repair_once/repair_twice)
    │
    ▼
G-400: Generation Compiler
    └── Final manuscript assembly from chapter drafts
    │
    ▼
Run status: pending → running → completed | failed
```

### Canon Packet Flow

```
Source Project Canon (characters, world bible, arcs, threads)
    │
    ▼
CanonPacketBuilder.build_packet(source_project_id, scope, policy)
    ├── Snapshot all canon entities
    ├── Apply scope filtering (character_ids, world_bible_refs, arc_ids, thread_ids)
    ├── Budget-aware truncation (120K character cap)
    └── Generate deterministic packet_id via hash_id()
    │
    ▼
CanonGenerationPacket stored in DB (packet_json, source_hashes_json, prompt_budget_json)
    │
    ▼
G-200/G-300 jobs load packet → LLM inference → canon-congruent output
    │
    ▼
GenerationGateService validates output against canon policy
```

### Manuscript Assist Flow (M-Phases)

```
POST /v1/manuscript-assist/runs { project_id, document_id, assist_kind, ... }
    │
    ▼
ManuscriptAssistService.create_run() → M-500 job
    │
    ▼
M-500: Manuscript Assist
    ├── LLM generates suggestions (style, continuity, canon compliance)
    └── Persists suggestions with gate results
    │
    ▼
M-550: Manuscript Repair (if gates fail)
    └── LLM repairs flagged issues
```

---

## 5. Key Files Index (~50 Most Important Files)

| File | Lines | Description |
|------|-------|-------------|
| `app/main.py` | 580 | App factory, middleware chain, router registration, SPA serving |
| `app/settings.py` | 157 | Configuration dataclass with pytest isolation support |
| `app/services/local_executor.py` | 2,486 | Job execution engine: 10 phase handlers, artifact lifecycle |
| `app/services/runtime_prompts.py` | 1,952 | LLM prompt builders for all phases (P-100 through M-550) |
| `app/services/story_import.py` | 1,588 | Story import service: single-pass LLM analysis + persistence |
| `app/services/multi_pass_import.py` | 1,786 | Multi-pass import for stories >30K chars |
| `app/schemas/story_development.py` | 1,280 | Story entity schemas (Foundation, Character, World Bible, Arcs, Planning) |
| `app/services/story_knowledge.py` | 915 | Story knowledge graph service |
| `app/persistence/story_development.py` | 6,689 | Story development repository (CRUD for all story entities) |
| `app/api/story_development.py` | 3,104 | Story development router (LARGEST router) |
| `app/persistence/sqlite.py` | 2,582 | Database schema definitions + migration system (60+ tables) |
| `app/persistence/jobs.py` | 732 | Job repository with idempotency support |
| `app/services/review_routing.py` | 686 | Review routing service for findings and decisions |
| `app/persistence/steps.py` | 670 | Step record and artifact lineage repository |
| `app/services/pattern_extraction.py` | 641 | Pattern extraction from text via LLM |
| `app/api/projects.py` | 475 | Project CRUD + import endpoints |
| `app/services/drafting.py` | 522 | Drafting service (draft artifacts, manuscript documents) |
| `app/persistence/checker_runs.py` | 574 | Checker run repository |
| `app/services/planning.py` | 570 | Planning service (sequences, chapters, scenes, beats) |
| `app/persistence/projects.py` | 435 | Project artifact repository |
| `app/services/mythos_extraction.py` | 433 | Mythos extraction via pattern extraction infrastructure |
| `app/services/authentication.py` | 430 | API key management service (SEC-02) |
| `app/services/foundation.py` | 430 | Foundation profile service |
| `app/services/backup.py` | 402 | Backup service (REL-04) |
| `app/services/canon_packet_builder.py` | 361 | Deterministic canon packet builder with budget truncation |
| `app/services/role_model_checker.py` | 378 | Role model checker service |
| `app/services/editable_flow.py` | 360 | Editable flow stage management |
| `app/utils/db_inserts.py` | 348 | Hash-based ID generation, DB insert helpers |
| `app/services/config_validator.py` | 322 | Startup config validation (REL-07) |
| `app/utils/input_validation.py` | 310 | Input sanitization (SEC-01) |
| `app/services/manuscript_assist.py` | 306 | Manuscript assist orchestration |
| `app/schemas/generation.py` | 293 | Story generation schemas (30 classes/enums) |
| `app/schemas/jobs.py` | 292 | Job schemas (create, status, logs, retry) |
| `app/services/story_branching.py` | 292 | Story branching service |
| `app/api/health.py` | 288 | Health check + latency metrics (REL-05) |
| `app/services/step_records.py` | 272 | Step record service with stable hashing |
| `app/services/circuit_breaker.py` | 267 | Circuit breaker for inference calls (REL-01) |
| `app/services/manuscript_review.py` | 267 | Manuscript review service |
| `app/services/role_model_check_manager.py` | 262 | Role model check manager |
| `app/services/storyboard_cards.py` | 259 | Storyboard card management |
| `app/services/job_manager.py` | 258 | Job manager with idempotency and retry |
| `app/services/story_generation_orchestrator.py` | 254 | Story generation orchestrator |
| `app/inference/openai_compatible.py` | 235 | OpenAI-compatible inference client |
| `app/services/projects.py` | 223 | Project service (CRUD, reconciliation) |
| `app/services/idempotency.py` | 213 | Idempotency key management (REL-02) |
| `app/middleware/rate_limit.py` | 182 | Rate limiting middleware (SEC-05) |
| `app/middleware/path_traversal.py` | 85 | Path traversal protection (SEC-04) |
| `frontend/src/App.tsx` | 63 | Root component with router and provider setup |
| `frontend/src/lib/api.ts` | 62 | Shared Axios client with ApiError interceptor |

---

## 6. Service Registry

### Core Infrastructure

| Service | File | Responsibility |
|---------|------|----------------|
| `JobManager` | `services/job_manager.py` | Job CRUD, idempotency, retry, status transitions |
| `LocalExecutor` | `services/local_executor.py` | Daemon threads for job/checker execution |
| `ProjectService` | `services/projects.py` | Project CRUD, artifact reading, reconciliation |
| `ModelRegistry` | `services/model_registry.py` | Model catalog management |
| `StepRecordService` | `services/step_records.py` | Step records, artifact lineage, runtime selections |
| `SceneContextService` | `services/scene_context.py` | Character anchors + world constraints + prior summaries |
| `ConfigValidator` | `services/config_validator.py` | Startup config validation (REL-07) |

### Security & Reliability

| Service | File | Responsibility |
|---------|------|----------------|
| `AuthenticationService` | `services/authentication.py` | API key CRUD, validation, fingerprinting (SEC-02) |
| `AuthorizationService` | `services/authorization.py` | Permission checks, resource access (SEC-03) |
| `CircuitBreaker` | `services/circuit_breaker.py` | Inference circuit breaker (REL-01) |
| `IdempotencyService` | `services/idempotency.py` | Idempotency key management (REL-02) |
| `BackupService` | `services/backup.py` | Backup creation and restoration (REL-04) |
| `FilePermissionValidator` | `services/file_permissions.py` | Directory permission validation (REL-09) |

### Story Development

| Service | File | Responsibility |
|---------|------|----------------|
| `FoundationService` | `services/foundation.py` | Foundation profile CRUD with revision history |
| `PlanningService` | `services/planning.py` | Sequences, chapters, scenes, beats management |
| `DraftingService` | `services/drafting.py` | Draft artifacts, manuscript documents, revisions |
| `StoryBranchingService` | `services/story_branching.py` | Branch creation, comparison, merge decisions |
| `StoryboardCardService` | `services/storyboard_cards.py` | Kanban-style storyboard card management |
| `BrainstormService` | `services/brainstorm.py` | Brainstorm items, clustering, promotion |
| `BrainDumpService` | `services/braindump.py` | Brain dump sessions with organization |
| `EditableFlowService` | `services/editable_flow.py` | Customizable workflow stage management |
| `StoryDecisionReviewService` | `services/story_decision_review.py` | Decision nodes, findings, review decisions |
| `ReviewRoutingService` | `services/review_routing.py` | Review finding routing and inspection links |

### Story Import & Extraction

| Service | File | Responsibility |
|---------|------|----------------|
| `StoryImportService` | `services/story_import.py` | Single-pass story import with LLM analysis |
| `MultiPassImportService` | `services/multi_pass_import.py` | Multi-pass import for large stories (>30K chars) |
| `PatternExtractionService` | `services/pattern_extraction.py` | Pattern extraction from text via LLM |
| `MythosExtractionService` | `services/mythos_extraction.py` | Mythos extraction (delegates to PatternExtractionService) |
| `ImportJobManager` | `services/import_jobs.py` | Async import job management with TTL |
| `ExtractionJobManager` | `services/extraction_jobs.py` | Async extraction job management |

### Story Generation

| Service | File | Responsibility |
|---------|------|----------------|
| `StoryGenerationOrchestrator` | `services/story_generation_orchestrator.py` | Full generation lifecycle orchestration |
| `CanonPacketBuilder` | `services/canon_packet_builder.py` | Deterministic canon packet with budget truncation |
| `StoryForkingService` | `services/story_forking.py` | Project forking with canon ID remapping |
| `GenerationGateService` | `services/generation_gates.py` | Consistency gates (plan, draft, repair) |
| `ChapterOrchestrator` | `services/chapter_orchestrator.py` | Multi-chapter drafting orchestration |
| `ChapterSummarizerService` | `services/chapter_summarizer.py` | Chapter summarization for prior context |

### Manuscript Assist

| Service | File | Responsibility |
|---------|------|----------------|
| `ManuscriptAssistService` | `services/manuscript_assist.py` | Assist request orchestration |
| `ManuscriptAssistGateService` | `services/manuscript_assist_gates.py` | Assist gate checks |
| `ManuscriptReviewService` | `services/manuscript_review.py` | Manuscript review and suggestions |

### Canon Customization

| Service | File | Responsibility |
|---------|------|----------------|
| `CanonCustomizationService` | `services/canon_customization.py` | Annotations and customization profiles |
| `MythosLibraryService` | `services/mythos_library.py` | Mythos entry management |
| `PatternLibraryService` | `services/pattern_library.py` | Pattern entry management |

### Quality & Analysis

| Service | File | Responsibility |
|---------|------|----------------|
| `ConsistencyCriticService` | `services/consistency_critic.py` | Character consistency checking in drafts |
| `EntityIntakeService` | `services/entity_intake.py` | Auto-detect new entities in drafts |
| `RoleModelCheckerService` | `services/role_model_checker.py` | Multi-role model evaluation |
| `RoleModelCheckManager` | `services/role_model_check_manager.py` | Checker run management |
| `StoryKnowledgeService` | `services/story_knowledge.py` | Story knowledge graph queries |

### Project I/O

| Service | File | Responsibility |
|---------|------|----------------|
| `ProjectExportService` | `services/project_export.py` | Project export packaging |
| `ProjectImportService` | `services/project_import.py` | Project import extraction |
| `ChapterPacketsService` | `services/chapter_packets.py` | Chapter packet assembly |
| `SequencePlansService` | `services/sequence_plans.py` | Sequence plan management |

---

## 7. API Surface

### Route Groups

| Prefix | Router | Purpose | Endpoints |
|--------|--------|---------|-----------|
| `/auth` | `auth.py` | API key management | POST /keys, GET /keys, DELETE /keys/{prefix} |
| `/backup` | `backup.py` | Backup operations | POST /create, POST /restore/{id}, GET /list, GET /latest, DELETE /{id} |
| `/health` | `health.py` | Health & metrics | GET /, GET /ready, GET /metrics |
| `/projects` | `projects.py` | Project CRUD + imports | GET /, POST /create, GET /{id}, DELETE /{id}, POST /import-story, POST /import-patterns, POST /{id}/extract-patterns |
| `/v1/jobs` | `jobs.py` | Job lifecycle | POST /create (202), GET /{id}/status, GET /{id}/logs, GET /{id}/steps, GET /{id}/lineage, GET /{id}/attempts, POST /{id}/retry |
| `/v1/models` | `models.py` | Model catalog | GET / |
| `/v1/story-development` | `story_development.py` | Full story development | branches, flow, decisions, review, planning, drafting, brainstorm, braindump, foundation, characters, world-bible, arcs, storyboard, relationships |
| `/v1/story-generation` | `story_generation.py` | Canon-congruent generation | POST /runs, GET /runs, GET /runs/{id}, POST /runs/{id}/retry, GET /runs/{id}/packet, GET /runs/{id}/gates, POST /fork-preview, POST /fork-project |
| `/v1/manuscript-assist` | `manuscript_assist.py` | Manuscript editing assist | POST /runs, GET /runs, GET /runs/{id}, POST /runs/{id}/retry, GET /runs/{id}/gates, GET /suggestions, POST /suggestions/{id}/apply, POST /suggestions/{id}/reject, POST /suggestions/{id}/archive |
| `/v1/canon` | `canon_customization.py` | Canon customization | annotations (CRUD), profiles (CRUD + packet-preview) |
| `/v1/mythos` | `mythos_library.py` | Mythos library | entries (CRUD), materialize-extraction |
| `/v1/patterns` | `pattern_library.py` | Pattern library | entries (CRUD), materialize-extraction |
| `/v1/role-model-checker` | `role_model_checker.py` | Role model evaluation | POST /run, POST /start, GET /{id}/status, GET /{id}/steps, GET /{id}/lineage, GET /{id}/attempts, POST /{id}/retry |

### Status Code Semantics

| Code | Meaning |
|------|---------|
| 200 | Read, update, selection operations |
| 201 | Resource creation |
| 202 | Async operation accepted (job creation, assist runs) |
| 400 | Validation errors |
| 401 | Missing/invalid API key |
| 404 | Resource not found |
| 409 | Idempotency conflict, retry not allowed |
| 422 | Pydantic validation failure |
| 429 | Rate limit exceeded |

---

## 8. Test Organization

### Structure

```
tests/
├── conftest.py                  # Shared fixtures, API key injection, pytest isolation
├── fixtures/                    # Test data fixtures
└── test_*.py                    # 126 test files, ~1,499 tests total
```

### Execution Strategy

**Clustered Parallel (recommended):**
```bash
# Step 1: Parallel-safe tests (~35s, ~1,438 tests)
pytest -n auto --dist=loadfile --basetemp=.tmp_xdist \
  --ignore=tests/test_audit_logging.py \
  --ignore=tests/test_rate_limiting.py \
  --ignore=tests/test_smoke.py \
  --ignore=tests/test_local_executor_manuscript_assist.py \
  --ignore=tests/test_story_generation_e2e.py

# Step 2: Serial-only tests (~31s, ~51 tests)
pytest -n 0 \
  tests/test_audit_logging.py \
  tests/test_rate_limiting.py \
  tests/test_persistence.py::test_local_executor_persists_pipeline_step_records \
  tests/test_smoke.py \
  tests/test_local_executor_manuscript_assist.py \
  tests/test_story_generation_e2e.py \
  tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters
```

**Total baseline: ~1,499 tests, ~65s**

### Test Categories

| Category | Files | Description |
|----------|-------|-------------|
| **Executor Runtime** | `test_local_executor_*_runtime.py` (6 files) | Phase-specific executor tests with stub inference |
| **Service Unit** | `test_*_service.py`, `test_*_schemas.py` | Service logic and schema validation |
| **API Integration** | `test_*_api.py`, `test_*_endpoints.py` | Full request/response cycle via TestClient |
| **Persistence** | `test_persistence.py`, `test_*_persistence.py` | DB operations, migrations, isolation |
| **Security** | `test_input_validation.py`, `test_authentication.py`, `test_authorization.py`, `test_path_traversal.py`, `test_rate_limiting.py` | Security features |
| **Reliability** | `test_circuit_breaker.py`, `test_idempotency.py`, `test_backup.py`, `test_thread_safety.py` | Reliability features |
| **E2E** | `test_executor_e2e_runtime.py`, `test_story_generation_e2e.py`, `test_*_integration.py` | End-to-end flows |

### Serial-Only Tests (must run with `-n 0`)

| File | Reason |
|------|--------|
| `test_audit_logging.py` | Shares `settings.audit_log_path` log file |
| `test_rate_limiting.py` | Creates checker runs triggering daemon threads |
| `test_persistence.py::test_local_executor_persists_pipeline_step_records` | Starts/stops executor threads |
| `test_smoke.py` | Integration smoke test |
| `test_local_executor_manuscript_assist.py` | Manuscript assist executor thread tests |
| `test_story_generation_e2e.py` | Full generation pipeline e2e |

### Key Test Patterns

- **`tmp_path` fixture**: Overridden in conftest.py to use isolated `.tmp_test_projects/pytest_runtime/{hash}/` directories
- **Stub inference backend**: All tests use `NARRATIVE_INFERENCE_BACKEND=stub` (set in conftest.py)
- **API key injection**: conftest.py auto-injects `X-API-Key` header on all TestClient requests
- **Test naming**: `test_<component>_<action>_<expected_result>`

---

## Quick Reference

### File Sizes (Top 10)

| File | Lines |
|------|-------|
| `app/persistence/story_development.py` | 6,689 |
| `app/api/story_development.py` | 3,104 |
| `app/persistence/sqlite.py` | 2,582 |
| `app/services/local_executor.py` | 2,486 |
| `app/services/runtime_prompts.py` | 1,952 |
| `app/services/multi_pass_import.py` | 1,786 |
| `app/services/story_import.py` | 1,588 |
| `app/schemas/story_development.py` | 1,280 |
| `app/services/story_knowledge.py` | 915 |
| `app/persistence/jobs.py` | 732 |

### Frontend File Sizes (Top 10)

| File | Lines |
|------|-------|
| `hooks/usePlanningTab.ts` | 1,051 |
| `components/projects/StoryImportModal.tsx` | 621 |
| `views/PlanningView.tsx` | 575 |
| `components/characters/CharacterBuilder.tsx` | 537 |
| `components/characters/RelationshipMapGraph.tsx` | 501 |
| `views/ProjectList.tsx` | 466 |
| `components/bible/WorldBibleWorkspace.tsx` | 445 |
| `services/planning.ts` | 439 |
| `components/SettingsPanel.tsx` | 418 |
| `components/brainstorm/BrainstormWorkspace.tsx` | 407 |

### Known Issues

| Issue | Impact | Status |
|-------|--------|--------|
| `Fallback.tsx` renders `null` | ErrorBoundary catches render errors and shows blank area instead of error message. Masks component crashes as invisible regions (e.g., Planning→Checker tab). | Known — affects user-facing error visibility |

### Counts

| Metric | Value |
|--------|-------|
| Backend Python files | ~100 |
| Backend lines of code | ~43,555 |
| Frontend TS/TSX files | ~170 |
| Frontend lines of code | ~34,315 |
| Total lines of code | ~77,870 |
| Test files | 126 |
| Total tests | ~1,499 |
| API route groups | 12 |
| Service modules | 57 |
| Schema files | 21 |
| Zustand stores | 9 |
| React Query hooks | 28 |
| Database tables (operations) | 60+ |
| Database schema version | 22 |

