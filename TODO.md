# TODO

## Security & Reliability (P0 - Immediate)

- [x] SEC-01 Add authentication middleware with API key validation
  **Objective**: Create authentication middleware requiring `X-API-Key` header on all routes except `/health`.
  
  **Required Context**:
  - File path: `app/middleware/auth.py`
  - Environment variable: `API_KEY` (stored in `.env`)
  - Header name: `X-API-Key`
  - Exempt paths: [`/health`]
  - Error response: HTTP 401 with body `{"error": "Unauthorized", "detail": "Invalid or missing API key"}`
  
  **Expected Output**:
  - Files created: `app/middleware/auth.py`, `tests/test_auth_middleware.py` ✓
  - Middleware registered in `app/main.py` ✓
  - `.env.example` updated with `API_KEY` placeholder ✓
  
  **Determinism**:
  - IF `API_KEY` not in environment, THEN raise startup error ✓
  - IF request path starts with `/health`, THEN skip authentication ✓
  - IF `X-API-Key` header missing or doesn't match `API_KEY`, THEN return 401 ✓
  
  **Tests**: All 10 tests passing (2.85s)

- [x] SEC-02 Add CORS middleware restricting origins to localhost
  Configure `CORSMiddleware` with `["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]`, enable credentials.
  Expected: Cross-origin requests from Vite dev server allowed, other origins blocked.
- [x] SEC-03 Add request size limits (10 MB max body, 5 MB payload validation)
  **Objective**: Add FastAPI body size limit and payload validation to prevent DoS attacks.
  
  **Required Context**:
  - File path: `app/main.py`
  - Max body size: `10_485_760` bytes (10 MB)
  - Payload max size: `5_242_880` bytes (5 MB) in `JobCreateRequest`
  - Error response: HTTP 413 with body `{"error": "Payload Too Large", "detail": "Request exceeds maximum allowed size"}`
  
  **Expected Output**:
  - Files modified: `app/main.py`, `app/schemas/jobs.py` ✓
  - Tests created: `tests/test_request_size_limits.py` ✓
  - Max body size configured on FastAPI app ✓
  - Payload validation added to JobCreateRequest ✓
  
  **Determinism**:
  - IF request body > 10 MB, THEN return 413 immediately ✓
  - IF `payload` field in job creation > 5 MB, THEN return 422 with validation error ✓
  
  **Tests**: All 5 tests passing (5.72s)

- [x] SEC-04 Validate file paths against traversal attacks
  **Objective**: Create path validation middleware to prevent directory traversal attacks.
  
  **Required Context**:
  - File path: `app/middleware/path_traversal.py`
  - Patterns blocked: `..`, `%2e%2e`, `%252e`, `%00`, `\` (backslash)
  - Error response: HTTP 400 with body `{"detail": "Invalid path: potential path traversal detected"}`
  
  **Expected Output**:
  - Files created: `app/middleware/path_traversal.py`, `tests/test_path_traversal.py` ✓
  - Middleware registered in `app/main.py` (first middleware) ✓
  - Validation applied to all incoming requests ✓
  
  **Determinism**:
  - IF path or query contains traversal patterns, THEN return 400 immediately ✓
  - ALL requests checked before reaching application logic ✓
  
  **Tests**: All 10 tests passing (2.76s)

- [x] SEC-05 Add rate limiting (10 jobs/min, 5 checker runs/min, 60 status checks/min)
  **Objective**: Implement token bucket rate limiter for job creation, checker runs, and status checks.
  
  **Required Context**:
  - File path: `app/middleware/rate_limit.py`
  - Limits per client IP:
    - Job creation (`/v1/jobs/create`): 10 requests/minute
    - Checker runs (`/v1/role-model-checker/start`): 5 requests/minute
    - Status checks (`*status`, `*logs`): 60 requests/minute
  - Headers added: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
  - Error response: HTTP 429 with body `{"error": "Too Many Requests", "detail": "Rate limit exceeded. Please retry after 60 seconds."}`
  
  **Expected Output**:
  - Files created: `app/middleware/rate_limit.py`, `tests/test_rate_limiting.py` ✓
  - Middleware registered in `app/main.py` (after auth) ✓
  - Rate limits configured per endpoint type ✓
  
  **Determinism**:
  - IF request count exceeds limit within time window, THEN return 429 ✓
  - Rate limit headers included in ALL responses for rate-limited endpoints ✓
  - Time window resets after configured duration (60 seconds) ✓
  
  **Tests**: All 9 tests passing (2.89s)

## Security & Reliability (P1 - Short-Term)

- [x] REL-01 Add circuit breaker for inference backend (5 failures, 60s recovery)
  **Objective**: Create `app/services/circuit_breaker.py` with token bucket pattern to protect against cascading failures.
  
  **Required Context**:
  - File path: `app/services/circuit_breaker.py`
  - Failure threshold: 5 consecutive failures
  - Recovery timeout: 60 seconds
  - Half-open max calls: 3 test requests
  - States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
  
  **Expected Output**:
  - Files created: `app/services/circuit_breaker.py`, `tests/test_circuit_breaker.py` ✓
  - Circuit breaker registry for multiple backends ✓
  - Thread-safe state management with locks ✓
  - Automatic state transitions based on success/failure patterns ✓
  
  **Determinism**:
  - IF failure count >= threshold, THEN transition to OPEN and reject all calls ✓
  - IF recovery timeout elapsed in OPEN state, THEN transition to HALF_OPEN ✓
  - IF test call succeeds in HALF_OPEN, THEN close circuit and reset counters ✓
  - IF test call fails in HALF_OPEN, THEN reopen circuit ✓
  
  **Tests**: All 17 tests passing (thread safety included)

- [x] REL-02 Add idempotency keys to project creation and story-development writes
  **Objective**: Create `app/services/idempotency.py` with SQLite-backed deduplication for retry-safe operations.
  
  **Required Context**:
  - File path: `app/services/idempotency.py`
  - TTL: 24 hours (86400 seconds)
  - Hash algorithm: SHA-256 of payload bytes
  - Header name: `Idempotency-Key`
  
  **Expected Output**:
  - Files created: `app/services/idempotency.py`, `tests/test_idempotency.py` ✓
  - IdempotencyStore with create_record, get_record, update_response methods ✓
  - Payload hashing for duplicate detection ✓
  - Automatic cleanup of expired records ✓
  
  **Determinism**:
  - IF idempotency key not seen, THEN create new record and allow operation ✓
  - IF same key + same payload hash, THEN return cached response ✓
  - IF same key + different payload, THEN raise IdempotencyError ✓
  - Expired records cleaned up on get (lazy cleanup) ✓
  
  **Tests**: All 14 tests passing (thread safety included)

- [x] REL-03 Fix thread safety race condition in `LocalExecutor.start()`
  **Objective**: Add threading.Lock() to prevent duplicate thread creation.
  
  **Required Context**:
  - File path: `app/services/local_executor.py`
  - Lock scope: Check-and-set of running flag + thread creation
  
  **Expected Output**:
  - Files modified: `app/services/local_executor.py`, `tests/test_thread_safety.py` ✓
  - Atomic check-and-start with lock protection ✓
  - No duplicate threads even under concurrent start() calls ✓
  
  **Determinism**:
  - IF already running, THEN return early without creating new thread ✓
  - ALL state checks and modifications protected by same lock ✓
  
  **Tests**: All 2 tests passing (concurrent start simulation)

- [x] REL-04 Add backup strategy for SQLite database (daily, 7-day retention)
  **Objective**: Create `app/services/backup.py` with WAL checkpoint, timestamped backups, and restore capability.
  
  **Required Context**:
  - File path: `app/services/backup.py`, `app/api/backup.py`
  - Retention policy: Keep 7 most recent backups
  - Backup format: SQLite file copy + metadata JSON
  - Pre-restore backup always created
  
  **Expected Output**:
  - Files created: `app/services/backup.py`, `app/api/backup.py`, `tests/test_backup.py` ✓
  - API endpoints: `/v1/backup/create`, `/v1/backup/list`, `/v1/backup/{id}/restore`, `/v1/backup/{id}/delete` ✓
  - WAL checkpoint before backup for consistency ✓
  - Automatic cleanup of old backups (retention policy) ✓
  
  **Determinism**:
  - IF create backup, THEN checkpoint WAL first to ensure consistency ✓
  - IF restore requested, THEN create pre-restore backup automatically ✓
  - AFTER new backup created, THEN delete backups beyond retention limit ✓
  
  **Tests**: All 12 tests passing (full lifecycle coverage)

- [x] REL-05 Add monitoring and telemetry (job success/failure rates, inference latency, `/metrics` endpoint)
  **Objective**: Structured logging with correlation IDs, Prometheus-style metrics export.
  
  **Status**: Deferred to Wave 3 - Core reliability foundation complete first
  
- [x] REL-06 Add deep health checks (`/health/ready` with database, inference, disk, memory checks)
  **Objective**: Return 503 if critical component unhealthy for load balancer readiness.
  
  **Required Context**:
  - File path: `app/api/health.py` (enhanced)
  - Checks: SQLite connectivity, inference backend reachability, disk space (>10% free), memory usage (<90%)
  - Endpoints: `/health` (liveness), `/health/ready` (readiness)
  
  **Expected Output**:
  - Files modified: `app/api/health.py`, `tests/test_health_api.py` ✓
  - Liveness check returns 200 if process alive ✓
  - Readiness check returns 503 if any critical dependency unhealthy ✓
  - Detailed health status JSON with per-component status ✓
  
  **Determinism**:
  - IF database connection fails, THEN ready=false with reason ✓
  - IF disk space < 10%, THEN ready=false with warning ✓
  - IF memory usage > 90%, THEN ready=false with warning ✓
  
  **Tests**: All 8 tests passing (simulated failure modes)

- [x] SEC-01 Add input validation and sanitization middleware
  **Objective**: Create `app/utils/input_validation.py` with comprehensive XSS, SQL injection, path traversal protection.
  
  **Required Context**:
  - File path: `app/utils/input_validation.py`, `tests/test_input_validation.py`
  - Sanitization: HTML escaping, SQL identifier validation, path normalization
  - Limits: Max string length (10MB), max nesting depth (10), max collection size (1000)
  
  **Expected Output**:
  - Files created: `app/utils/input_validation.py`, `tests/test_input_validation.py` ✓
  - Utility functions for strings, filenames, project IDs, SQL identifiers, URLs ✓
  - DoS protection via size/depth limits ✓
  
  **Determinism**:
  - IF HTML tags detected in user input, THEN escape to text entities ✓
  - IF path contains `..` or null bytes, THEN raise ValidationError ✓
  - IF payload > max_size, THEN raise SizeLimitError ✓
  
  **Tests**: All 39 tests passing (comprehensive attack vector coverage)

- [x] SEC-02 Enhance authentication middleware with API key support
  **Objective**: Create `app/services/authentication.py` with SQLite-backed API key store and Bearer token auth.
  
  **Required Context**:
  - File path: `app/services/authentication.py`, `app/middleware/authentication.py`, `app/api/auth.py`
  - Key format: `{prefix}.{secret}` (4-char prefix + URL-safe secret)
  - Hashing: SHA-256 with constant-time comparison
  - Permissions: read, write, admin
  
  **Expected Output**:
  - Files created: `app/services/authentication.py`, `app/middleware/authentication.py`, `app/api/auth.py` ✓
  - API endpoints: `/v1/auth/keys` (create/list/revoke) ✓
  - Prefix index for O(1) key lookup ✓
  - Permission decorators for route protection ✓
  
  **Determinism**:
  - IF key format invalid, THEN raise AuthenticationError immediately ✓
  - IF hashed secret doesn't match, THEN return None (no error) ✓
  - IF key expired or revoked, THEN return None ✓
  - last_used_at updated on every successful validation ✓
  
  **Tests**: All 13 tests passing (key lifecycle and edge cases)

- [x] SEC-03 Add authorization checks for project operations
  **Objective**: Create `app/services/authorization.py` with permission-based access control and ownership enforcement.
  
  **Required Context**:
  - File path: `app/services/authorization.py`, `tests/test_authorization.py`
  - Permission hierarchy: admin > write > read
  - Ownership model: Users can only access resources they own (unless admin)
  
  **Expected Output**:
  - Files created: `app/services/authorization.py`, `tests/test_authorization.py` ✓
  - AuthorizationService for permission checking ✓
  - ResourceAuthorizationService for ownership-based access control ✓
  
  **Determinism**:
  - IF user has admin permission, THEN grant all access ✓
  - IF user owns resource AND has required permission, THEN grant access ✓
  - IF user doesn't own resource AND not admin, THEN deny access ✓
  - Write permission includes read access (hierarchy) ✓
  
  **Tests**: All 13 tests passing (permission hierarchies and ownership scenarios)

## Security & Reliability (P2 - Medium-Term)

- [ ] REL-05 Add monitoring and telemetry (job success/failure rates, inference latency, `/metrics` endpoint)
  Structured logging with correlation IDs, Prometheus export.
  Expected: Visibility into system health, proactive alerting.
- [ ] REL-06 Add deep health checks (`/health/ready` with database, inference, disk, memory checks)
  Return 503 if critical component unhealthy.
  Expected: Accurate health reporting, load balancer readiness.
- [ ] REL-07 Add configuration validation at startup (inference URL reachable, directories writable, API key set)
  Create `app/services/config_validator.py`, fail fast with clear errors.
  Expected: Configuration errors detected at startup.
- [ ] REL-08 Add input validation for job payloads per phase (P-100, P-200, P-300, P-400 schema validation)
  Validate required fields, reject malformed payloads with 400.
  Expected: Executor crashes from bad payloads prevented.
- [ ] REL-09 Add file permission validation (verify ownership, reject world-writable directories)
  Create `app/utils/file_permissions.py`, log permission warnings.
  Expected: Accidental overwrites prevented.
- [ ] REL-10 Add audit logging (timestamp, API key hash, operation, target resource, before/after state)
  Create `audit_log` table, `/audit/query` endpoint, 90-day retention.
  Expected: Complete audit trail, incident investigation capability.

---

## CRITICAL

- [x] Remove reconstruction or recreation framing from the story-development docs package and rewrite it as an aspirational writing-product specification, especially anywhere the docs describe story-development features as "reconstruction" requirements instead of target product contracts.
- [x] Add one canonical docs contract table for story-development objects, with one approved name per object, a short definition, owning layer, and explicit aliases or replacements for terms that should no longer be used across the SRS, product spec, frontend SRS, and orchestrator spec.
- [x] Add one canonical docs contract table for stage states, artifact lifecycle states, suggestion lifecycle states, and execution states, then update all story-development docs to use the same enum names and explain any UI-only display mapping separately.
- [x] Resolve the current docs contradiction about what is already implemented versus still aspirational in the checker and inspect surfaces so agents can tell whether future tasks are extension work or net-new work.
- [x] Define the editable-flow removal contract precisely so "remove", "disable", "archive", "optional", and "delete custom stage" are no longer interchangeable in the docs.
- [x] Split the drafting contract into distinct canonical concepts for generated draft artifacts, user-authored manuscript state, proposed revisions, and promoted canonical outputs so provenance rules stay deterministic.
- [x] Replace broad frontend implementation waves with real deterministic task cards that each have one bounded screen family, one write scope, explicit dependencies, expected outputs, acceptance criteria, and verification.
- [x] Convert abstract feature verbs in the story-development docs into concrete orchestrator-callable operations with defined inputs, outputs, side effects, and done conditions.
- [x] Define the difference between stage type, project stage instance, and stage status so rename, redefine, reorder, and revisit behavior can be persisted without ambiguity.
- [x] Canonicalize planning terminology so the docs explicitly state whether cards are persisted planning objects, UI views over plan objects, or both, and remove conflicting plan versus card naming.
- [x] Implement `app/services/runtime_prompts.py` with a deterministic `architect` prompt builder that uses the accepted job payload plus project manifest context.
- [x] Generalize the inference adapter so `llama.cpp`, LM Studio, `vLLM`, and other OpenAI-compatible backends can be selected without orchestration changes.
- [x] Update `app/services/local_executor.py` so phase `P-100` calls `inferencer.generate_text()` instead of unconditional stub completion.
- [x] Implement the first real `architect` call in `app/services/local_executor.py` for phase `P-100`, using `app/services/runtime_prompts.py`, the generalized inferencer, and persisted step or lineage output.
- [x] Promote the first real `architect` runtime output from candidate lineage to canonical lineage using an explicit artifact registration policy.
- [x] Update `app/services/role_model_checker.py` so runtime-backed checking can be enabled per role while preserving stub fallback.
- [x] Map timeout, HTTP-status, and invalid-JSON failures in `app/inference/openai_compatible.py` to structured runtime error categories.
- [x] Persist runtime telemetry for provider name, provider version when available, prompt hash, input hash, output hash, token usage, and finish reason on runtime-backed steps.
- [x] Make project artifact endpoints for generated runtime outputs lineage-aware so failed `P-200`/`P-300` runs do not return placeholder `sequence` or `chapter-1` files as if they were successful canonical artifacts.
- [x] Ignore bootstrapped empty upstream artifacts in downstream runtime phases so `P-300` does not record empty `sequence` context as a real dependency.
- [x] Add explicit supersession behavior for rerun canonical job artifacts so repeated `P-200`/`P-300` successes do not leave multiple unsuperseded `CANONICAL` lineage rows.
- [x] Rebuild `LocalExecutor` job processing so the current phase set `P-100`, `P-200`, `P-300`, and `P-400` runs through explicit runtime-backed step handlers instead of one-step stub completion.
- [x] Add read-only API endpoints for step records and artifact lineage on both jobs and checker runs.
- [x] Implement `GET /jobs/{job_id}/steps` backed only by persisted step-record rows and the step projection contract.
- [x] Implement `GET /jobs/{job_id}/lineage` backed only by persisted artifact-lineage rows and the lineage projection contract.
- [x] Implement `GET /role-model-checker/{run_id}/steps` backed only by persisted step-record rows and the step projection contract.
- [x] Implement `GET /role-model-checker/{run_id}/lineage` backed only by persisted artifact-lineage rows and the lineage projection contract.
- [x] Update `.github/workflows/tests.yml` so CI runs `tests/test_inference_runtime.py` in addition to the existing pytest baseline.

## Core Runtime

- [x] Add a prompt-builder service that turns project context into provider-ready `architect` requests.
- [x] Execute one real provider-backed `architect` step through the existing job queue and attempt pipeline.
- [x] Execute one real provider-backed `sequencer` step through the existing job queue and attempt pipeline.
- [x] Execute one real provider-backed `drafter` step through the existing job queue and attempt pipeline.
- [x] Register `architect` runtime output through canonical artifact-lineage persistence.
- [x] Register `sequence` runtime output through canonical artifact-lineage persistence.
- [x] Register `chapter_1` runtime output through canonical artifact-lineage persistence.
- [x] Rebuild the current job-phase set on top of explicit runtime-backed step handlers.
- [x] Rebuild the orchestrator/compiler path on top of durable step and artifact state.
   Completed sub-slices:
   - [x] `ORCH-02A` Delay runtime success completion until step persistence, lineage persistence, and project artifact registration succeed.
   - [x] `ORCH-02B` Remove unsupported-phase stub completion so unknown job phases fail deterministically.
   - [x] `ORCH-02C.1` Persist selected upstream artifact snapshots for `P-200`, `P-300`, and `P-400` attempts so downstream runtime steps stop depending only on live project-file reads.
   - [x] `ORCH-02C.2` Add stronger `story_bible` provenance and supersession/regression coverage for repeated `P-400` runs and latest-canonical upstream selection behavior.
   - [x] `ORCH-02D.1` Remove generated runtime artifact files when finalization fails after write but before durable registration completes, with focused compiler and architect regression coverage.
   - [x] `ORCH-02D.2` Mark already-written step records as failed when finalization breaks after initial persistence, with focused compiler and architect regression coverage.
   - [x] `ORCH-02D.3` Compensate project-artifact projection writes when project-db registration fails, with focused compiler regression coverage and lineage rollback.
   - [x] `ORCH-02D.4` Add staged output-write and restoration semantics so failed reruns do not destroy the prior canonical runtime artifact file before finalization completes.
- [x] Expand the role-model checker beyond stub execution with provider-backed per-role evaluation.
- [x] Add a concrete runtime adapter interface that supports multiple providers and a reusable OpenAI-compatible HTTP transport.
- [x] Wire the generalized inferencer into one real provider-backed `architect` execution path.
- [x] Persist runtime telemetry and hashes for each runtime-backed step.
- [x] Replace stub checker role execution with runtime-backed per-role evaluation while preserving current run and attempt semantics.

## Protocol Hardening

- [x] Persist immutable request snapshots and append-only event history for jobs and checker runs.
- [x] Add baseline attempt-lineage fields for jobs and checker runs.
- [x] Define the planning contract for per-step records and artifact lineage before runtime wiring.
- [x] Enforce the current run-state transition rules in services.
- [x] Return `202 Accepted` from job and checker start endpoints with status polling targets.
- [x] Introduce first-class attempt records instead of relying on a single mutable run row plus event stream.
- [x] Add queue idempotency keys and deterministic duplicate-submission handling.
- [x] Add worker claim or lease semantics for accepted jobs and checker runs in the local executor path.
- [x] Make status endpoints pure persisted projections over worker-managed state.
- [x] Add explicit retry metadata and operator retry flow on top of attempt lineage.
- [x] Add stale-lease reclaim semantics and reclaim events.
- [x] Add attempt-level executor telemetry for queue delay, executor identity, and finish reasons.
- [x] Add structured runtime telemetry for backend identity, hashes, token usage, and finish reasons.
- [x] Add `GET /jobs/{job_id}/steps` and `GET /role-model-checker/{run_id}/steps`.
- [x] Add `GET /jobs/{job_id}/lineage` and `GET /role-model-checker/{run_id}/lineage`.
- [ ] Add stable response schemas for attempt history, step history, and lineage history suitable for inspect views.

## Persistence

- [x] Add SQLite-backed operational persistence.
- [x] Harden SQLite with foreign keys, WAL mode, busy timeout, indexes, and schema versioning.
- [x] Move project reconciliation into an explicit sync or repair flow.
- [x] Add step-record and artifact-lineage persistence for the local executor path.
- [ ] Extend persistence to support orchestration attempts, richer artifact lineage, and projection endpoints.
- [x] Add artifact lineage supersession behavior for canonical project artifacts rather than checker-report-only lineage.
- [ ] Persist chapter-packet, sequence, and future story-bible artifacts through lineage-aware registration instead of flat file assumptions.
- [ ] Add persistence helpers for scene or chapter storyboard cards once frontend-backed planning state becomes canonical.

## Backend Engine Completion

- [x] BE-01 Canonical story-development enums and schema models:
  define the canonical backend enums and schema models for story-development state, flow, foundation, character, world bible, arc, planning, drafting, review, and inspect links in `app/schemas/`.
  Expected result: one importable schema contract aligned with `docs/Story Development Canonical Contract v0.1.md`.
  Verification: targeted schema tests cover enum values, object shape validation, and canonical aliases that should not be accepted as primary field names.
- [x] BE-02 Story-development SQLite persistence scaffolding:
  add operational SQLite tables and repository helpers for editable flow, brainstorm items, foundation revisions, character profiles, world bible entries, arc selection, planning objects, manuscript documents, revision suggestions, and review decisions.
  Expected result: durable persistence exists for canonical story-development objects without breaking existing jobs/checker/inspect tables.
  Note: this is the first backend stage for story-development persistence; we will need to return at the required later stages to finish the remaining service-layer build-out and the still-pending object families.
  Verification: targeted persistence tests cover table creation, round-trip CRUD for representative objects, and foreign-key behavior.
- [x] BE-02A Story-development persistence contract alignment:
  align the current persistence scaffold with the canonical schema layer by using canonical enum values, separating custom-stage identity from stage kind, and tightening record shapes around the accepted story-development contract.
  Expected result: persistence is safe for service-layer integration and no longer bakes in conflicting state or stage semantics.
  Verification: focused persistence tests cover canonical enum round-trips, custom-stage deletion eligibility metadata, and schema-aligned record boundaries.
- [x] BE-03 Editable flow service and repository slice:
  implement the first backend service slice for `StoryFlowDefinition`, `StoryFlowStage`, `StoryFlowEdge`, and editable-flow transitions using the canonical disable/archive/delete-custom semantics.
  Expected result: a backend service can create a default flow, add custom stages, rename/redefine stages, reorder stages, disable/archive stages, and reject invalid custom-stage deletion.
  Verification: focused service tests cover add, rename, redefine, reorder, disable, archive, delete-eligible-custom, and blocked deletion cases.
- [x] BE-03A Editable flow integration cleanup:
  rework the current editable-flow prototype to import canonical story-development schemas, prevent stage-id reuse after deletion, and validate dependency references before saving.
  Expected result: the editable-flow service is safe to build on for persistence and API wiring.
  Verification: focused service tests cover non-reused ids, invalid dependency rejection, and shared schema-type usage.
- [x] BE-04 Brainstorm and promotion service slice:
  implement bounded backend operations for `capture_brainstorm_item`, `cluster_brainstorm_items`, and `promote_brainstorm_item`.
  Expected result: brainstorm items can be stored, grouped, and promoted into downstream story-development objects with provenance links.
  Expected endpoints: none in this slice; service-only foundation for later `/story-development/brainstorm/*` routes.
  Verification: service and persistence tests cover keep/discard/park states and promotion recording.
- [x] BE-05 Foundation profile and downstream-impact slice:
  implement `FoundationProfile` and `FoundationRevision` services plus downstream review-cue generation for foundation changes.
  Expected result: foundation updates remain editable after downstream work exists and create explicit review cues instead of silent overwrites.
  Expected endpoints: none in this slice; service-only foundation for later `/story-development/foundation/*` routes.
  Verification: service tests cover revision history, active-profile reads, and downstream impact records.
- [x] BE-06A Story-knowledge persistence completion:
  add canonical persistence tables and repository helpers for `RelationshipEdge`, `ArcCandidate`, `ArcSelection`, and `ArcStageMap`, and confirm `CharacterProfile` and `WorldBibleEntry` persistence remain aligned to the same contract.
  Expected result: all BE-06 canonical objects have durable backend storage and repository operations instead of mixed persistence-plus-service-local state.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/characters/*`, `/story-development/world-bible/*`, and `/story-development/arcs/*` routes.
  Verification: targeted persistence tests cover relationship-edge round trips, active arc selection storage, arc-stage-map persistence, and repository-backed candidate comparison inputs.
- [x] BE-06B Arc comparison persistence and review contract:
  add canonical persistence tables and repository helpers for `ArcComparisonRecord`, and update arc-selection storage so selections can link to the comparison records that informed the decision.
  Expected result: arc comparison history becomes a first-class persisted object the user can review later instead of advisory service-local memory.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/arcs/comparisons/*` and `/story-development/arcs/*` routes.
  Verification: targeted persistence tests cover ranked comparison record round trips, candidate-set storage, selection-to-comparison links, and multi-comparison history retrieval in deterministic order.
- [x] BE-06C Story decision node persistence contract:
  add canonical persistence tables and repository helpers for `StoryDecisionNode` so user-made story-shaping decisions such as arc pivots, flow changes, and future comparable direction changes remain reviewable over time as a typed timeline and tree.
  Expected result: story-shaping user decisions become first-class persisted nodes rather than only implicit changes to current state.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/decisions/*`, `/story-development/arcs/*`, and future flow-history routes.
  Verification: targeted persistence tests cover decision-subject links, decision type storage, prior-state and new-state summaries or refs, rationale or notes storage, actor identity, chronological retrieval, and links to affected canonical objects.
- [x] BE-06D Arc comparison and decision-node schema alignment:
  add canonical schema support for `ArcComparisonRecord`, selection-to-comparison links, and `StoryDecisionNode` enum-driven timeline and tree fields in `app/schemas/story_development.py`.
  Expected result: the schema layer matches the updated docs contract so persistence and services can exchange typed reviewable decision objects without ad hoc dict payloads.
  Expected endpoints: none in this slice; schema-only foundation for later `/story-development/arcs/comparisons/*`, `/story-development/decisions/*`, and related routes.
  Verification: targeted schema tests cover object validation, required timeline fields, selection link fields, and canonical naming.
- [x] BE-06 Character, world bible, and arc-selection slice:
  implement bounded services for `CharacterProfile`, `RelationshipEdge`, `WorldBibleEntry`, `ArcCandidate`, `ArcComparisonRecord`, `ArcSelection`, `ArcStageMap`, and related `StoryDecisionNode` creation for user choices.
  Expected result: canonical story knowledge can be stored and compared independently of manuscript generation.
  Note: accept this slice only after `BE-06A`, `BE-06B`, `BE-06C`, and `BE-06D` land, because the docs require these objects to be canonical persisted records rather than service-local state.
  Verification: persistence and service tests cover source-linked world facts, relationship updates, persisted arc comparison review, advisory arc selection, and reviewable user decision history.
- [x] BE-07A Planning persistence scaffold:
  add canonical persistence tables and repository helpers for `BeatPlan`, `SequencePlan`, `ChapterPlan`, `ScenePlan`, `PlanningDependency`, and `ChapterPacket`.
  Expected result: planning objects exist as durable backend records before the planning service slice is implemented.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/planning/*` routes.
  Verification: targeted persistence tests cover parent-child relationships, ordering fields, dependency rows, and chapter-packet round trips.
- [x] BE-07 Planning objects and chapter-packet slice:
  implement `BeatPlan`, `SequencePlan`, `ChapterPlan`, `ScenePlan`, `PlanningDependency`, and `ChapterPacket` services.
  Expected result: planning objects persist as canonical records and can be rendered later as UI card views without introducing a competing persisted card contract.
  Note: this slice depends on `BE-07A`; do not implement it as an in-memory or service-local workaround.
  Verification: service tests cover parent-child relationships, reorder behavior, and dependency preservation.
- [x] BE-08A Drafting persistence scaffold:
  add canonical persistence tables and repository helpers for `DraftArtifact`, `ManuscriptDocument`, and `RevisionSuggestion` before implementing manuscript-state services.
  Expected result: generated prose, author-owned manuscript state, and non-destructive revision suggestions all have durable backend storage with no service-local placeholders.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/drafting/*`, `/story-development/manuscript/*`, and `/story-development/revisions/*` routes.
  Verification: targeted persistence tests cover draft-artifact round trips, manuscript-document version storage, and revision-suggestion persistence without overwriting source text.
- [x] BE-08 Draft artifact versus manuscript document separation:
  implement the backend state split between generated `DraftArtifact`, author-owned `ManuscriptDocument`, and non-destructive `RevisionSuggestion`, including continuation, constrained rewrite, alternate-variant, and provenance-preserving promotion behavior.
  Expected result: generated prose, editable manuscript state, and proposed revisions remain distinct in persistence and service behavior, and accepted manuscript changes do not erase originating draft artifacts or their lineage.
  Note: this slice depends on `BE-08A`; do not implement it against process-local or browser-local placeholder state.
  Verification: tests cover promotion into manuscript state without erasing source artifacts, continuation and rewrite flows that preserve provenance, alternate-variant storage, and suggestion acceptance via explicit decisions.
- [x] BE-09B Review and inspect persistence scaffold:
  add canonical persistence tables and repository helpers for `CheckerFinding`, `ReviewDecision`, and `InspectRunLink` before implementing review-routing services.
  Expected result: review findings, review decisions, and inspect links become durable backend records tied to source objects and runs.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/review/*` and inspect-linked workflow routes.
  Verification: targeted persistence tests cover finding storage, decision storage, inspect-link round trips, and stable source-object linkage.
- [x] BE-09 Review decisions and inspect links:
  implement `CheckerFinding`, `ReviewDecision`, and `InspectRunLink` support so findings and suggestions can route back into planning, drafting, and inspect surfaces.
  Expected result: review outcomes become first-class backend records tied to source artifacts and runs.
  Note: this slice depends on `BE-09B` and `BE-08`; do not implement it against process-local review state or against placeholder manuscript or suggestion targets.
  Verification: service tests cover accept/reject/defer/escalate/refine decisions, inspect-link creation, and routing findings back into planning or drafting using canonical service boundaries rather than direct state mutation.
- [x] BE-09A Story decision review surface:
  implement bounded backend support so `StoryDecisionNode` objects can be listed and linked from the related story-development objects they affected.
  Expected result: the user can return later and review why a story direction changed without inferring history from current state alone.
  Expected endpoints: none in this slice; backend foundation for later `/story-development/decisions/*` routes and related object detail screens.
  Verification: service tests cover deterministic ordering, affected-object links, retrieval of prior superseded decisions, and timeline-ready output fields for what changed from what to what and why.
- [x] BE-11 Story branching canonical contract and persistence scaffold:
  add canonical backend schemas and persistence support for `StoryBranch`, `BranchPoint`, `BranchStateRef`, `BranchComparisonRecord`, and `BranchMergeDecision`, explicitly modeled as structured application objects rather than Git commits or branches.
  Expected result: storyline forking becomes a first-class backend capability with durable branch identity, branch origin, branch comparisons, and merge decisions.
  Expected endpoints: none in this slice; foundation for later `/story-development/branches/*` and related branching routes.
  Verification: targeted schema and persistence tests cover branch creation metadata, branch-point links, active-branch selection, branch comparison history, and explicit merge-decision storage.
- [x] BE-11A Story branch identity and branch-point persistence:
  add canonical schema and persistence support for `StoryBranch` and `BranchPoint`, including branch origin, branch name, source node, and active or archived branch state.
  Expected result: branch identity and the decision-node fork point become durable backend objects without compare or merge logic yet.
  Expected endpoints: none in this slice; foundation for later `/story-development/branches/*` routes.
  Verification: targeted schema and persistence tests cover branch creation metadata, branch-point links to `StoryDecisionNode`, and deterministic branch listing order.
- [x] BE-11B Branch state reference and active-branch persistence:
  add canonical schema and persistence support for `BranchStateRef` and active-branch selection per project.
  Expected result: the backend can persist which canonical objects and decision-node path a branch points at, and which branch is currently active.
  Expected endpoints: none in this slice; foundation for later `/story-development/branches/*` routes.
  Verification: targeted schema and persistence tests cover active-branch changes, stable state references, and branch-local decision-node lineage lookup.
- [x] BE-11C Branch comparison persistence:
  add canonical schema and persistence support for `BranchComparisonRecord` so two branches can be compared without mutating branch state.
  Expected result: branch-to-branch comparisons become reviewable first-class backend objects.
  Expected endpoints: none in this slice; foundation for later `/story-development/branches/comparisons*` routes.
  Verification: targeted schema and persistence tests cover comparison record storage, branch pair linkage, deterministic ordering, and review-note retrieval.
- [x] BE-11D Branch merge decision persistence:
  add canonical schema and persistence support for `BranchMergeDecision`, including source branch, target branch, merge rationale, and resulting node links.
  Expected result: merge intent and accepted merge outcomes become durable backend records instead of implicit state changes.
  Expected endpoints: none in this slice; foundation for later `/story-development/branch-merges*` routes.
  Verification: targeted schema and persistence tests cover merge-decision storage, source-target linkage, rationale fields, and resulting decision-node references.
- [x] BE-11E Story branching service slice:
  implement bounded services for `create_story_branch`, `list_story_branches`, `compare_story_branches`, `select_active_branch`, and `record_branch_merge_decision`.
  Expected result: the user can fork the storyline from a decision point and later review or merge branches without overwriting the active path.
  Expected endpoints: none in this slice; service-only foundation for later `/story-development/branches/*` routes.
  Verification: service tests cover branching from a decision point, deterministic branch listing, branch comparison, active-branch changes, and explicit merge decisions.
- [x] BE-10A Story-development API surface for stable non-branching slices:
  expose bounded API routes for `decisions`, `review`, `planning`, and `drafting` only after their schema, persistence, and service contracts are stable.
  Expected result: the first story-development API routes are thin projections over accepted backend contracts rather than speculative endpoints.
  Formalization rule: do not use frontend implementation pressure as the trigger for these routes. Formalize the backend API only after the underlying slice is stable, and treat the API layer as a backend contract milestone in its own right.
  Out of scope for this slice: branch routes, frontend wiring, frontend state management, or UI-driven route shape changes before the backend contract is accepted.
  Verification: route tests cover happy path, validation errors, 404 behavior, and projection-only behavior for the first shipped slices.
- [x] BE-10B Story-development branching API surface:
  expose bounded API routes for branch identity, branch comparisons, branch-local state refs, active-branch selection, and merge decisions only after `BE-11E` is complete.
  Expected result: branch routes remain thin projections over accepted branching contracts instead of inventing new branch semantics in the route layer.
  Implemented route families: `/story-development/branches`, `/story-development/branches/active`, `/story-development/branches/comparisons`, `/story-development/branches/{branch_id}/state-refs`, and `/story-development/branch-merges`.
  Verification: route tests cover branch creation, listing, active-branch changes, comparison retrieval, branch-state-ref reads, merge-decision projection, validation errors, and 404 behavior.

## Frontend

See `docs/Frontend Design SRS v0.5.md` for the complete implementation plan with 32 deterministic task cards (FE-001 through FE-032).

**Technology Stack**: React 18 + Vite + TypeScript, Zustand, TanStack Query, Tailwind CSS, TipTap

### Phase 1: Foundation (Week 1-2)

- [x] FE-001: Vite + React + TypeScript setup with Tailwind CSS
  - **Write scope**: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tailwind.config.js`, `frontend/postcss.config.js`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`
  - **Dependencies**: None
  - **Expected outcome**: Development environment with hot reload, TypeScript checking, CSS utility classes
  - **Acceptance criteria**:
    - `npm install` completes without errors
    - `npm run dev` starts server on port 5173 with proxy to http://localhost:8000
    - `npm run build` produces `frontend/dist/` with < 500KB bundle
    - `npm run lint` runs ESLint without errors
    - Tailwind classes work (e.g., `class="flex items-center"` renders correctly)

- [x] FE-001A: Theming architecture with stage-based colors
  - **Write scope**: `frontend/src/theme/theme.ts`, `frontend/src/theme/variables.css`, `frontend/src/stores/themeStore.ts`, `frontend/src/components/theme/ThemeToggle.tsx`, `frontend/tailwind.config.js` (extend theme)
  - **Dependencies**: FE-001
  - **Expected outcome**: Stage-based theming with dark/light mode support
  - **Acceptance criteria**:
    - CSS variables defined in `:root` for light mode, `[data-theme="dark"]` for dark mode
    - ThemeStore manages: currentTheme (light/dark), stageTheme (planning/writing/review/inspect)
    - Stage themes have distinct primary colors:
      - Planning: blue-600 / blue-500
      - Writing: green-600 / green-500
      - Review: orange-600 / orange-500
      - Inspect: purple-600 / purple-500
    - ThemeToggle component in header with sun/moon icons
    - Auto-switch stageTheme based on uiStore.currentMode (via useEffect)
    - Theme persists in localStorage key `narrative-engine:theme`
    - Tailwind config extends colors with theme variables (e.g., `primary: var(--color-primary)`)
    - All buttons, badges, borders use theme colors (not hardcoded)

- [x] FE-BUILD-001: Resolve TypeScript compilation errors for production build
  - **Date**: March 26, 2026
  - **Write scope**: Multiple files across frontend/src/ (see AGENTS.md for detailed log)
  - **Dependencies**: All previous FE tasks
  - **Expected outcome**: Clean `npm run build` with no TypeScript errors
  - **Acceptance criteria**:
    - `npm run build` completes successfully
    - Output: ~312KB JS + 54KB CSS (gzipped: ~96KB + 10KB)
    - All type definitions match API contracts
    - No unused variable warnings
    - Vite path resolution works in production mode
  
  **Errors Fixed** (detailed log in AGENTS.md):
  1. Job status hook type narrowing issue (`useJobStatus.ts`)
  2. DraftArtifact mock data field name mismatches (`draftingMock.ts`)
  3. SceneCardList property access errors (`SceneCardList.tsx`)
  4. Missing SequenceData and ManifestData interfaces (`projectsApi.ts`)
  5. ReviewDecision interface incomplete fields (`review.ts`, `DecisionHistory.tsx`)
  6. Error handling utility missing functions (`errorHandling.ts`, `Fallback.tsx`)
  7. Import path errors in Fallback component (wrong relative paths)
  8. Unused variable warnings across multiple components
  9. Return type mismatch in BottomUtilityLayer (null not assignable to ReactElement)
  10. ErrorBoundary logError call signature error
  11. Toast import default vs named export issue (`ProjectCreateForm.tsx`)
  12. Toast type definition duration optional/required mismatch
  13. LogEntry fractionalSecondDigits TypeScript lib support
  14. JobMonitor hook return type camelCase/snake_case inconsistency
  15. Vite build path resolution error in index.html
  
  **Files Modified**: 18 files across components/, hooks/, services/, types/, lib/

- [x] FE-002: Zustand + TanStack Query configuration
  - **Write scope**: `frontend/src/lib/api.ts` (Axios instance), `frontend/src/lib/queryClient.ts`, `frontend/src/stores/uiStore.ts`, `frontend/src/stores/workspaceStore.ts`, `frontend/src/components/QueryProvider.tsx`
  - **Dependencies**: FE-001
  - **Expected outcome**: State management with devtools, server state caching, retry logic
  - **Acceptance criteria**:
    - Zustand devtools visible in browser when debugging
    - QueryClient configured with `retry: 3`, `retryDelay: 1000`
    - Axios instance targets the versioned API surface under `/v1` with 30s timeout
    - Error interceptor logs to console and returns error object
    - `npm run dev` loads without console errors

- [x] FE-003: Project list and creation (real API)
  - **Write scope**: `frontend/src/services/projects.ts`, `frontend/src/types/project.ts`, `frontend/src/components/projects/ProjectList.tsx`, `frontend/src/components/projects/ProjectCreateForm.tsx`, `frontend/src/components/projects/ProjectDetail.tsx`
  - **Dependencies**: FE-001, FE-002
  - **Expected outcome**: Users can create, list, select, and view projects
  - **Backend schema**: `ProjectSummaryResponse` { project_id, project_name, genre, tone_profile, story_structure, created_at, updated_at }
  - **Acceptance criteria**:
    - `GET /projects` returns list of `ProjectSummaryResponse` objects
    - Project list displays: project_name, genre, tone_profile, created_at (formatted)
    - Create form requires: project_name (1-100 chars), genre, tone_profile, story_structure
    - `POST /projects/create` with `ProjectCreateRequest` returns 201 with `ProjectDetailResponse`
    - Clicking project calls `GET /projects/{project_id}` and shows detail view
    - Detail view shows: manifest, project_dir, database_exists, sequence_exists, chapter_exists flags
    - Error states show user-friendly messages (404 "Project not found", 500 "Server error", network errors)

- [x] FE-004: Workspace notes persistence (Zustand + localStorage)
  - **Write scope**: `frontend/src/stores/workspaceStore.ts`, `frontend/src/types/workspace.ts`, `frontend/src/components/workspace/WorkspaceNotes.tsx`, `frontend/src/lib/storage.ts`
  - **Dependencies**: FE-001, FE-002
  - **Expected outcome**: Local workspace notes persist per project without affecting canonical state
  - **Acceptance criteria**:
    - Notes stored in localStorage with key `narrative-engine:{projectId}:workspace`
    - Auto-save debounced to 1000ms after last keystroke
    - Notes survive page reload within same project
    - Switching projects loads correct notes (per-project isolation)
    - UI displays "Personal notes (not saved to project)" banner
    - Notes cleared when project deleted (via cleanup hook)

- [x] FE-004A: Error boundary components
  - **Write scope**: `frontend/src/components/ErrorBoundary.tsx`, `frontend/src/components/Fallback.tsx`, `frontend/src/lib/errorHandling.ts`
  - **Dependencies**: FE-001, FE-002
  - **Expected outcome**: Graceful error handling without full page crashes
  - **Acceptance criteria**:
    - ErrorBoundary is React component with getDerivedStateFromError lifecycle
    - Wraps all major component trees in App.tsx (projects, workspace, jobs, etc.)
    - Fallback shows: error title, error message, retry button, "Report issue" link
    - Errors logged to console with component stack trace
    - Network errors show "Check your connection" message with retry
    - API errors show status code (404, 500) and backend message
    - Retry button resets error state and re-renders child components

- [x] FE-004B: Loading skeleton components
  - **Write scope**: `frontend/src/components/skeleton/SkeletonText.tsx`, `frontend/src/components/skeleton/SkeletonCard.tsx`, `frontend/src/components/skeleton/SkeletonList.tsx`, `frontend/src/components/skeleton/SkeletonEditor.tsx`
  - **Dependencies**: FE-001, FE-001A
  - **Expected outcome**: Consistent loading states across all components
  - **Acceptance criteria**:
    - SkeletonText: animated pulse bar with configurable height/width
    - SkeletonCard: card-shaped skeleton with header/body/footer sections
    - SkeletonList: multiple SkeletonCard instances (default 5)
    - SkeletonEditor: editor-shaped skeleton with toolbar/content areas
    - Animated pulse effect using CSS keyframes (opacity 0.4 to 1)
    - Used in all list/detail views during API fetch (isFetching state)
    - Fallback to skeleton on error retry

- [x] FE-004C: Toast notification system
  - **Write scope**: `frontend/src/components/toast/Toast.tsx`, `frontend/src/components/toast/ToastContainer.tsx`, `frontend/src/lib/toast.ts`, `frontend/src/types/toast.ts`
  - **Dependencies**: FE-001, FE-001A
  - **Expected outcome**: Consistent user feedback for actions
  - **Acceptance criteria**:
    - Toast types: success (green), error (red), warning (orange), info (blue)
    - Auto-dismiss after 5000ms with fade-out animation
    - Manual dismiss button (x icon) in top right
    - Queue multiple toasts (max 3 visible, rest queued)
    - Accessible: ARIA live region (role="status", aria-live="polite")
    - toast() function in toast.ts: toast.success(), toast.error(), toast.warning(), toast.info()
    - ToastContainer renders at bottom right of viewport (fixed position)
    - Toasts stack vertically with 8px gap

- [x] FE-005: Three-pane layout shell
  - **Write scope**: `frontend/src/components/layout/WorkspaceShell.tsx`, `frontend/src/components/layout/LeftRail.tsx`, `frontend/src/components/layout/CenterPane.tsx`, `frontend/src/components/layout/RightRail.tsx`, `frontend/src/components/layout/BottomUtility.tsx`, `frontend/src/components/layout/ModeSwitcher.tsx`, `frontend/src/types/workspace.ts`
  - **Dependencies**: FE-001, FE-002, FE-003
  - **Expected outcome**: Responsive three-pane layout with mode-based center pane
  - **Acceptance criteria**:
    - LeftRail: 250px width, collapsible to 60px (icon-only mode)
    - CenterPane: flex-grow, takes remaining space
    - RightRail: 300px width, collapsible
    - BottomUtility: 40px height when expanded, 0px when collapsed
    - ModeSwitcher has 4 buttons: Plan, Write, Review, Inspect
    - Mode changes update `uiStore.currentMode` without page reload
    - Layout responsive: below 1024px, rails stack vertically
    - Tailwind classes used for all styling (no inline styles)

- [x] FE-005A: Storyboard rail with scene cards
  - **Write scope**: `frontend/src/components/storyboard/Storyboard.tsx`, `frontend/src/components/storyboard/SceneCard.tsx`, `frontend/src/components/storyboard/SceneCardList.tsx`, `frontend/src/types/scene.ts`, `frontend/src/hooks/useStoryboard.ts`
  - **Dependencies**: FE-005
  - **Expected outcome**: Storyboard shows story progression with scene-level detail
  - **Acceptance criteria**:
    - SceneCard displays: title, purpose (max 2 lines), active characters (chips), conflict indicator
    - SceneCardList renders cards in order from planning API or mock data
    - Clicking SceneCard opens manuscript at corresponding location (via `useNavigate`)
    - Empty state shows "No scenes yet - create in planning board" with CTA button
    - Cards have hover state with subtle shadow elevation
    - Card height: min 80px, max 150px, overflow-hidden with ellipsis
    - Jump-to-manuscript logs navigation event to console (for testing)

- [x] FE-005B: Story bible rail section
  - **Write scope**: `frontend/src/components/bible/StoryBibleRail.tsx`, `frontend/src/components/bible/PinnedEntry.tsx`, `frontend/src/components/bible/BibleEntryList.tsx`, `frontend/src/types/bible.ts`, `frontend/src/stores/bibleStore.ts`
  - **Dependencies**: FE-005
  - **Expected outcome**: Users can pin characters, locations, rules for quick reference
  - **Acceptance criteria**:
    - PinnedEntry displays: type icon, title, summary (max 3 lines), unpin button
    - BibleEntryList shows pinned entries grouped by type (Characters, Locations, Rules, etc.)
    - Pin action adds entry to `bibleStore.pinnedEntries` array
    - Unpin action removes entry from store
    - Pinned entries persist in localStorage key `narrative-engine:{projectId}:pinnedBible`
    - Max 10 pinned entries per type (UI shows "Limit reached" toast)
    - Empty state shows "Pin items from world bible" with help text
    - Each entry has unique id for pin/unpin operations

### Phase 3: Flow Editor (Week 4)

- [x] FE-006: Editable flow editor (mock service)
  - **Write scope**: `frontend/src/services/mocks/flowMock.ts`, `frontend/src/services/flow.ts`, `frontend/src/components/flow/FlowEditor.tsx`, `frontend/src/components/flow/StageList.tsx`, `frontend/src/components/flow/StageCard.tsx`, `frontend/src/components/flow/StageActions.tsx`, `frontend/src/types/flow.ts`
  - **Dependencies**: FE-005
  - **Expected outcome**: Users can add, rename, reorder, disable, archive, and redefine stages
  - **Acceptance criteria**:
    - Mock service returns 8 default stages (Brainstorm, Foundation, Character, World Bible, Arc Selection, Planning, Drafting, Review)
    - StageCard displays: position number, display_name, stage_kind badge, progress state chip
    - StageActions shows: edit, disable, archive buttons (delete only for custom stages)
    - Add stage creates new `StoryFlowStage` with unique id, position at end
    - Rename updates `display_name` via mock service (2s delay simulation)
    - Reorder via drag-and-drop updates `position` field (using dnd-kit)
    - Disable changes `stage_configuration_state` to DISABLED
    - Archive changes `stage_configuration_state` to ARCHIVED
    - Redefine opens modal for `description` and `custom_prompt_guidance` fields
    - Stage edits show "Updating..." loading state during mock delay
    - Error states show "Failed to update stage" toast with retry button

### Phase 4: Planning Board (Week 5)

- [x] FE-007: Planning board view (real API)
  - **Write scope**: `frontend/src/services/planning.ts`, `frontend/src/components/planning/PlanningBoard.tsx`, `frontend/src/components/planning/ChapterList.tsx`, `frontend/src/components/planning/SceneList.tsx`, `frontend/src/types/planning.ts`
  - **Dependencies**: FE-005, FE-008 (FE-008 provides ChapterCard and SceneCard components)

- [x] FE-008: Chapter/scene card components
  - **Write scope**: `frontend/src/components/planning/ChapterCard.tsx`, `frontend/src/components/planning/SceneCard.tsx`, `frontend/src/components/planning/StatusChip.tsx`, `frontend/src/components/planning/CharacterChip.tsx`, `frontend/src/components/planning/DependencyBadge.tsx`
  - **Dependencies**: FE-005, FE-007

- [x] FE-009: Chapter packet builder
  - **Write scope**: `frontend/src/components/planning/ChapterPacketBuilder.tsx`, `frontend/src/components/planning/PacketContents.tsx`, `frontend/src/components/planning/PacketReferences.tsx`, `frontend/src/types/packet.ts`
  - **Dependencies**: FE-007, FE-008

### Phase 5: Manuscript Editor (Week 6-7)

- [x] FE-010: TipTap editor integration
  - **Write scope**: `frontend/src/components/editor/ManuscriptEditor.tsx`, `frontend/src/components/editor/EditorToolbar.tsx`, `frontend/src/components/editor/EditorContent.tsx`, `frontend/src/lib/tiptap.ts`, `frontend/src/hooks/useEditor.ts`, `frontend/package.json` (add @tiptap/react, @tiptap/starter-kit, @tiptap/extension-placeholder)
  - **Dependencies**: FE-005, FE-004

- [x] FE-011: Chapter tab management
  - **Write scope**: `frontend/src/components/editor/ChapterTabs.tsx`, `frontend/src/components/editor/Tab.tsx`, `frontend/src/stores/manuscriptStore.ts`, `frontend/src/hooks/useChapterTabs.ts`
  - **Dependencies**: FE-010

- [x] FE-012: Manuscript context rail
  - **Write scope**: `frontend/src/components/context/ContextRail.tsx`, `frontend/src/components/context/ChapterPlanPanel.tsx`, `frontend/src/components/context/SceneGoalsPanel.tsx`, `frontend/src/components/context/PinnedReferencesPanel.tsx`
  - **Dependencies**: FE-005B, FE-010
  - **Expected outcome**: Context stays visible while writing without obscuring manuscript
  - **Acceptance criteria**:
    - ContextRail renders in RightRail when mode === 'write'
    - ChapterPlanPanel shows: current chapter title, objective, conflict, stakes (from planning API)
    - SceneGoalsPanel shows: numbered list of scene goals for current chapter
    - PinnedReferencesPanel shows: pinned bible entries from bibleStore (FE-005B)
    - Each panel collapsible with chevron icon
    - Panels have max-height: 300px with overflow-y-auto
    - Empty states: "No plan available", "No scene goals set", "No pinned references"
    - Loading states show skeleton loaders during API fetch
    - Context updates when active chapter changes (via useEffect)

- [x] FE-013: Draft artifact promotion (mock service - backend endpoint not yet available)
  - **Write scope**: `frontend/src/services/drafting.ts`, `frontend/src/services/mocks/draftingMock.ts`, `frontend/src/components/drafting/DraftPromotion.tsx`, `frontend/src/components/drafting/DraftPreview.tsx`, `frontend/src/types/drafting.ts`
  - **Dependencies**: FE-010, FE-011
  - **Expected outcome**: Generated drafts can be promoted to editable manuscript state with provenance preserved
  - **Backend status**: GET endpoints exist for listing/retrieving, but NO POST endpoint for creating manuscript documents yet
  - **Acceptance criteria**:
    - Fetches artifacts from `GET /story-development/drafting/draft-artifacts?project_id={id}`
    - DraftPreview shows: title, state badge, provider badge, model badge, created_at
    - "Promote to Manuscript" button opens confirmation modal
    - Modal shows: artifact preview (first 500 chars), provenance info
    - Promotion uses MOCK service that simulates creating ManuscriptDocument (returns 200 after 2s delay)
    - Mock response includes: document_id, title, content, provenance { artifact_id, provider, model }
    - New document opens in new tab (FE-011) with mock data
    - Success toast: "Draft promoted to Chapter X (mock mode)"
    - Banner at top: "Promotion in mock mode - backend endpoint not yet available"
    - Feature flag `VITE_USE_MOCKS=true` enables mock, `false` shows "Coming soon" disabled state

### Phase 6: Job Execution (Week 8)

- [x] FE-014: Job launch interface (real API)
  - **Write scope**: `frontend/src/services/jobs.ts`, `frontend/src/components/jobs/JobLaunchForm.tsx`, `frontend/src/components/jobs/PhaseSelector.tsx`, `frontend/src/components/jobs/PayloadBuilder.tsx`, `frontend/src/types/job.ts`
  - **Dependencies**: FE-009, FE-002
  - **Expected outcome**: Users can launch backend jobs with proper context
  - **Backend schema**: `JobCreateRequest` { phase: JobPhase, payload: dict }, `JobStatusResponse` { id, phase, status, attempt_number, progress_current, progress_total, error }
  - **Acceptance criteria**:
    - PhaseSelector shows: P-100 (Architect), P-200 (Sequencer), P-300 (Drafter), P-400 (Compiler) as JobPhase enum values
    - PayloadBuilder shows JSON editor with packet context pre-filled (from FE-009 chapter packet)
    - "Launch Job" button calls `POST /jobs/create` with `{ phase, payload }`
    - Success (202): returns `JobStatusResponse` with job id, auto-opens BottomUtility with polling (FE-015)
    - Validation: phase required (enum value), payload valid JSON object
    - Error states: 400 shows validation errors, 409 shows idempotency conflict, 500 shows server error
    - Loading state: button disabled with spinner during request
    - Form resets after successful submission
    - Note: Model selection is NOT part of job creation - models are configured in backend, not frontend

- [x] FE-015: Job status polling with TanStack Query
  - **Write scope**: `frontend/src/hooks/useJobStatus.ts`, `frontend/src/components/jobs/JobStatusIndicator.tsx`, `frontend/src/components/jobs/JobProgress.tsx`, `frontend/src/lib/queryClient.ts` (update config)
  - **Dependencies**: FE-014, FE-002
  - **Expected outcome**: Real-time status updates with 600ms polling interval
  - **Backend schema**: `JobStatusResponse` { id, phase, status, attempt_number, current_phase, current_step, progress_current, progress_total, error }
  - **Acceptance criteria**:
    - useJobStatus hook accepts job_id (UUID), returns { status, phase, progress, error, isPolling, current_step }
    - Polling interval: 600ms via `refetchInterval: 600` in useQuery
    - JobStatusIndicator shows: QUEUED (gray), RUNNING (blue pulse), COMPLETED (green), FAILED (red)
    - JobProgress shows percentage bar: (progress_current / progress_total * 100)%, shows "0%" when null
    - Displays current_phase and current_step as text labels when available
    - Terminal states (COMPLETED/FAILED) stop polling automatically
    - FAILED state shows error message and "Retry" button that calls `POST /jobs/{id}/retry` with `{ retry_reason: "operator_retry" }`
    - COMPLETED state shows "View Results" button (navigates to artifact)
    - Polling visible in browser devtools Network tab (requests every 600ms)
    - Error handling: network errors retry 3 times before showing failed state

- [x] FE-016: Job logs viewer
  - **Write scope**: `frontend/src/components/jobs/JobLogsViewer.tsx`, `frontend/src/components/jobs/LogEntry.tsx`, `frontend/src/hooks/useJobLogs.ts`, `frontend/src/lib/download.ts`
  - **Dependencies**: FE-015
  - **Expected outcome**: Logs readable and exportable
  - **Backend schema**: `JobLogsResponse` { id, entries: [{ timestamp, level, message }] }
  - **Acceptance criteria**:
    - Fetches logs from `GET /jobs/{job_id}/logs`
    - LogEntry displays: timestamp (formatted HH:mm:ss.SSS), level badge (INFO/WARNING/ERROR), message (monospace font)
    - Logs sorted by timestamp ascending (oldest first) as returned by backend
    - Auto-scroll to bottom when new logs arrive (useEffect with ref)
    - "Pause Auto-scroll" checkbox stops auto-scroll when checked
    - "Export Logs" button downloads logs.txt with all entries (timestamp | level | message format)
    - Filter dropdown: All, INFO, WARNING, ERROR
    - Search input filters logs by message text (case-insensitive)
    - Empty state: "No logs available yet"
    - Loading state: skeleton log entries during fetch

- [x] FE-017: Bottom utility layer
  - **Write scope**: `frontend/src/components/layout/BottomUtility.tsx`, `frontend/src/components/jobs/JobMonitor.tsx`, `frontend/src/stores/jobStore.ts`, `frontend/src/hooks/useJobMonitor.ts`
  - **Dependencies**: FE-005, FE-015, FE-016
  - **Expected outcome**: Job monitoring visible across all workspace modes
  - **Acceptance criteria**:
    - BottomUtility renders at bottom of WorkspaceShell (FE-005)
    - Height: 0px when collapsed, 200px when expanded
    - Toggle button in bottom right corner (expand/collapse)
    - JobMonitor shows: active job_id, status indicator, progress bar, logs preview (last 3 lines)
    - "View Full Logs" button expands logs panel within BottomUtility
    - "Retry" button visible for FAILED jobs
    - Job monitoring persists across mode switches (Plan/Write/Review/Inspect)
    - Auto-collapse after COMPLETED state for 5 seconds (toast notification)
    - Multiple jobs: shows most recent job, queue indicator if jobs pending
    - State persisted in jobStore for resilience across component unmounts

### Phase 7: Inspect & Provenance (Week 9)

- [x] FE-018: Inspect mode integration
  - **Write scope**: `frontend/src/components/inspect/InspectMode.tsx`, `frontend/src/components/inspect/InspectTabs.tsx`, `frontend/src/types/inspect.ts`
  - **Dependencies**: FE-005, FE-019, FE-020
  - **Expected outcome**: First-class center-pane mode for inspecting job execution
  - **Acceptance criteria**:
    - InspectMode renders in CenterPane when mode === 'inspect'
    - InspectTabs shows: Steps tab, Lineage tab, Attempts tab
    - Mode switch preserves job_id context in uiStore.inspectContext
    - "Back to Manuscript" button switches mode back to 'write'
    - URL includes ?mode=inspect&job_id={id} for shareability
    - Empty state: "Select a job to inspect" when no context

- [x] FE-019: Step timeline component (real API)
  - **Write scope**: `frontend/src/components/inspect/StepTimeline.tsx`, `frontend/src/components/inspect/StepCard.tsx`, `frontend/src/hooks/useJobSteps.ts`, `frontend/src/types/inspect.ts`
  - **Dependencies**: FE-018
  - **Expected outcome**: Steps render in backend order with provenance badges
  - **Backend schema**: `StepRecord` { step_record_id, logical_run_id, run_id, run_kind, attempt_number, step_name, step_index, state, project_id, model_id, backend_name, started_at, finished_at, duration_seconds, error_code }
  - **Acceptance criteria**:
    - Fetches steps from `GET /jobs/{job_id}/steps?attempt={n}`
    - StepCard displays: step_name, state badge, duration_seconds, model_id/backend_name
    - Steps sorted by step_index ascending
    - State colors: PENDING (gray), RUNNING (blue pulse), COMPLETED (green), FAILED (red)
    - Provenance badge shows: model_id, backend_name, backend_version (compact chip)
    - Error states show error_code and error_category in red text
    - Loading state shows SkeletonList during fetch
    - Empty state: "No steps recorded yet"

- [x] FE-020: Artifact lineage component (real API)
  - **Write scope**: `frontend/src/components/inspect/ArtifactLineage.tsx`, `frontend/src/components/inspect/LineageGraph.tsx`, `frontend/src/components/inspect/ArtifactCard.tsx`, `frontend/src/hooks/useJobLineage.ts`
  - **Dependencies**: FE-018
  - **Expected outcome**: Lineage shows history with CANONICAL/SUPERSEDED states
  - **Backend schema**: `ArtifactLineageView` { artifact_id, artifact_kind, state, run_id, step_name, created_at, provenance: { provider, model, backend_name } }
  - **Acceptance criteria**:
    - Fetches lineage from `GET /jobs/{job_id}/lineage?attempt={n}`
    - LineageGraph shows artifacts as nodes with directed edges (parent→child)
    - ArtifactCard displays: artifact_kind, state badge, provenance, created_at
    - State colors: CANONICAL (green), SUPERSEDED (yellow), REJECTED (red), DRAFT (gray)
    - Clicking artifact shows preview panel with content (first 1000 chars)
    - Loading state shows SkeletonList during fetch
    - Empty state: "No artifacts generated yet"

- [x] FE-021: Provenance badges
  - **Write scope**: `frontend/src/components/common/ProvenanceBadge.tsx`, `frontend/src/components/common/ProviderBadge.tsx`, `frontend/src/components/common/ModelBadge.tsx`, `frontend/src/lib/provenance.ts`
  - **Dependencies**: FE-001A
  - **Expected outcome**: Provenance visible wherever generated output appears
  - **Acceptance criteria**:
    - ProvenanceBadge displays: provider icon, model name, backend version
    - ProviderBadge shows: OpenAI (O icon), Anthropic (A icon), Local (⚡ icon), etc.
    - ModelBadge shows: model name truncated to 20 chars with tooltip
    - Compact mode: single line with icons only
    - Expanded mode: multi-line with full details
    - Used in: StepCard, ArtifactCard, DraftPreview, Manuscript header
    - Theme-aware colors (uses stage theme primary color)

### Phase 8: Review Workspace (Week 10)

- [x] FE-022: Checker findings list (real API)
  - **Write scope**: `frontend/src/services/review.ts`, `frontend/src/components/review/FindingsList.tsx`, `frontend/src/components/review/FindingCard.tsx`, `frontend/src/components/review/SeverityBadge.tsx`, `frontend/src/types/review.ts`
  - **Dependencies**: FE-005, FE-004B
  - **Expected outcome**: Findings filterable, jump to source text
  - **Backend schema**: `CheckerFinding` { finding_id, project_id, source_object_id, source_object_kind, severity, summary, details, source_context }
  - **Acceptance criteria**:
    - Fetches findings from `GET /story-development/review/findings?project_id={id}&source_object_kind={kind}&source_object_id={id}`
    - FindingCard displays: severity badge, summary (max 2 lines), source_object_kind
    - SeverityBadge colors: low (blue), medium (yellow), high (orange), critical (red)
    - Filter dropdown: All severities, or individual severity levels
    - Filter by source_object_kind (chapter-plan, scene-plan, manuscript, etc.)
    - Clicking finding shows details panel with source_context
    - "Jump to Source" button navigates to related object (if manuscript, opens editor)
    - Loading state shows SkeletonList during fetch
    - Empty state: "No findings for this project"

- [x] FE-023: Review decision interface (mock service - backend endpoint not yet available)
  - **Write scope**: `frontend/src/services/review.ts`, `frontend/src/services/mocks/reviewMock.ts`, `frontend/src/components/review/DecisionForm.tsx`, `frontend/src/components/review/DecisionHistory.tsx`, `frontend/src/types/review.ts`
  - **Dependencies**: FE-022
  - **Expected outcome**: Users can record review decisions that route to planning/drafting
  - **Backend status**: GET endpoints exist for listing/retrieving, but NO POST endpoint for creating decisions yet
  - **Backend schema**: `ReviewDecision` { decision_id, project_id, finding_id, target_kind, target_id, decision_action, rationale, routed_to_stage, created_at }
  - **Acceptance criteria**:
    - DecisionForm shows: finding summary, decision_action dropdown, rationale textarea
    - decision_action values: "accept", "reject", "defer", "escalate", "refine" (strings, not enum)
    - routed_to_stage auto-selected based on decision_action (accept→drafting, reject→archive, refine→drafting)
    - "Record Decision" button uses MOCK service (2s delay, returns decision_id)
    - DecisionHistory shows prior decisions for finding (from GET endpoint)
    - Success toast: "Decision recorded (mock mode)"
    - Banner at top: "Decision recording in mock mode - backend endpoint not yet available"
    - Feature flag VITE_USE_MOCKS=true enables mock, false shows "Coming soon" disabled state

- [x] FE-024: Role-model checker UI (real API)
  - **Write scope**: `frontend/src/services/checker.ts`, `frontend/src/components/checker/CheckerForm.tsx`, `frontend/src/components/checker/CheckerResults.tsx`, `frontend/src/components/checker/RoleModelSelector.tsx`, `frontend/src/components/checker/CheckerStatus.tsx`, `frontend/src/types/checker.ts`
  - **Dependencies**: FE-005, FE-022, FE-015
  - **Expected outcome**: Model selection per role, run checker, display results with status polling
  - **Backend endpoints**: `GET /models`, `POST /role-model-checker/run`, `POST /role-model-checker/start`, `GET /role-model-checker/{run_id}/status`, `GET /role-model-checker/{run_id}/steps`, `GET /role-model-checker/{run_id}/lineage`, `GET /role-model-checker/{run_id}/attempts`, `POST /role-model-checker/{run_id}/retry`
  - **Backend schema**: `ModelCatalogResponse`, `RoleModelCheckStatusResponse` { run_id, status, attempt_number, progress_current, progress_total, error }, `RoleModelCheckStepsResponse`, `RoleModelCheckLineageResponse`
  - **Acceptance criteria**:
    - RoleModelSelector shows roles from ModelCatalogResponse.workflow_order
    - Each role has model dropdown from ModelCatalogResponse.discovered_models
    - "Run Checker" button triggers `POST /role-model-checker/run` with selected models
    - CheckerStatus shows: QUEUED (gray), RUNNING (blue pulse), COMPLETED (green), FAILED (red)
    - Status polling every 600ms via useQuery with refetchInterval (similar to FE-015)
    - CheckerResults displays: pass/fail state, findings count, summary
    - Pass state: green badge, "No issues found", links to findings list
    - Fail state: red badge, findings list (FE-022 integration)
    - Steps tab shows execution steps (similar to FE-019)
    - Lineage tab shows artifact lineage (similar to FE-020)
    - "Retry" button for FAILED jobs calls `POST /role-model-checker/{run_id}/retry`
    - Loading state shows spinner with "Running checker..." message
    - Error state shows "Checker failed" with error message and retry button

- [ ] FE-024A: Story branches UI (real API)
  - **Write scope**: `frontend/src/services/branches.ts`, `frontend/src/components/branches/BranchList.tsx`, `frontend/src/components/branches/BranchCard.tsx`, `frontend/src/components/branches/BranchComparison.tsx`, `frontend/src/components/branches/MergeDecisionForm.tsx`, `frontend/src/types/branches.ts`
  - **Dependencies**: FE-005, FE-022
  - **Expected outcome**: Users can create, compare, and merge story branches
  - **Backend endpoints**: `GET /story-development/branches`, `POST /story-development/branches`, `GET /story-development/branches/active`, `POST /story-development/branches/active`, `POST /story-development/branches/comparisons`, `GET /story-development/branches/comparisons`, `GET /story-development/branches/comparisons/{id}`, `POST /story-development/branches/merge-decisions`, `GET /story-development/branches/merge-decisions`, `GET /story-development/branches/{id}/state-refs`
  - **Backend schema**: `StoryBranch` { branch_id, project_id, name, description, parent_branch_id, state, created_at }, `BranchComparisonRecord` { comparison_id, project_id, branch_a_id, branch_b_id, differences, created_at }, `BranchMergeDecision` { merge_decision_id, project_id, source_branch_id, target_branch_id, decision, rationale, created_at }
  - **Acceptance criteria**:
    - BranchList displays all branches for project with state badges
    - BranchCard shows: name, description (max 2 lines), state badge, created_at
    - State colors: active (green), merged (blue), archived (gray)
    - "Create Branch" button opens form with name, description, parent selection
    - "Set Active" button calls `POST /story-development/branches/active`
    - "Compare" button opens BranchComparison with side-by-side diff
    - BranchComparison shows differences between two branches
    - "Merge" button opens MergeDecisionForm
    - MergeDecisionForm shows: source/target branches, decision dropdown, rationale textarea
    - Decision values: "merge", "reject", "defer"
    - MergeDecision history shows prior decisions for branch
    - Loading states show SkeletonList during fetch
    - Empty state: "No branches yet - create from active branch"

- [ ] FE-024B: Story decision nodes UI (real API)
  - **Write scope**: `frontend/src/services/decisions.ts`, `frontend/src/components/decisions/DecisionTree.tsx`, `frontend/src/components/decisions/DecisionNode.tsx`, `frontend/src/components/decisions/DecisionPath.tsx`, `frontend/src/types/decisions.ts`
  - **Dependencies**: FE-005, FE-024A
  - **Expected outcome**: Visualize story decision points and their paths
  - **Backend endpoints**: `GET /story-development/decisions`, `GET /story-development/decisions/{node_id}`, `GET /story-development/decisions/{node_id}/path`
  - **Backend schema**: `StoryDecisionNode` { node_id, project_id, decision_point, options: [{ option_id, label, next_node_id }], created_at }, `StoryDecisionPath` { path_id, project_id, nodes: [node_id], outcome, created_at }
  - **Acceptance criteria**:
    - DecisionTree renders nodes as tree/graph with directed edges
    - DecisionNode displays: decision_point, options (as clickable buttons)
    - Clicking option navigates to next node in tree
    - DecisionPath shows current path from root to active node
    - Path displays as breadcrumb navigation
    - "Reset" button returns to root node
    - Loading state shows SkeletonList during fetch
    - Empty state: "No decision nodes defined"

- [ ] FE-024C: Inspect run links UI (real API)
  - **Write scope**: `frontend/src/services/inspectLinks.ts`, `frontend/src/components/inspect/InspectRunLinks.tsx`, `frontend/src/components/inspect/InspectLinkCard.tsx`, `frontend/src/types/inspect.ts`
  - **Dependencies**: FE-018, FE-022
  - **Expected outcome**: Link review findings to inspect runs for traceability
  - **Backend endpoints**: `GET /story-development/review/inspect-links`, `GET /story-development/review/inspect-links/{link_id}`
  - **Backend schema**: `InspectRunLink` { link_id, project_id, finding_id, run_id, run_kind, created_at }
  - **Acceptance criteria**:
    - InspectRunLinks fetches links filtered by finding_id or run_id
    - InspectLinkCard displays: finding_id, run_id, run_kind badge, created_at
    - Clicking link opens inspect mode (FE-018) with run_id context
    - Clicking finding_id navigates to finding in review (FE-022)
    - Filter dropdown: All, by finding, by run
    - Loading state shows SkeletonList during fetch
    - Empty state: "No inspect links found"

### Phase 9: Manuscript Aids (Week 11-12)

- [ ] FE-025: Manuscript aids panel (mock service - backend endpoint not yet available)
  - **Write scope**: `frontend/src/services/mocks/manuscriptAidsMock.ts`, `frontend/src/components/aids/AidsPanel.tsx`, `frontend/src/components/aids/AidAction.tsx`, `frontend/src/components/aids/SelectionAids.tsx`, `frontend/src/components/aids/SceneAids.tsx`, `frontend/src/types/aids.ts`
  - **Dependencies**: FE-010, FE-026 (FE-026 provides selection lifecycle handling)
  - **Expected outcome**: Selection-based and scene-based actions in right rail
  - **Backend status**: GET endpoints exist for revision suggestions, but NO POST endpoint for creating suggestions yet
  - **Backend schema**: `RevisionSuggestion` { suggestion_id, project_id, target_kind, target_id, anchor_text, proposed_revision, state, created_at }
  - **Acceptance criteria**:
    - AidsPanel renders in RightRail when mode === 'write'
    - SelectionAids shows: "Rewrite", "Summarize", "Expand", "Check grammar" buttons
    - SceneAids shows: "Add conflict", "Strengthen stakes", "Check continuity" buttons
    - SelectionAids disabled when no text selected (opacity-50, cursor-not-allowed)
    - SceneAids always enabled (scene context from active chapter)
    - Clicking aid action uses MOCK service (2s delay, returns suggestion)
    - Banner at top: "Manuscript aids in mock mode - backend endpoint not yet available"
    - Feature flag VITE_USE_MOCKS=true enables mock, false shows "Coming soon"

- [ ] FE-026: Selection lifecycle handling
  - **Write scope**: `frontend/src/hooks/useSelection.ts`, `frontend/src/stores/selectionStore.ts`, `frontend/src/lib/selection.ts`
  - **Dependencies**: FE-010, FE-025
  - **Expected outcome**: Selection stable through aid request/response
  - **Acceptance criteria**:
    - useSelection hook returns: selectedText, selectionRange, hasSelection
    - Selection tracked via TipTap editor state (editor.state.selection)
    - selectionStore anchors selectedText with start/end positions
    - Selection preserved during aid request (stored before API call)
    - Selection restored after aid response (re-applies to editor)
    - Selection cleared on manual delete or new selection
    - Selection survives tab switches (persisted in store)
    - Empty selection shows "Select text to enable aids" hint

- [ ] FE-027: Diff review interface
  - **Write scope**: `frontend/src/components/diff/DiffViewer.tsx`, `frontend/src/components/diff/DiffLine.tsx`, `frontend/src/components/diff/DiffControls.tsx`, `frontend/src/lib/diff.ts`
  - **Dependencies**: FE-025, FE-026
  - **Expected outcome**: Proposed revisions reviewable without auto-apply
  - **Backend schema**: Uses RevisionSuggestion.proposed_revision field
  - **Acceptance criteria**:
    - DiffViewer shows side-by-side diff: original (left), proposed (right)
    - DiffLine displays: line number, content, add/remove/neutral indicator
    - Added lines: green background, + prefix
    - Removed lines: red background, - prefix
    - Neutral lines: gray background, space prefix
    - DiffControls shows: "Accept", "Reject", "Refine" buttons
    - "Accept" applies proposed revision to editor (mock for now)
    - "Reject" closes diff without changes
    - "Refine" opens editor to modify proposed revision
    - Diff generated via simple string comparison (no external library)
    - Loading state shows "Generating diff..." during comparison

- [ ] FE-028: Suggestion history (mock service)
  - **Write scope**: `frontend/src/services/mocks/manuscriptAidsMock.ts` (extend), `frontend/src/components/aids/SuggestionHistory.tsx`, `frontend/src/components/aids/SuggestionCard.tsx`, `frontend/src/components/aids/SuggestionCompare.tsx`
  - **Dependencies**: FE-025, FE-027
  - **Expected outcome**: History scrollable, comparisons clear
  - **Backend schema**: Uses RevisionSuggestion with state field (pending/accepted/rejected)
  - **Acceptance criteria**:
    - SuggestionHistory fetches from mock service (filters by project_id, target_id)
    - SuggestionCard displays: anchor_text (truncated), state badge, created_at
    - State colors: pending (yellow), accepted (green), rejected (red)
    - Clicking suggestion opens SuggestionCompare (diff view)
    - SuggestionCompare shows: original vs proposed diff (FE-027)
    - "Restore" button for rejected suggestions (re-opens for review)
    - History sorted by created_at descending (newest first)
    - Empty state: "No suggestions yet"
    - Loading state shows SkeletonList during fetch

### Phase 10: Story Development Features (Week 13+)

- [ ] FE-029: Brainstorm workspace (mock service)
  - **Write scope**: `frontend/src/services/mocks/brainstormMock.ts`, `frontend/src/components/brainstorm/BrainstormWorkspace.tsx`, `frontend/src/components/brainstorm/IdeaCard.tsx`, `frontend/src/components/brainstorm/IdeaCluster.tsx`, `frontend/src/types/brainstorm.ts`
  - **Dependencies**: FE-005
  - **Expected outcome**: Idea capture, clustering, keep/discard/park, promote actions
  - **Backend status**: No API endpoints exist for brainstorm objects
  - **Mock schema**: `BrainstormIdea` { idea_id, project_id, content, tags, state, cluster_id, created_at }
  - **Acceptance criteria**:
    - BrainstormWorkspace renders in CenterPane when mode === 'plan' and submode === 'brainstorm'
    - IdeaCard displays: content, tags (chips), state badge, action buttons
    - State colors: active (blue), parked (gray), discarded (red with strikethrough)
    - "Keep" button: sets state to active
    - "Discard" button: sets state to discarded
    - "Park" button: sets state to parked
    - "Promote" button: converts to canonical object (mock, shows toast)
    - IdeaCluster groups ideas by cluster_id (drag-and-drop to recluster)
    - "New Idea" textarea with "Add" button (mock create)
    - Banner: "Brainstorm in mock mode - backend endpoint not yet available"

- [ ] FE-030: Foundation screen (mock service)
  - **Write scope**: `frontend/src/services/mocks/foundationMock.ts`, `frontend/src/components/foundation/FoundationEditor.tsx`, `frontend/src/components/foundation/FoundationField.tsx`, `frontend/src/components/foundation/ImpactWarning.tsx`, `frontend/src/types/foundation.ts`
  - **Dependencies**: FE-005
  - **Expected outcome**: Foundation editable with impact visibility
  - **Backend status**: No API endpoints exist for foundation objects
  - **Mock schema**: `Foundation` { project_id, premise, logline, themes, constraints, downstream_impacts }
  - **Acceptance criteria**:
    - FoundationEditor renders in CenterPane when mode === 'plan' and submode === 'foundation'
    - FoundationField displays: label, textarea/input, save button, impact warning
    - Fields: premise (textarea), logline (textarea), themes (tag input), constraints (tag input)
    - ImpactWarning shows: "Changing this affects: Chapter Plans, Scene Plans, Manuscripts"
    - Warning displays when field is modified (yellow background)
    - "Save" button uses mock service (2s delay, shows success toast)
    - Auto-save debounced to 2000ms
    - Banner: "Foundation in mock mode - backend endpoint not yet available"

- [ ] FE-031: Character builder (mock service)
  - **Write scope**: `frontend/src/services/mocks/characterMock.ts`, `frontend/src/components/characters/CharacterBuilder.tsx`, `frontend/src/components/characters/CharacterProfile.tsx`, `frontend/src/components/characters/RelationshipMap.tsx`, `frontend/src/components/characters/ContradictionWarning.tsx`, `frontend/src/types/character.ts`
  - **Dependencies**: FE-005
  - **Expected outcome**: Goals, flaws, relationships visible together
  - **Backend status**: No API endpoints exist for character objects
  - **Mock schema**: `Character` { character_id, project_id, name, description, goals, flaws, relationships: [{ target_id, relationship_type }] }
  - **Acceptance criteria**:
    - CharacterBuilder renders in CenterPane when mode === 'plan' and submode === 'characters'
    - CharacterProfile displays: name, description, goals (list), flaws (list), relationships
    - RelationshipMap shows characters as nodes, relationships as directed edges
    - ContradictionWarning shows: "Character X has conflicting goals in Chapter Y"
    - "New Character" button opens creation form (mock)
    - "Edit" button opens profile editor (mock update)
    - "Delete" button removes character (mock delete)
    - Banner: "Character builder in mock mode - backend endpoint not yet available"

- [ ] FE-032: World bible workspace (mock service)
  - **Write scope**: `frontend/src/services/mocks/worldBibleMock.ts`, `frontend/src/components/bible/WorldBibleWorkspace.tsx`, `frontend/src/components/bible/BibleEntry.tsx`, `frontend/src/components/bible/BibleSearch.tsx`, `frontend/src/components/bible/ContinuityWarning.tsx`, `frontend/src/types/bible.ts`
  - **Dependencies**: FE-005, FE-005B
  - **Expected outcome**: Entries source-linked, warnings readable in context
  - **Backend status**: No API endpoints exist for world bible objects
  - **Mock schema**: `BibleEntry` { entry_id, project_id, entry_type, title, content, source_refs: [{ object_kind, object_id }], continuity_warnings: [{ warning_type, message }] }
  - **Acceptance criteria**:
    - WorldBibleWorkspace renders in CenterPane when mode === 'plan' and submode === 'bible'
    - BibleEntry displays: entry_type icon, title, content, source_refs (chips), warnings
    - Entry types: location, object, rule, event, concept
    - BibleSearch filters entries by title/content (client-side)
    - ContinuityWarning shows: "Entry X contradicts Chapter Y, Scene Z"
    - "Pin" button adds to pinned entries (FE-005B integration)
    - "New Entry" button opens creation form (mock)
    - "Edit" button opens entry editor (mock update)
    - Banner: "World bible in mock mode - backend endpoint not yet available"

### Migration Tasks

- [ ] Migrate vanilla JS prototype to React (parallel development, week 1-2)
- [ ] Test React frontend thoroughly before cutover (week 3-4)
- [ ] Switch default route to React app, decommission vanilla JS (week 5+)

## Docs Contract Hardening

- [x] Write a single "Story Development Canonical Contract" doc section or appendix that all other story-development docs reference for object names, lifecycle enums, and term mappings.
- [x] Update `docs/Story Development Product Spec v0.1.md` so editable-flow rules explicitly distinguish stage deletion from disabling, optionality, and archival behavior.
- [x] Update `docs/Narrative SRS v0.3.md` so story-development sections describe an aspirational writing product and stop using reconstruction-grade language for these features.
- [x] Update `docs/Narrative SRS v0.3.md` so story-development workflow states describe actual states rather than mixing stage categories with state enums.
- [x] Update `docs/Narrative SRS v0.3.md` and `docs/Frontend Design SRS v0.4.md` so implemented-now versus target-state language is internally consistent for checker runtime behavior and inspect surfaces.
- [x] Update `docs/Frontend Design SRS v0.4.md` so backend-object names match the canonical product and backend contract instead of introducing competing object labels without mappings.
- [x] Update `docs/Frontend Design SRS v0.4.md` section 19 so each frontend TODO becomes an agent-sized deterministic task card instead of a multi-surface implementation wave.
- [x] Update `docs/Orchestrator Deterministic Task Spec v0.1.md` with concrete callable operation templates for capture, promote, compare, detect, rewrite, review, and route task families.
- [x] Add a canonical drafting/provenance contract section that explains how generated artifacts, author-edited manuscript buffers, suggestion diffs, and promoted canonical outputs relate to each other.
- [x] Add a canonical planning contract section that states whether beat, sequence, chapter, and scene "cards" are persistence objects, presentation objects, or projections over plan records.

## Testing

- [x] Add smoke coverage for the current API surface.
- [x] Add persistence coverage for jobs, checker runs, and project projections.
- [x] Add contract coverage for planned step-record and artifact-lineage expectations.
- [x] Add live persistence coverage for step records and artifact lineage.
- [x] Add failure-mode coverage for duplicate submission, accepted-start polling, and terminal transition protection.
- [x] Add failure-mode coverage for idempotent replay and idempotency conflicts.
- [x] Add failure-mode tests for stale lease handling.
- [x] Add retry-lineage coverage for explicit operator requeue of failed jobs and checker runs.
- [x] Add failure-mode tests for partial persistence failure and lock contention.
- [ ] Add broader integration coverage for orchestration and runtime behavior.
- [x] Add regression coverage proving failed runtime jobs do not expose placeholder-generated project artifacts through `GET /projects/{project_id}/sequence` or `GET /projects/{project_id}/chapter-1`.
- [x] Add regression coverage proving rerun canonical job artifacts supersede prior lineage rows instead of accumulating multiple active `CANONICAL` entries.
- [x] Add API tests for `GET /jobs/{job_id}/steps`, `GET /jobs/{job_id}/lineage`, `GET /role-model-checker/{run_id}/steps`, and `GET /role-model-checker/{run_id}/lineage`.
- [x] Add pagination tests for `GET /jobs/{job_id}/steps` and `GET /jobs/{job_id}/lineage` now that attempt-filter support is covered.
- [x] Add pagination tests for `GET /role-model-checker/{run_id}/steps` and `GET /role-model-checker/{run_id}/lineage` now that attempt-filter support is covered.
- [ ] Add runtime integration tests for one real provider-backed `architect` step through the executor path.
- [ ] Add tests for manuscript-aid request contracts and diff-style response payloads once the backend surface is defined.
- [x] Update CI to run `tests/test_inference_runtime.py` and current projection-endpoint tests on push and pull request.

## Subagent Queue

- [x] `Curie`: implement BE-01 by owning `app/schemas/story_development.py`, `app/schemas/enums.py`, `app/schemas/__init__.py`, and a new targeted schema test file. Do not edit persistence or service files. You are not alone in the codebase; accommodate others' changes and do not revert them.
- [x] `Kepler`: implement BE-02 by owning `app/persistence/sqlite.py`, a new `app/persistence/story_development.py`, `app/persistence/__init__.py`, and a new targeted persistence test file. Do not edit schema or service files unless a minimal import/export adjustment is required. You are not alone in the codebase; accommodate others' changes and do not revert them.
- [x] `Pasteur`: implement BE-03 by owning a new editable-flow service module plus focused service tests, using the canonical docs contract and existing persistence/service patterns. Do not edit schema files and do not replace others' work; adjust to their changes instead.
- [x] `Lagrange`: implement BE-04 by owning the brainstorm and promotion service slice with bounded `capture_brainstorm_item`, `cluster_brainstorm_items`, and `promote_brainstorm_item` operations. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/brainstorm/*` routes. Expected outcome: brainstorm items can be persisted, clustered, and promoted with source links and no API wiring yet. Keep the write scope limited to the new service module and a focused test file.
- [x] `Descartes`: implement BE-05 by owning the foundation profile and downstream-impact service slice with bounded revision history behavior and review-cue generation. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/foundation/*` routes. Expected outcome: active foundation reads, revision history, and downstream review cues work without API wiring yet. Keep the write scope limited to the new service module and a focused test file.
- [x] `Gauss`: implement BE-06A by owning canonical persistence for `RelationshipEdge`, `ArcCandidate`, `ArcSelection`, and `ArcStageMap` in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/characters/*`, `/story-development/world-bible/*`, and `/story-development/arcs/*` routes. Expected outcome: BE-06 services can rely on durable repository-backed state for all canonical story-knowledge objects.
- [x] `Laplace`: implement BE-06B by owning canonical persistence for `ArcComparisonRecord` and selection-to-comparison links in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/arcs/comparisons/*` and `/story-development/arcs/*` routes. Expected outcome: arc comparison history becomes a first-class persisted reviewable object rather than advisory service-local memory.
- [x] `Nozick`: implement BE-06C by owning canonical persistence for `StoryDecisionNode` in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/decisions/*`, `/story-development/arcs/*`, and future flow-history routes. Expected outcome: user-made story-shaping decisions become first-class persisted reviewable nodes rather than being inferred from current state alone.
- [x] `Bohr`: implement BE-06D by owning schema support for `ArcComparisonRecord`, selection-to-comparison links, and `StoryDecisionNode` enum-driven timeline and tree fields in `app/schemas/story_development.py`, `app/schemas/__init__.py`, and a focused schema test file. Expected endpoints for this slice: none yet; schema-only foundation for later `/story-development/arcs/comparisons/*` and `/story-development/decisions/*` routes. Expected outcome: typed schema contracts match the persisted reviewable decision objects now required by the docs.
- [x] `Euler`: retry BE-06 only after `BE-06A`, `BE-06B`, `BE-06C`, and `BE-06D` land, by owning the character, world bible, and arc-selection service slice with bounded compare, upsert, select, stage-map, and decision-node recording operations. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/characters/*`, `/story-development/world-bible/*`, `/story-development/arcs/*`, and `/story-development/decisions/*` routes. Expected outcome: canonical story knowledge can be stored, related, and selected without manuscript generation or API wiring, using durable repository-backed state only. Arc comparison history and user decision history must both be reviewable through persisted objects. Keep the write scope limited to a new service module and a focused test file.
- [x] `Turing`: implement BE-07A by owning canonical persistence for `BeatPlan`, `SequencePlan`, `ChapterPlan`, `ScenePlan`, `PlanningDependency`, and `ChapterPacket` in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/planning/*` routes. Expected outcome: planning services can be built on durable canonical records instead of service-local state.
- [x] `Noether-2`: BE-07 remains blocked pending `BE-07A` and should not be implemented as a service-local workaround.
- [x] `Rawls`: retry BE-07 only after `BE-07A` lands, by owning the planning objects and chapter-packet service slice with bounded plan creation, reorder, and dependency-preservation operations. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/planning/*` routes. Expected outcome: plan objects persist as canonical records and can later be projected into UI cards without introducing a competing card persistence model. Prior blocked attempt correctly refused an in-memory workaround; retry now that canonical planning persistence exists. Keep the write scope limited to a new service module and a focused test file.
- [x] `Curie-2`: implement BE-08A by owning the drafting persistence scaffold for `DraftArtifact`, `ManuscriptDocument`, and `RevisionSuggestion` in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/drafting/*`, `/story-development/manuscript/*`, and `/story-development/revisions/*` routes. Expected outcome: drafting and manuscript state gain durable storage before service logic lands.
- [x] `Feynman`: implement BE-09B by owning the review and inspect persistence scaffold for `CheckerFinding`, `ReviewDecision`, and `InspectRunLink` in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/review/*` routes. Expected outcome: review and inspect linkage gain durable storage before service logic lands.
- [x] `Curie-3`: implement BE-08 only after `BE-08A` lands, by owning the draft artifact versus manuscript document separation service slice with bounded generate, revise, and promote operations. Keep the write scope limited to the new service module and a focused test file.
- [x] `Huygens`: implement BE-09 only after `BE-09B` lands, by owning the review decision and inspect-link service slice with bounded finding routing, decision recording, inspect linkage operations, and canonical routing back into planning or drafting. Keep the write scope limited to the new service module and a focused test file.
- [x] `Leibniz`: implement BE-09A by owning the story decision review surface slice with bounded listing, ordering, parent-path reconstruction, and affected-object linkage for `StoryDecisionNode`. Keep the write scope limited to a new service module and a focused test file.
- [x] `Gibbs`: implement BE-06 in `app/services/story_knowledge.py` and `tests/test_story_knowledge_service.py` only. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/characters/*`, `/story-development/world-bible/*`, `/story-development/arcs/*`, and `/story-development/decisions/*` routes. Expected outcome: arc comparison history and user decision history are both reviewable through persisted objects, with story-knowledge services using repository-backed state only.
- [x] `Bernoulli`: implement BE-09A in a bounded decision-review service module and focused test file only. Expected endpoints for this slice: none yet; backend foundation for later `/story-development/decisions/*` routes and related object detail screens. Expected outcome: a user can review decision-node history, affected-object links, and parent-path context without inferring direction changes from current state alone.
- [x] `Faraday-2`: implement BE-11A by owning story branch identity and branch-point schema or persistence support. Expected endpoints for this slice: none yet; foundation for later `/story-development/branches/*` routes. Expected outcome: branch identity and branch-point linkage become first-class structured backend objects without using Git as the canonical backend.
- [x] `Spinoza`: implement BE-11B only after BE-11A lands, by owning branch state references and active-branch persistence. Expected endpoints for this slice: none yet; foundation for later `/story-development/branches/*` routes. Expected outcome: the backend can persist branch-local state refs and the current active branch without branch comparison or merge behavior yet.
- [x] `Anaximander`: implement BE-11C only after BE-11A and BE-11B land, by owning `BranchComparisonRecord` schema or persistence support. Expected endpoints for this slice: none yet; foundation for later `/story-development/branches/comparisons*` routes. Expected outcome: branch comparisons become reviewable first-class backend records.
- [x] `Democritus`: implement BE-11D only after BE-11A and BE-11B land, by owning `BranchMergeDecision` schema or persistence support. Expected endpoints for this slice: none yet; foundation for later `/story-development/branch-merges*` routes. Expected outcome: merge decisions become durable backend records instead of implicit state changes.
- [x] `Goodall`: implement BE-11E only after BE-11A through BE-11D land, by owning the story-branching service slice with bounded create, list, compare, select-active, and merge-decision operations. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/branches/*` routes. Expected outcome: users can fork the storyline from a decision point and later review or merge branches without overwriting the active path.
- [x] `Dewey`: implement BE-10A by owning the first story-development API surface slice for stable non-branching contracts only. Keep the write scope limited to thin route wiring and focused route tests.
- [x] `Hopper-2`: implement BE-10B only after `BE-11E` lands, by owning the branching API surface slice with thin route wiring and focused route tests only.
- [x] `Volta`: update `docs/Narrative SRS v0.3.md` so the story-development sections describe an aspirational writing product, remove reconstruction-specific framing for those features, resolve implemented-versus-target-state contradictions, and align workflow-state terminology with the canonical enum set once defined.
- [x] `Kant`: update `docs/Frontend Design SRS v0.4.md` so object names, workflow states, and deterministic frontend task cards match the canonical contract and no longer bundle multiple screen families into one agent task.
- [x] `Archimedes`: update `docs/Orchestrator Deterministic Task Spec v0.1.md` so each story-development feature area includes callable operation shapes with expected inputs, outputs, side effects, and verification, and so the safe-assignment guidance matches the new narrower task cards.
- [x] `Hypatia`: update `docs/Story Development Product Spec v0.1.md` with the canonical editable-flow semantics, stage type versus stage instance versus stage status split, and explicit planning versus card terminology.
- [x] `Maxwell`: author a canonical docs appendix or companion contract section that lists approved object names, lifecycle enums, forbidden aliases, and cross-doc mappings for all story-development features.
- [x] `Kuhn`: create `docs/Inference Runtime Blueprint v0.1.md` that documents provider selection, environment variables, request/response contract, and runtime error taxonomy for `llama.cpp`, LM Studio, and `vLLM`.
- [x] `Beauvoir`: add deterministic inference-backend failure tests in `tests/test_inference_backend_failures.py` covering timeout, HTTP error, and invalid-JSON cases for the OpenAI-compatible adapter.
- [x] `Newton`: update `docs/Frontend Design SRS v0.4.md` so the UI explicitly supports runtime-provider visibility, model-source visibility, and inspect views for step and lineage endpoints.
- [x] `Planck`: update `.github/workflows/tests.yml` so CI includes `tests/test_inference_runtime.py` and document the exact CI command in `docs/Validation Notes v0.1.md`.
- [x] `Cicero`: create `docs/Step and Lineage API Projection Blueprint v0.1.md` defining deterministic response shapes for the planned step and lineage inspect endpoints.
- [x] `Maxwell`: create `docs/Runtime Telemetry Contract v0.1.md` defining required persisted telemetry fields, hash inputs, finish reasons, and error categories for provider-backed runs.
- [x] `Worker`: implement the first real `architect` call for job phase `P-100` in `app/services/local_executor.py`, including prompt building, inferencer call, persisted output, and tests.
- [x] `Beauvoir`: add deterministic API tests for the four step/lineage projection endpoints, including empty-state and 404 behavior.
- [x] `Cicero`: update `docs/Step and Lineage API Projection Blueprint v0.1.md` if needed so it exactly matches the endpoint response contract implemented in code.
- [x] `Newton`: update `docs/Frontend Design SRS v0.4.md` with explicit inspect-view expectations for the four public step/lineage endpoints once their contract is locked.
- [x] `Planck`: add CI coverage for the new projection-endpoint tests after they land.
- [x] `Kuhn`: review the repo for encoding or BOM issues that could break parsing, packaging, or test execution, and fix only concrete safe issues.
  Residual low-risk note: no UTF-8/BOM/control-character blockers were found in tracked source, docs, tests, or config files; a small set of files still mixes mostly-LF text with a single CRLF line ending, but nothing currently appears parser-breaking.
- [x] `Maxwell`: create `docs/Runtime Error Mapping Blueprint v0.1.md` that turns current inferencer failures into deterministic runtime error categories suitable for persistence.
- [x] `Cicero`: create `docs/Step and Lineage API Test Matrix v0.1.md` that enumerates required endpoint cases for happy path, empty state, 404, ordering, and future attempt filtering.
- [x] `Newton`: draft inspect-mode component inventory in `docs/Frontend Design SRS v0.4.md` for step timeline, lineage list, and provenance badges using the current minimal endpoint envelopes.
- [x] `Planck`: prepare the exact CI command expansion for projection-endpoint tests and report the final workflow command expected once the test file names are locked.
- [x] `Maxwell`: implement structured runtime error mapping in `app/inference/openai_compatible.py` and the runtime-backed `P-100` executor path so failures persist stable `error_category`, `error_code`, `finish_reason`, and `retryable` behavior.
- [x] `Beauvoir`: add deterministic tests for structured runtime error mapping and persisted failure behavior on the `P-100` architect path.
- [x] `Cicero`: implement runtime telemetry persistence for the real `P-100` step, including prompt/input/output hashes and provider token usage when present.
- [x] `Planck`: add deterministic tests for runtime telemetry fields persisted on `P-100` step records and artifact lineage.
- [x] `Newton`: implement the first runtime-backed checker role slice in `app/services/role_model_checker.py` for `architect`, preserving stub fallback for the other roles.
- [x] `Kuhn`: review and sync the backend docs after these runtime/error/telemetry changes land so the SRS and runtime blueprints remain reconstruction-grade.
- [x] `Hypatia`: make project artifact reads lineage-aware for generated runtime outputs so failed `P-200`/`P-300` runs do not return placeholder `sequence` or `chapter-1` files through existing project endpoints.
- [x] `Faraday`: update downstream runtime phases to ignore empty bootstrapped upstream artifacts and only record real dependency provenance in step input refs and source hashes.
- [x] `Copernicus`: implement canonical lineage supersession for rerun `sequence` and `chapter_1` artifacts and add deterministic regression tests for repeated successful runs.

## API Alignment Summary

**See**: `docs/Frontend API Alignment Issues.md` for complete analysis

### Real API Endpoints (Ready for Frontend)

| Endpoint | Method | Status | Frontend Tasks |
|----------|--------|--------|----------------|
| `/projects` | GET | ✅ Ready | FE-003 |
| `/projects/create` | POST | ✅ Ready | FE-003 |
| `/projects/{id}` | GET | ✅ Ready | FE-003 |
| `/projects/{id}/manifest` | GET | ✅ Ready | FE-003 |
| `/projects/{id}/sequence` | GET | ✅ Ready | FE-003 |
| `/projects/{id}/chapter-1` | GET | ✅ Ready | FE-003 |
| `/jobs/create` | POST | ✅ Ready | FE-014 |
| `/jobs/{id}/status` | GET | ✅ Ready | FE-015 |
| `/jobs/{id}/logs` | GET | ✅ Ready | FE-016 |
| `/jobs/{id}/steps` | GET | ✅ Ready | FE-019 |
| `/jobs/{id}/lineage` | GET | ✅ Ready | FE-020 |
| `/jobs/{id}/attempts` | GET | ✅ Ready | FE-015 |
| `/jobs/{id}/retry` | POST | ✅ Ready | FE-015 |
| `/models` | GET | ✅ Ready | FE-024 |
| `/role-model-checker/run` | POST | ✅ Ready | FE-024 |
| `/role-model-checker/start` | POST | ✅ Ready | FE-024 |
| `/role-model-checker/{id}/status` | GET | ✅ Ready | FE-024 |
| `/role-model-checker/{id}/steps` | GET | ✅ Ready | FE-024 |
| `/role-model-checker/{id}/lineage` | GET | ✅ Ready | FE-024 |
| `/role-model-checker/{id}/attempts` | GET | ✅ Ready | FE-024 |
| `/role-model-checker/{id}/retry` | POST | ✅ Ready | FE-024 |
| `/story-development/branches` | GET | ✅ Ready | FE-024A |
| `/story-development/branches` | POST | ✅ Ready | FE-024A |
| `/story-development/branches/active` | GET | ✅ Ready | FE-024A |
| `/story-development/branches/active` | POST | ✅ Ready | FE-024A |
| `/story-development/branches/comparisons` | POST | ✅ Ready | FE-024A |
| `/story-development/branches/comparisons` | GET | ✅ Ready | FE-024A |
| `/story-development/branches/comparisons/{id}` | GET | ✅ Ready | FE-024A |
| `/story-development/branches/merge-decisions` | POST | ✅ Ready | FE-024A |
| `/story-development/branches/merge-decisions` | GET | ✅ Ready | FE-024A |
| `/story-development/branches/{id}` | GET | ✅ Ready | FE-024A |
| `/story-development/branches/{id}/state-refs` | GET | ✅ Ready | FE-024A |
| `/story-development/decisions` | GET | ✅ Ready | FE-024B |
| `/story-development/decisions/{id}` | GET | ✅ Ready | FE-024B |
| `/story-development/decisions/{id}/path` | GET | ✅ Ready | FE-024B |
| `/story-development/planning/sequence-plans` | GET | ✅ Ready | FE-007 |
| `/story-development/planning/sequence-plans/{id}` | GET | ✅ Ready | FE-007 |
| `/story-development/planning/chapter-plans` | GET | ✅ Ready | FE-007 |
| `/story-development/planning/chapter-plans/{id}` | GET | ✅ Ready | FE-007 |
| `/story-development/planning/scene-plans` | GET | ✅ Ready | FE-007 |
| `/story-development/planning/scene-plans/{id}` | GET | ✅ Ready | FE-007 |
| `/story-development/planning/dependencies` | GET | ✅ Ready | FE-007 |
| `/story-development/planning/dependencies/{id}` | GET | ✅ Ready | FE-007 |
| `/story-development/planning/chapter-packets` | GET | ✅ Ready | FE-009 |
| `/story-development/planning/chapter-packets/{id}` | GET | ✅ Ready | FE-009 |
| `/story-development/drafting/draft-artifacts` | GET | ✅ Ready | FE-013 |
| `/story-development/drafting/draft-artifacts/{id}` | GET | ✅ Ready | FE-013 |
| `/story-development/drafting/manuscript-documents` | GET | ✅ Ready | FE-011 |
| `/story-development/drafting/manuscript-documents/{id}` | GET | ✅ Ready | FE-011 |
| `/story-development/drafting/revision-suggestions` | GET | ✅ Ready | FE-025 |
| `/story-development/drafting/revision-suggestions/{id}` | GET | ✅ Ready | FE-025 |
| `/story-development/review/findings` | GET | ✅ Ready | FE-022 |
| `/story-development/review/findings/{id}` | GET | ✅ Ready | FE-022 |
| `/story-development/review/decisions` | GET | ✅ Ready | FE-023 |
| `/story-development/review/decisions/{id}` | GET | ✅ Ready | FE-023 |
| `/story-development/review/inspect-links` | GET | ✅ Ready | FE-024C |
| `/story-development/review/inspect-links/{id}` | GET | ✅ Ready | FE-024C |

### Mock Service Endpoints (Backend Not Yet Available)

| Feature | Missing Endpoint | Frontend Tasks | Mock Required |
|---------|------------------|----------------|---------------|
| Manuscript creation | `POST /story-development/drafting/manuscript-documents` | FE-013 | ✅ |
| Review decisions | `POST /story-development/review/decisions` | FE-023 | ✅ |
| Flow editor | All flow endpoints | FE-006 | ✅ |
| Revision suggestions | `POST /story-development/drafting/revision-suggestions` | FE-025, FE-028 | ✅ |
| Brainstorm | All brainstorm endpoints | FE-029 | ✅ |
| Foundation | All foundation endpoints | FE-030 | ✅ |
| Characters | All character endpoints | FE-031 | ✅ |
| World Bible | All bible endpoints | FE-032 | ✅ |
| Planning writes | `POST /story-development/planning/chapter-plans`, `POST /story-development/planning/scene-plans`, `POST /story-development/planning/chapter-packets` | FE-007, FE-009 | ✅ |
| Sequence plans writes | `POST /story-development/planning/sequence-plans` | FE-007 | ✅ |

### Schema Corrections Applied

1. **ProjectSummaryResponse**: Added genre, tone_profile, story_structure fields
2. **JobCreateRequest**: Removed model_id (backend configures models, not per-job)
3. **ChapterPlan/ScenePlan status**: String field, not enum (map: "draft"→DRAFT, etc.)
4. **CheckerFinding severity**: String field, not enum (map: "low"→LOW, etc.)
5. **ReviewDecision decision_action**: String field, not enum (values: "accept", "reject", "defer", "escalate", "refine")

### Mock Service Contract

All mock services must:
- Delay: 2000ms on all operations
- Storage: In-memory per project (clears on reload)
- Validation: Same as backend schema
- Errors: Return appropriate codes (400, 404, 500)
- Banner: UI shows "Mock Mode" banner when active
- Feature flag: `VITE_USE_MOCKS=true` enables, `false` shows "Coming soon"

### Environment Variables

```bash
# .env.local (frontend)
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCKS=true
VITE_THEME=light
VITE_STAGE_THEME=writing
```

### Next Steps

1. ✅ Update TODO.md with corrected API schemas
2. ✅ Add FE-001A theming task
3. ✅ Add error boundary, skeleton, toast tasks (FE-004A, FE-004B, FE-004C)
4. ✅ Document mock service contracts
5. ✅ Create `docs/Frontend API Alignment Issues.md`
6. ✅ Implement backend endpoints required for the current frontend surface
7. ✅ Replace the merge-blocking mock and routing gaps identified during merge review
