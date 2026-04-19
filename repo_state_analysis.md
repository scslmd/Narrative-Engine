# Narrative Engine - Repository State Analysis

**Generated:** 2026-04-19
**Analyzer:** opencode review agent
**Workspace:** `C:\Users\SLuh\Documents\Dev\Narrative-Engine`

---

## 1. What Is Found

### 1.1 Product Overview

Narrative Engine is a local-first narrative compilation system for long-form fiction development. It helps writers move from premise to structured story assets, draft prose with local models, and review outputs through a deterministic multi-role workflow with durable backend progress tracking.

### 1.2 Architecture

- **Backend:** FastAPI (Python 3.12+), single SQLite database (`operations_db`), in-process worker threads for job execution
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + Zustand + TanStack Query
- **API:** Mixed versioning -- versioned `/v1/` routes for jobs, models, story-development, checker; unversioned routes for projects, auth, backup, health
- **Inference:** Provider-agnostic adapter supporting `llama.cpp`, LM Studio, vLLM, and any OpenAI-compatible server (via `openai_compatible.py`); stub backend for testing

### 1.3 Codebase Structure

```
narrative-engine/
|-- app/                          # FastAPI backend
|   |-- api/                      # 8 router files (jobs, projects, auth, backup, health, models, checker, story_development)
|   |-- persistence/              # 7 repository files (jobs, steps, projects, checker_runs, story_development, sqlite, __init__)
|   |-- schemas/                  # 10 schema files (base, enums, jobs, projects, models, inference, inspect, manifest, role_model_checker, story_development)
|   |-- services/                 # 20+ service files (local_executor, job_manager, authentication, authorization, backup, circuit_breaker, idempotency, story_branching, story_knowledge, planning, drafting, review_routing, editable_flow, foundation, brainstorm, role_model_checker, projects, runtime_prompts, step_records, etc.)
|   |-- middleware/               # Auth, authentication, rate_limit, path_traversal
|   |-- inference/                # base.py, stub.py, openai_compatible.py, factory.py
|   |-- utils/                    # input_validation.py
|   |-- main.py                   # 482-line app factory
|   |-- settings.py               # Settings with env var overrides
|-- frontend/
|   |-- src/
|       |-- components/           # 45+ components across 20 directories (ui, projects, branches, decisions, flow, brainstorm, foundation, characters, bible, checker, review, inspect, drafting, aids, jobs, storyboard, common, skeleton)
|       |-- views/                # 6 route-level components
|       |-- services/             # 16 API service files + 10 mock service files
|       |-- hooks/                # 8 custom hooks
|       |-- stores/               # 7 Zustand stores
|       |-- lib/                  # 11 utility modules (api, projectsApi, jobsApi, queryClient, errorHandling, storage, provenance, download, diff, selection, toast)
|       |-- types/                # 18 type definition files
|-- tests/                        # 56 test files
|-- docs/                         # 22 documentation files
|-- scripts/                      # qc.py quality-check utility
```

### 1.4 Backend - What Is Implemented

#### Job Pipeline (Production-Ready)
- 4-phase pipeline: P-100 (Architect), P-200 (Sequencer), P-300 (Drafter), P-400 (Compiler)
- `202 Accepted` start flow with status polling and idempotent replay
- Local lease-claim execution with stale-lease reclaim
- Attempt-level executor telemetry (name, identity, queue delay, finish reasons, reclaim context)
- Operator retry flow for failed jobs
- SQLite-backed persistence for step records and artifact lineage
- Structured runtime error mapping (timeout, HTTP status, invalid JSON -> error categories)

#### Story Development Domain (Production-Ready)
- **Branching:** StoryBranch, BranchPoint, BranchStateRef, BranchComparisonRecord, BranchMergeDecision -- full CRUD
- **Flow:** Flow stages with add, rename, redefine, reorder, disable, archive semantics
- **Decisions:** StoryDecisionNode with timeline and tree fields, affected-object links
- **Review:** CheckerFinding, ReviewDecision, InspectRunLink -- findings, decisions, inspect links
- **Planning:** BeatPlan, SequencePlan, ChapterPlan, ScenePlan, PlanningDependency, ChapterPacket
- **Drafting:** DraftArtifact, ManuscriptDocument, RevisionSuggestion (separate generated vs authored state)
- **Brainstorm:** Items, clustering, promotion with keep/discard/park states
- **Foundation:** FoundationProfile, FoundationRevision, downstream review cues
- **Characters:** CharacterProfile, RelationshipEdge
- **World Bible:** WorldBibleEntry with source references and continuity warnings
- **Arcs:** ArcCandidate, ArcComparisonRecord, ArcSelection, ArcStageMap

#### Security Features (All Complete)
- SEC-01: Input validation and sanitization (XSS, SQL injection, path traversal, size/depth limits)
- SEC-02: API key authentication (SHA-256 hashed, SQLite-backed key store)
- SEC-03: Authorization (permission-based, ownership enforcement)
- SEC-04: Path traversal protection middleware
- SEC-05: Rate limiting (10 jobs/min, 5 checker runs/min, 60 status checks/min)
- SEC-02 (Enhanced): Bearer token auth with prefix index for O(1) lookup

#### Reliability Features (All Complete)
- REL-01: Circuit breaker (5 failures, 60s recovery, half-open testing)
- REL-02: Idempotency keys (24h TTL, SHA-256 payload hashing)
- REL-03: Thread safety (Lock-protected LocalExecutor.start())
- REL-04: Backup strategy (WAL checkpoint, timestamped backups, 7-day retention, restore with pre-restore backup)
- REL-05: Telemetry (job success/failure rates, inference latency, `/health/metrics`)
- REL-06: Deep health checks (`/health/ready` with DB, circuit breaker, disk, memory)
- REL-08: Job payload validation per phase (P-100 through P-400)
- REL-09: File permission validation (world-writable rejection, directory-safety checks)
- REL-10: Audit logging (timestamp, API key hash, normalized operation, target resource)

#### Inference Layer (Production-Ready)
- Abstract `InferenceBackend` interface
- Factory-based provider selection (`llama.cpp`, `lmstudio`, `vllm`, `openai_compatible`, `stub`)
- Structured error mapping: timeout, HTTP errors, invalid JSON -> retryable categories
- Runtime telemetry: provider name, prompt/input/output hashes, token usage, finish reason

### 1.5 Frontend - What Is Implemented

#### Production-Ready Routes (API-backed, no mocks)
- **Projects** (`/`): List, create, detail view
- **Planning** (`/workspace/:projectId/plan`): 11 tabs covering all story-dev features with real API calls
- **Writing** (`/workspace/:projectId/write`): Manuscript documents, draft artifacts, revision suggestions
- **Review** (`/workspace/:projectId/review`): Findings list, inspect run links
- **Inspect** (`/workspace/:projectId/inspect/:jobId`): Step timeline, artifact lineage, attempts data

#### UI Components (45+ across 20 directories)
- Layout: WorkspaceShell, ModeSwitcher, BottomUtilityLayer, notes panel
- Projects: ProjectList, ProjectCreateForm, ProjectDetail
- Branches: BranchList, BranchCard, BranchComparison, MergeDecisionForm
- Decisions: DecisionTree, DecisionNode, DecisionPath
- Flow: FlowEditor, StageList, StageCard, StageActions
- Brainstorm: BrainstormWorkspace, IdeaCard, IdeaCluster
- Foundation: FoundationEditor, FoundationField, ImpactWarning
- Characters: CharacterBuilder, CharacterProfile
- Bible: WorldBibleWorkspace, BibleEntry, PinnedEntry, BibleRail
- Checker: RoleModelSelector, CheckerForm, CheckerResults, CheckerStatus
- Review: FindingsList, FindingCard, DecisionHistory, DecisionForm
- Inspect: InspectMode, InspectTabs, StepTimeline, ArtifactLineage, ProvenanceBadge
- Drafting: DraftPromotion, DraftPreview, AidsPanel, DiffViewer, SuggestionHistory
- Jobs: JobLaunchForm, JobMonitor, JobProgress, JobLogsViewer
- Storyboard: Storyboard, SceneCardList

#### State Management
- Server state: TanStack Query (React Query) with retry logic
- Client state: Zustand (7 stores: workspace, job, ui, toast, theme, notes, bible, selection)
- Route state: `useRouteSync` hook -- URL is source of truth
- Local persistence: localStorage for notes, pinned bible entries, theme

### 1.6 Tests

**56 test files** covering:
- Story branching (service, lifecycle, API, persistence)
- Story decision review service
- Story development (API, integration, persistence, schemas)
- Story knowledge service (characters, world bible, arcs)
- Planning service
- Drafting service
- Review routing service
- Brainstorm service
- Foundation service
- Editable flow service
- Job management (persistence, attempt history, attempt lineage, projection endpoints, step records)
- Local executor (architect, sequencer, drafter, compiler runtime)
- Authentication / Authorization / Input validation
- Circuit breaker / Idempotency / Backup
- Health API / Rate limiting / Path traversal
- Runtime/inference failures / Runtime error mapping
- Failure modes / Thread safety / File permissions / Request size limits
- Configuration validation / Exception hierarchy
- Smoke tests / Audit logging
- Role model checker runtime

### 1.7 Documentation

**13 core docs:** Documentation Guide, Project Index, Validation Notes, Quality Guidelines, Backend API Reference, Narrative SRS v0.3, Frontend Design SRS v0.5, Async Protocol Blueprint, Inference Runtime Blueprint, Step Record Blueprint, Step and Lineage API Projection Blueprint, Story Arc Paradigm Blueprint, Failure Mode Test Matrix, Runtime Error Mapping Blueprint, Runtime Telemetry Contract, Step and Lineage API Test Matrix

**6 planning/spec docs:** TODO.md, Frontend API Alignment Issues, Frontend Workspace Behavior Contract, Story Development Canonical Contract, Story Development Product Spec, Orchestrator Deterministic Task Spec

**22 total doc files** including `docs/archive/`

---

## 2. Current State Assessment

### 2.1 Quality Checks

| Check | Status | Details |
|-------|--------|---------|
| `python -m pytest` | **BLOCKED** | Python 3.10 in use; code requires 3.11+ (`datetime.UTC`) |
| `cd frontend && npm run lint` | **PASS** | Clean |
| `cd frontend && npm run typecheck` | **PASS** | Clean |
| `cd frontend && npm run build` | **PASS** | 389KB JS + 30KB CSS (gzipped: ~112KB + 6KB) |

### 2.2 What Is Working Well

1. **Backend is mature and production-ready** -- The story development domain, job pipeline, security features, and reliability features are all implemented with comprehensive test coverage. The codebase is well-structured with clean separation of concerns.

2. **Frontend is mostly complete** -- All routed workspace views (plan, write, review, inspect) are functional with real API integration. The routing architecture is solid, using route params as the source of truth.

3. **Documentation is extensive** -- The project has well-maintained docs covering architecture, contracts, blueprints, SRS, and validation notes. Active docs are kept in sync with the codebase.

4. **Security and reliability foundations are solid** -- Auth, authz, rate limiting, circuit breaker, idempotency, backups, audit logging, health checks -- all present and tested.

5. **Test coverage is comprehensive** -- 56 test files across all major subsystems. The documented baseline was 514 passing tests.

### 2.3 What Is NOT Working / Blockers

1. **CRITICAL: Python version mismatch** -- The system is running Python 3.10, but the codebase uses `datetime.UTC` which is only available in Python 3.11+. This blocks ALL test execution. The project requires Python 3.12+ per `pyproject.toml`.

### 2.4 Remaining Work

#### Release-Blocker Items
- Upgrade Python runtime to 3.11+ (or 3.12+ per project requirement) to unblock tests
- Fix storyboard mock data (`useStoryboard.ts` uses hardcoded mock scenes instead of API calls)
- Clean up dead route links in `SceneCardList.tsx` (navigates to non-existent routes)
- Fix `disableStage()` and `archiveStage()` stubs that throw "not yet implemented" errors

#### Non-Blocking Improvements
- Remove 10 dead mock service files (`services/mocks/`) that are never imported
- Fix dual `JobPhase`/`JobStatus` type definitions (in `types/job.ts` and `lib/jobsApi.ts`)
- Consolidate Vite proxy (`/api`) vs API client base URL (`/v1`) routing
- Extract logic from monolithic `local_executor.py` (~1200 lines) and `PlanningView.tsx` (671 lines)
- Add database migration system (currently only `CREATE TABLE IF NOT EXISTS`)
- Move to production-grade key hashing (bcrypt instead of SHA-256)
- Add WebSocket support for real-time job status updates
- Add Docker configuration

---

## 3. Thoughts on Current State

### 3.1 Strengths

- **Architecture quality:** The separation of API -> Services -> Persistence is clean and consistent. Raw SQL with parameterized queries is a deliberate and well-executed choice for SQLite.
- **Incremental delivery:** The v1.0 scope was carefully cut (read-only planning, flow, arcs, character relationships deferred). This is a mature approach.
- **Documentation discipline:** The canonical contract documents prevent drift between backend, frontend, and product specs. Active docs are updated after implementation changes.
- **Security-by-design:** Authentication, authorization, rate limiting, path traversal protection, and input validation are all implemented from the ground up.
- **Testing culture:** The subagent queue with named agents (Curie, Kepler, Pasteur, etc.) and deterministic task cards shows a disciplined approach to development.
- **Error handling:** Structured runtime error mapping, circuit breakers, idempotency, and backup/restore show operational thinking.

### 3.2 Concerns

- **Python version blocker is concerning:** The codebase clearly targets Python 3.12+ but the local environment has 3.10. This suggests either the environment wasn't set up properly or the environment was upgraded without updating the codebase. Either way, it's a critical blocker.
- **Dead code accumulation:** The 10 mock service files and the unused `VITE_USE_MOCKS` env var are dead code that survived through the merge process. The comprehensive review process should have caught this.
- **Monolithic components:** `local_executor.py` (1200 lines) and `PlanningView.tsx` (671 lines) are large. While they work, they're difficult to maintain and test in isolation.
- **No database migrations:** The `CREATE TABLE IF NOT EXISTS` pattern works for development but will be fragile in production with schema changes.
- **In-memory rate limiting:** Rate limit state is lost on restart. Fine for single-instance deployments but a limitation.
- **Mixed API versioning:** Having both versioned and unversioned routes creates confusion. The rationale (backward compatibility) is valid but adds maintenance burden.

### 3.3 Production Readiness

The codebase is **functionally close to production-ready** but has several gaps:

1. **Environment:** Needs Python 3.12+ runtime and proper configuration
2. **Deployment:** No Dockerfile, no CI/CD pipeline documentation, no deployment guide
3. **Operations:** No centralized logging framework, no performance monitoring (beyond `/health/metrics`), no database backup scheduling automation
4. **Testing:** All tests are currently blocked by Python version; the 514-pass baseline cannot be verified locally
5. **Security:** SHA-256 for API keys is functional but not production-grade; simple API key gate uses direct comparison (though `hmac.compare_digest` was noted as an improvement)
6. **Frontend dead code:** Mock services and unused env vars should be cleaned up

---

## 4. Remaining Todos

### 4.1 v1.0 Completion (Critical)

| Item | Status | Notes |
|------|--------|-------|
| Python 3.12+ runtime upgrade | **BLOCKED** | `datetime.UTC` import fails on Python 3.10 |
| Fix storyboard mock data | **TODO** | `useStoryboard.ts` uses hardcoded `MOCK_SCENES` |
| Fix dead route links | **TODO** | `SceneCardList.tsx` navigates to non-existent routes |
| Implement flow stage disable/archive | **TODO** | Throws "not yet implemented" errors |
| Remove dead mock services | **TODO** | 10 files in `services/mocks/` never imported |
| Fix type duplication | **TODO** | `JobPhase`/`JobStatus` defined in both `types/job.ts` and `lib/jobsApi.ts` |
| Vite proxy alignment | **TODO** | Proxy maps `/api` but API client uses `/v1` base URL |

### 4.2 Backend Expansion (Planned)

| Item | Priority | Notes |
|------|----------|-------|
| Extend persistence for orchestration attempts | Medium | Richer artifact lineage, projection endpoints |
| Persist chapter-packet, sequence, story-bible artifacts | Medium | Beyond flat file assumptions |
| Scene/chapter storyboard card persistence | Low | Until frontend-backed planning state becomes canonical |
| Manuscript-aid request contracts | Low | Backend surface not yet defined |
| Database migration system | Medium | Currently `CREATE TABLE IF NOT EXISTS` |
| Connection pooling | Low | Only if profiling justifies it |
| Background task queue (Celery/RQ) | Low | For horizontal scaling |

### 4.3 Frontend Polish (Planned)

| Item | Priority | Notes |
|------|----------|-------|
| Frontend error boundary in `main.tsx` | Medium | Already done per `comprehensive_todo.md` |
| Consolidate job status type normalization | Low | `normalizeJobStatus()` maps between incompatible types |
| Clean up unused components | Low | `SequenceViewer.tsx` (not imported), `JobLogsViewer.tsx` at root |

### 4.4 Production Hardening (Planned)

| Item | Priority | Notes |
|------|----------|-------|
| Docker configuration | High | No Dockerfile exists |
| Deployment documentation | High | No deployment guide |
| CI/CD pipeline | High | GitHub Actions exists but only runs specific test subset |
| Centralized logging | Medium | No logging framework beyond audit log |
| Production key hashing | Medium | bcrypt instead of SHA-256 |
| Persistent rate limiting | Low | Redis or similar for multi-instance |
| Performance tests | Low | Optional, outside default merge gate |

---

## 5. What Is Needed to Hit Production Status

### 5.1 Immediate (Must-Have)

1. **Fix Python runtime:** Upgrade to Python 3.12+ or downgrade `datetime.UTC` usage to `datetime.timezone.utc` for backward compatibility
2. **Verify test baseline:** Run `python -m pytest -q -p no:cacheprovider` and confirm 514 passed
3. **Clean up dead code:** Remove `services/mocks/` directory and unused env vars
4. **Fix storyboard hook:** Wire `useStoryboard.ts` to real API or remove the mock data
5. **Fix flow stubs:** Implement or properly disable `disableStage`/`archiveStage`
6. **Add Dockerfile:** Single-file deployment configuration
7. **Write deployment guide:** Document environment setup, configuration, and running in production

### 5.2 Near-Term (Should-Have)

1. **Database migrations:** Add Alembic or similar migration tooling
2. **Production key hashing:** Switch from SHA-256 to bcrypt for API key storage
3. **HMAC for simple API key gate:** Use `hmac.compare_digest` for constant-time comparison
4. **Make CORS origins configurable:** Via `CORS_ORIGINS` env var (already noted in code)
5. **Add backup integrity test:** Verify corrupt backup is rejected before overwrite
6. **Add app-level integration tests:** `build_app()` based tests for jobs, backup, auth-gated routes

### 5.3 Future (Nice-to-Have)

1. **Performance benchmarks:** Optional outside default merge gate
2. **WebSocket real-time updates:** For job status, instead of polling
3. **Horizontal scaling support:** Background task queue, persistent rate limiting
4. **OpenAPI/Swagger customization:** Branded API documentation
5. **Database connection pooling:** If write contention shows up in profiling
6. **Extract `local_executor.py`:** Break into smaller, testable modules
7. **Break up `PlanningView.tsx`:** Extract tab components into separate modules

---

## 6. Summary Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| Backend Implementation | 9/10 | Comprehensive, production-ready with minor technical debt |
| Frontend Implementation | 8/10 | Mostly complete, some dead code and mock stubs remain |
| Test Coverage | 7/10 | 56 files, but currently blocked by Python version |
| Security | 8/10 | Auth, authz, rate limiting all present; bcrypt and HMAC needed |
| Reliability | 9/10 | Circuit breaker, idempotency, backups, health checks all solid |
| Documentation | 9/10 | Extensive, well-maintained, canonical contracts in place |
| Deployment Readiness | 4/10 | No Dockerfile, no deployment guide, no production config examples |
| Code Quality | 7/10 | Clean architecture but large monolithic files and some dead code |

**Overall: 7.5/10** -- The codebase is a mature, well-architected project that is **functionally close to production-ready**. The main blockers are the Python version mismatch (blocking all tests), missing deployment infrastructure, and a small amount of dead code that should be cleaned up. The architectural decisions (raw SQL, route-driven state, canonical contracts) are sound and the security/reliability features are production-grade.

---

*End of analysis.*
