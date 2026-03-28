[
  {
    "task_id": "8c6f6c4a-9d7c-4e6d-9d0c-4bd0da6b4fd9",
    "purpose": "Expand the existing `/health/metrics` payload so REL-05 exposes job and checker operational counters in the same router that already serves liveness and readiness. The implementation should add stable keys for job terminal status counts, checker terminal status counts, and inference circuit-breaker state snapshots without changing `/health/` or `/health/ready` contracts.",
    "responsible_file": "F:/Dev/Narrative-Engine/app/api/health.py",
    "knowledge_base": [
      "router = APIRouter(prefix='/health', tags=['health'])",
      "get_metrics()",
      "get_all_circuit_states()",
      "CircuitState",
      "settings.projects_dir"
    ],
    "references_and_schema": {
      "input_data_schema": "HTTP GET /health/metrics with no request body.",
      "output_data_schema": "JSON object containing `timestamp`, `circuit_breakers`, `jobs`, and `role_model_checker` sections. `jobs` and `role_model_checker` should each expose status buckets keyed by existing terminal/non-terminal status names already used by JobStatusResponse and checker status responses.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/api/health.py",
        "F:/Dev/Narrative-Engine/app/schemas/jobs.py",
        "F:/Dev/Narrative-Engine/app/services/circuit_breaker.py"
      ]
    },
    "utilized_features": [
      "FastAPI APIRouter",
      "existing `get_all_circuit_states()` helper",
      "existing health router mounted in `app/main.py`"
    ],
    "expected_outcomes": [
      "`GET /health/metrics` returns HTTP 200 with deterministic top-level keys `timestamp`, `circuit_breakers`, `jobs`, and `role_model_checker`.",
      "The response keeps the existing circuit-breaker fields and adds stable job/checker status buckets instead of ad-hoc counters."
    ]
  },
  {
    "task_id": "7c2aa1e6-67cc-4c6a-aed8-fde249c882d1",
    "purpose": "Codify the REL-05 metrics contract in API tests so the new `/health/metrics` shape cannot silently regress. The test should verify the endpoint stays unauthenticated and returns the expanded job/checker sections alongside circuit breaker data.",
    "responsible_file": "F:/Dev/Narrative-Engine/tests/test_health_api.py",
    "knowledge_base": [
      "FastAPI TestClient usage in existing API tests",
      "health_check/readiness_check behavior",
      "JSON assertions against response payloads"
    ],
    "references_and_schema": {
      "input_data_schema": "GET requests against `/health/`, `/health/ready`, and `/health/metrics`.",
      "output_data_schema": "Assertions for `/health/metrics` should require `timestamp`, `circuit_breakers`, `jobs`, and `role_model_checker` keys and should not require auth headers.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/api/health.py",
        "F:/Dev/Narrative-Engine/tests/test_smoke.py"
      ]
    },
    "utilized_features": [
      "pytest",
      "fastapi.testclient.TestClient"
    ],
    "expected_outcomes": [
      "A failing or incomplete metrics payload breaks this test file.",
      "The test suite proves `/health/metrics` remains reachable without `X-API-Key` or bearer credentials."
    ]
  },
  {
    "task_id": "e8ce3a45-f5f8-4327-a560-bd8e09baea42",
    "purpose": "Add phase-specific payload validation to job creation so REL-08 rejects malformed `payload` objects before they enter JobManager. The validator should enforce a required `project_id` for `P-100`, `P-200`, `P-300`, and `P-400`, while preserving the existing 5 MB payload-size limit.",
    "responsible_file": "F:/Dev/Narrative-Engine/app/schemas/jobs.py",
    "knowledge_base": [
      "JobCreateRequest",
      "JobPhase",
      "MAX_PAYLOAD_SIZE",
      "Pydantic `field_validator` patterns already used for `payload`"
    ],
    "references_and_schema": {
      "input_data_schema": "JobCreateRequest = { `phase`: JobPhase, `payload`: dict[str, Any], `idempotency_key`?: str | null }.",
      "output_data_schema": "Validation error when `phase` is one of `P-100|P-200|P-300|P-400` and `payload.project_id` is missing, blank, or not a string. Valid requests still produce JobCreateRequest instances unchanged.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/schemas/jobs.py",
        "F:/Dev/Narrative-Engine/tests/test_failure_modes.py",
        "F:/Dev/Narrative-Engine/tests/test_local_executor_architect_runtime.py"
      ]
    },
    "utilized_features": [
      "Pydantic v2 `field_validator`",
      "existing JobPhase enum",
      "existing payload-size validation logic"
    ],
    "expected_outcomes": [
      "`JobCreateRequest.model_validate({phase:'P-100', payload:{}})` raises a validation error mentioning `project_id`.",
      "Payloads for supported phases continue to pass when `payload.project_id` is a non-empty string."
    ]
  },
  {
    "task_id": "17f4f0df-46f3-489b-b531-bd7b3b58559e",
    "purpose": "Create regression tests for REL-08 so phase-specific payload validation is enforced at the schema boundary and at the HTTP layer. The tests should cover both direct `JobCreateRequest` validation and rejected `/jobs/create` requests.",
    "responsible_file": "F:/Dev/Narrative-Engine/tests/test_job_payload_validation.py",
    "knowledge_base": [
      "JobCreateRequest",
      "existing TestClient request patterns for `/jobs/create`",
      "HTTP 422 validation failure semantics"
    ],
    "references_and_schema": {
      "input_data_schema": "Schema validation inputs and POST `/jobs/create` JSON bodies for phases `P-100`, `P-200`, `P-300`, and `P-400`.",
      "output_data_schema": "Tests should assert validation failure on missing/blank/non-string `payload.project_id` and success on minimally valid payloads.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/schemas/jobs.py",
        "F:/Dev/Narrative-Engine/app/api/jobs.py"
      ]
    },
    "utilized_features": [
      "pytest",
      "fastapi.testclient.TestClient",
      "Pydantic validation assertions"
    ],
    "expected_outcomes": [
      "This file fails if `/jobs/create` accepts a phase payload without a valid `project_id`.",
      "This file passes when minimally valid phase payloads still return 202 or 200 accepted responses."
    ]
  },
  {
    "task_id": "d8b16d95-17d7-4c6b-b4a6-61e3db7beec6",
    "purpose": "Harden startup filesystem checks for REL-09 by rejecting unsafe writable locations such as world-writable project roots and by surfacing ownership/permission problems through ConfigValidationError instead of best-effort writes alone.",
    "responsible_file": "F:/Dev/Narrative-Engine/app/services/config_validator.py",
    "knowledge_base": [
      "ConfigValidator.validate_all()",
      "_validate_directories()",
      "ConfigValidationError",
      "settings.projects_dir and database path checks"
    ],
    "references_and_schema": {
      "input_data_schema": "Runtime environment variables controlling `PROJECTS_DIR` and database path resolution.",
      "output_data_schema": "Validation report entries include failed/error status for unsafe directories, with `component` = `directories` and a descriptive permission/ownership message.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/services/config_validator.py",
        "F:/Dev/Narrative-Engine/tests/test_config_validator.py"
      ]
    },
    "utilized_features": [
      "existing ConfigValidator validation pipeline",
      "Path and os.stat permission checks",
      "existing ConfigValidationError reporting"
    ],
    "expected_outcomes": [
      "`validate_all()` returns false or raises ConfigValidationError when the configured projects directory is world-writable or otherwise unsafe.",
      "Writable-but-safe directories continue to pass without changing existing startup validation behavior."
    ]
  },
  {
    "task_id": "b8ebd580-32d2-476d-9684-47fc049d71c6",
    "purpose": "Add deterministic REL-09 test coverage for directory permission validation so unsafe directory modes do not slip through startup checks. The tests should cover both safe writable directories and explicitly unsafe permission patterns.",
    "responsible_file": "F:/Dev/Narrative-Engine/tests/test_config_validator.py",
    "knowledge_base": [
      "ConfigValidator",
      "monkeypatch/temp directory patterns already used in this test file",
      "ConfigValidationError"
    ],
    "references_and_schema": {
      "input_data_schema": "Temporary directories patched into `PROJECTS_DIR` or equivalent environment paths.",
      "output_data_schema": "Assertions on validation success/failure and `directories` component messages in `validation_results`.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/services/config_validator.py"
      ]
    },
    "utilized_features": [
      "pytest tmp_path",
      "monkeypatch",
      "existing ConfigValidator report API"
    ],
    "expected_outcomes": [
      "The test file fails if unsafe directory permissions are accepted as valid.",
      "The test file passes when safe directories still validate normally."
    ]
  },
  {
    "task_id": "4510ab68-48ab-42ba-a6d8-b45979eb3e5f",
    "purpose": "Add an API-key fingerprint helper for REL-10 so audit records can log a stable, non-secret identifier instead of raw credentials. The implementation should derive a deterministic hash or prefix-safe fingerprint from existing APIKey data without exposing full secrets.",
    "responsible_file": "F:/Dev/Narrative-Engine/app/services/authentication.py",
    "knowledge_base": [
      "APIKey dataclass/model fields",
      "APIKeyStore.validate_key()",
      "existing hashing patterns in the authentication service"
    ],
    "references_and_schema": {
      "input_data_schema": "Validated APIKey metadata and/or the raw API key string passed through authentication flows.",
      "output_data_schema": "A deterministic audit-safe string such as `sha256:<hex>` or equivalent fingerprint that never contains the full API key secret.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/services/authentication.py",
        "F:/Dev/Narrative-Engine/app/middleware/authentication.py"
      ]
    },
    "utilized_features": [
      "existing hashlib usage in the repo",
      "existing APIKey validation flow"
    ],
    "expected_outcomes": [
      "A helper callable from request middleware returns the same fingerprint for the same API key and never returns the full secret.",
      "Revoked or invalid keys still do not expose secret material through the helper."
    ]
  },
  {
    "task_id": "2f1c1d8b-f3b8-491f-92fb-91d4fca9919f",
    "purpose": "Implement REL-10 request audit logging at the application boundary so versioned API requests record timestamp, authenticated API-key fingerprint, HTTP method, path, and final response code in one structured JSONL stream.",
    "responsible_file": "F:/Dev/Narrative-Engine/app/main.py",
    "knowledge_base": [
      "build_app()",
      "existing `versioned_api_key_gate` middleware",
      "settings.structured_log_filename",
      "Request and JSONResponse middleware patterns in FastAPI"
    ],
    "references_and_schema": {
      "input_data_schema": "Incoming HTTP requests under `/v1/*`, request headers including `X-API-Key`, and response status codes.",
      "output_data_schema": "One JSONL audit entry per request with keys `timestamp`, `method`, `path`, `status_code`, `api_key_hash` (or null), and request target identifiers when available from path params or JSON body.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/main.py",
        "F:/Dev/Narrative-Engine/app/services/authentication.py",
        "F:/Dev/Narrative-Engine/app/settings.py"
      ]
    },
    "utilized_features": [
      "FastAPI `@app.middleware('http')`",
      "existing settings paths",
      "existing JSONResponse path for auth failures"
    ],
    "expected_outcomes": [
      "Each `/v1` request appends exactly one audit record to the configured structured log file.",
      "The audit record includes method, path, final status code, and a non-secret API-key fingerprint when authentication data is present."
    ]
  },
  {
    "task_id": "1a483f7c-54d8-4828-a497-a8f6d4b4c59c",
    "purpose": "Lock REL-10 behavior with tests that verify structured audit records are written for versioned API requests and do not leak raw API keys. The tests should cover both authenticated and unauthenticated/error responses.",
    "responsible_file": "F:/Dev/Narrative-Engine/tests/test_audit_logging.py",
    "knowledge_base": [
      "FastAPI TestClient",
      "structured log file assertions",
      "versioned_api_key_gate behavior in app/main.py"
    ],
    "references_and_schema": {
      "input_data_schema": "Requests to `/v1/jobs/create`, `/v1/models`, or other mounted versioned routes with and without auth headers.",
      "output_data_schema": "Parsed JSONL entries must contain `timestamp`, `method`, `path`, `status_code`, and `api_key_hash`, and must not contain the submitted API key value.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/main.py",
        "F:/Dev/Narrative-Engine/app/services/authentication.py"
      ]
    },
    "utilized_features": [
      "pytest",
      "tmp_path",
      "JSON parsing of log lines"
    ],
    "expected_outcomes": [
      "The file fails if audit lines are missing for `/v1` requests.",
      "The file fails if raw API key values appear in the audit payload."
    ]
  },
  {
    "task_id": "7d536949-3f76-4d29-88b3-580b8e53c244",
    "purpose": "Extend job persistence for orchestration-centric attempt history so later projection endpoints can expose richer attempt metadata without overloading step rows. This task should add repository-level storage/read helpers rather than UI or route logic.",
    "responsible_file": "F:/Dev/Narrative-Engine/app/persistence/jobs.py",
    "knowledge_base": [
      "SQLite schema setup in jobs persistence",
      "attempt history read/write helpers",
      "lineage and step-record persistence patterns",
      "stable_hash_payload usage in related tests"
    ],
    "references_and_schema": {
      "input_data_schema": "Accepted job/checker attempts, retry transitions, and per-attempt metadata already persisted through JobManager and RoleModelCheckManager.",
      "output_data_schema": "Repository helpers that can read/write richer attempt rows keyed by run/job id plus `attempt_number`, preserving existing projection semantics.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/persistence/jobs.py",
        "F:/Dev/Narrative-Engine/tests/test_attempt_lineage.py",
        "F:/Dev/Narrative-Engine/tests/test_attempt_history_endpoints.py"
      ]
    },
    "utilized_features": [
      "existing SQLite migration/bootstrap pattern",
      "existing attempt history projection codepaths"
    ],
    "expected_outcomes": [
      "Repository APIs can persist and retrieve per-attempt metadata beyond status timestamps alone.",
      "Existing callers continue to read current attempt history without schema breakage."
    ]
  },
  {
    "task_id": "c1df5ef9-c2a7-47f1-9b74-d8d2b3f0daf5",
    "purpose": "Add regression tests for richer orchestration attempt persistence so the new repository contract stays aligned with attempt-history projections and retry lineage.",
    "responsible_file": "F:/Dev/Narrative-Engine/tests/test_attempt_lineage.py",
    "knowledge_base": [
      "attempt history endpoint expectations",
      "retry lineage assertions",
      "job/checker attempt projection semantics"
    ],
    "references_and_schema": {
      "input_data_schema": "Retry and accepted-start flows already exercised by attempt-history tests.",
      "output_data_schema": "Assertions should require the new per-attempt metadata to remain stable across retries and lineage reads.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/persistence/jobs.py",
        "F:/Dev/Narrative-Engine/tests/test_attempt_history_endpoints.py"
      ]
    },
    "utilized_features": [
      "pytest",
      "existing attempt-history fixtures",
      "job/checker manager APIs"
    ],
    "expected_outcomes": [
      "The file fails if new attempt metadata is not persisted or projected consistently.",
      "Retry-lineage assertions remain green after the persistence extension lands."
    ]
  },
  {
    "task_id": "a99eec89-ee4d-43a9-bd08-27f3601a6a1f",
    "purpose": "Move project artifact reads for chapter-packet, sequence, and future story-bible style outputs toward lineage-aware registration instead of flat file assumptions. This task should update the project artifact service layer so reads prefer canonical lineage-backed artifacts when they exist.",
    "responsible_file": "F:/Dev/Narrative-Engine/app/services/projects.py",
    "knowledge_base": [
      "ProjectService.read_artifact()",
      "artifact key mapping for `manifest`, `sequence`, and `chapter-1`",
      "existing lineage-aware runtime artifact behavior from local executor fixes"
    ],
    "references_and_schema": {
      "input_data_schema": "Project artifact lookup by `project_id` and artifact key such as `sequence` or `chapter-1`.",
      "output_data_schema": "Artifact reads return canonical lineage-backed content when present and fall back to file-based project artifacts only when no lineage-backed canonical artifact exists.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/services/projects.py",
        "F:/Dev/Narrative-Engine/tests/test_projection_endpoints.py",
        "F:/Dev/Narrative-Engine/tests/test_projection_runtime_failure_modes.py"
      ]
    },
    "utilized_features": [
      "existing ProjectService artifact IO",
      "existing lineage persistence already used by runtime-generated artifacts"
    ],
    "expected_outcomes": [
      "`read_artifact(project_id, 'sequence')` prefers canonical lineage content when available.",
      "Existing manifest and fallback file reads continue to work when lineage data is absent."
    ]
  },
  {
    "task_id": "d93e7300-7196-4779-bf7d-8427c61f0f7a",
    "purpose": "Add persistence helpers for storyboard-card style planning state so scene/chapter board data can be stored canonically once the planning workspace stops being mock-backed. This task should stay in the story-development repository layer only.",
    "responsible_file": "F:/Dev/Narrative-Engine/app/persistence/story_development.py",
    "knowledge_base": [
      "dataclass record patterns in StoryDevelopmentRepository",
      "existing `create_*`, `upsert_*`, and `list_*` methods for planning/foundation/drafting tables",
      "SQLite JSON serialization helpers `_json_list`, `_json_objects`, `_parse_json_objects`"
    ],
    "references_and_schema": {
      "input_data_schema": "Storyboard-card-like objects should follow the same repository patterns used for sequence, chapter, and scene plans: project-scoped identifiers, position/order fields, content, and timestamp metadata.",
      "output_data_schema": "Repository dataclasses plus CRUD/reorder helpers that store storyboard cards in SQLite and return typed records, without adding API routes yet.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/persistence/story_development.py",
        "F:/Dev/Narrative-Engine/app/services/planning.py",
        "F:/Dev/Narrative-Engine/frontend/src/hooks/useStoryboard.ts"
      ]
    },
    "utilized_features": [
      "existing StoryDevelopmentRepository schema bootstrap",
      "existing JSON column helpers",
      "existing plan position/reorder logic patterns"
    ],
    "expected_outcomes": [
      "The repository exposes dedicated storyboard-card persistence helpers instead of relying on ad-hoc planning JSON blobs.",
      "No API route or frontend dependency is introduced in this file."
    ]
  },
  {
    "task_id": "b594421a-b748-4f03-8b2c-b620ccdc8e36",
    "purpose": "Broaden orchestration/runtime integration coverage by asserting end-to-end P-100 through P-400 persistence, supersession, and projection behavior in one deterministic runtime test module.",
    "responsible_file": "F:/Dev/Narrative-Engine/tests/test_local_executor_compiler_runtime.py",
    "knowledge_base": [
      "_run_phase()",
      "stable_hash_payload",
      "existing P-400 supersession assertions",
      "project_service.read_artifact()"
    ],
    "references_and_schema": {
      "input_data_schema": "Runtime job creation payloads shaped as `{ phase, payload: { project_id, ... } }`.",
      "output_data_schema": "Additional assertions should verify orchestration attempt history, canonical artifact supersession, and projection reads remain consistent across repeated successful runs.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/tests/test_local_executor_compiler_runtime.py",
        "F:/Dev/Narrative-Engine/app/services/local_executor.py"
      ]
    },
    "utilized_features": [
      "pytest",
      "existing runtime fixtures",
      "existing local executor integration helpers"
    ],
    "expected_outcomes": [
      "The file fails if orchestration/runtime regressions reintroduce stale canonical artifacts or broken attempt metadata.",
      "Successful reruns preserve prior history while promoting only the latest canonical artifacts."
    ]
  },
  {
    "task_id": "29c2d7d8-2a23-4f33-a904-bb7802f5cb37",
    "purpose": "Add contract tests for manuscript-aid and diff-style payloads in a way that is explicit about current backend availability. This task should cover the currently shipped `GET /story-development/drafting/revision-suggestions` contract and leave skipped/xfail placeholders for write-side or diff routes until the backend surface exists.",
    "responsible_file": "F:/Dev/Narrative-Engine/tests/test_story_development_api.py",
    "knowledge_base": [
      "story-development API TestClient patterns",
      "RevisionSuggestion list/detail routes",
      "pytest skip/xfail markers"
    ],
    "references_and_schema": {
      "input_data_schema": "GET `/story-development/drafting/revision-suggestions?project_id=...` and GET detail routes for existing revision suggestion records.",
      "output_data_schema": "Tests assert the current `RevisionSuggestion` read contract and explicitly mark write/diff coverage as pending until matching routes are added.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/api/story_development.py",
        "F:/Dev/Narrative-Engine/app/schemas/story_development.py"
      ]
    },
    "utilized_features": [
      "pytest",
      "fastapi.testclient.TestClient",
      "existing story-development fixtures"
    ],
    "expected_outcomes": [
      "Existing revision-suggestion GET routes are covered by contract tests.",
      "Pending manuscript-aid write/diff coverage is represented explicitly instead of silently omitted."
    ]
  },
  {
    "task_id": "2eb9f6c1-9938-4d0d-b62e-a8222044fbe3",
    "purpose": "Stabilize the branch service layer around the real backend endpoints so all branch UI work shares one typed contract. The file should rely on existing `/v1/story-development/branches*` routes and preserve `project_id`, `branch_id`, `comparison_id`, and merge-decision payload names exactly as defined by the backend.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/services/branches.ts",
    "knowledge_base": [
      "getBranches/createBranch/getActiveBranch/setActiveBranch",
      "createBranchComparison/getComparisons/getComparison",
      "createMergeDecision/getMergeDecisions/getBranchStateRefs"
    ],
    "references_and_schema": {
      "input_data_schema": "Branch service request bodies use `{ project_id, name, description?, parent_branch_id? }`, `{ project_id, branch_a_id, branch_b_id }`, and `{ project_id, source_branch_id, target_branch_id, decision, rationale? }`.",
      "output_data_schema": "All service functions resolve backend list envelopes shaped as `{ project_id, items, meta }` or single objects shaped as `StoryBranch`, `BranchComparisonRecord`, `BranchMergeDecision`, and `BranchStateRef`.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/services/branches.ts",
        "F:/Dev/Narrative-Engine/frontend/src/types/branches.ts",
        "F:/Dev/Narrative-Engine/app/api/story_development.py"
      ]
    },
    "utilized_features": [
      "existing fetch-based service pattern",
      "existing branch route family under `/v1/story-development/branches`"
    ],
    "expected_outcomes": [
      "Branch service methods use only the real backend endpoints listed in the current API appendix.",
      "List functions always return `data.items` and single-object functions always return the direct backend object."
    ]
  },
  {
    "task_id": "45673ca6-619c-4841-b836-2e245625548c",
    "purpose": "Finish the branches list UI so FE-024A supports active-branch changes and a real empty-state action path instead of a dead button. The component should invalidate branch queries after mutations and expose a deterministic create-branch workflow entry point.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/branches/BranchList.tsx",
    "knowledge_base": [
      "useQuery/useMutation/useQueryClient",
      "BranchCard props",
      "useToastStore.addToast",
      "query keys `['branches', projectId]` and `['active-branch', projectId]`"
    ],
    "references_and_schema": {
      "input_data_schema": "Component prop `projectId: string`; service responses from `getBranches()` and `setActiveBranch()`.",
      "output_data_schema": "Rendered branch list with loading state, empty state, active-branch selection, and compare trigger using live service data.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/components/branches/BranchList.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/components/branches/BranchCard.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/services/branches.ts"
      ]
    },
    "utilized_features": [
      "@tanstack/react-query",
      "toast store",
      "existing BranchCard component"
    ],
    "expected_outcomes": [
      "Changing the active branch invalidates both `branches` and `active-branch` queries.",
      "The empty state no longer presents a button with no mutation or callback path behind it."
    ]
  },
  {
    "task_id": "c8129060-fa4e-43cb-a026-ee6f3dd86302",
    "purpose": "Replace the comparison placeholder behavior with a real FE-024A comparison view that consumes `BranchComparisonRecord.differences` from the backend. The component should fetch or accept a created comparison record and render the server-provided differences list deterministically.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/branches/BranchComparison.tsx",
    "knowledge_base": [
      "selectedA/selectedB local state",
      "comparison local state",
      "branch comparison service methods",
      "BranchComparisonRecord type"
    ],
    "references_and_schema": {
      "input_data_schema": "Comparison request body `{ project_id, branch_a_id, branch_b_id }`; backend comparison response `BranchComparisonRecord`.",
      "output_data_schema": "Rendered diff list uses `comparison.differences` from the API instead of any fabricated client-side placeholder array.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/components/branches/BranchComparison.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/services/branches.ts",
        "F:/Dev/Narrative-Engine/frontend/src/types/branches.ts"
      ]
    },
    "utilized_features": [
      "existing branch comparison service client",
      "React local state",
      "toast or error rendering already used elsewhere in the frontend"
    ],
    "expected_outcomes": [
      "Clicking compare renders backend-provided comparison results.",
      "The file contains no hard-coded sample differences array."
    ]
  },
  {
    "task_id": "cfcfe801-b1b2-4d77-ae18-125401eb2ac1",
    "purpose": "Complete merge-decision submission for FE-024A so branch merge actions call the real backend and surface existing decision history. The form should preserve `source_branch_id`, `target_branch_id`, `decision`, and `rationale` field names exactly.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/branches/MergeDecisionForm.tsx",
    "knowledge_base": [
      "BranchMergeDecision type",
      "createMergeDecision/getMergeDecisions service methods",
      "existing form state and submit handlers"
    ],
    "references_and_schema": {
      "input_data_schema": "Submit payload `{ project_id, source_branch_id, target_branch_id, decision: 'merge'|'reject'|'defer', rationale? }`.",
      "output_data_schema": "On success the form reflects the created `BranchMergeDecision` and refreshes existing decision history for the relevant branches/project.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/components/branches/MergeDecisionForm.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/services/branches.ts",
        "F:/Dev/Narrative-Engine/frontend/src/types/branches.ts"
      ]
    },
    "utilized_features": [
      "React form state",
      "existing branch services",
      "React Query or local refresh logic already used in branch components"
    ],
    "expected_outcomes": [
      "Submitting the form creates a real merge decision through the backend service.",
      "The decision history shown by the component is derived from live backend data."
    ]
  },
  {
    "task_id": "4d7dd8e8-7d58-4911-9c1e-b0ef3e66e8d4",
    "purpose": "Stabilize the decision service contract for FE-024B so the frontend preserves subject filters and full path context instead of collapsing server data into a lossy placeholder structure.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/services/decisions.ts",
    "knowledge_base": [
      "getDecisions()",
      "getDecision()",
      "getDecisionPath()",
      "StoryDecisionNode and StoryDecisionPath types"
    ],
    "references_and_schema": {
      "input_data_schema": "GET `/v1/story-development/decisions?project_id=...&subject_type=...&subject_id=...`, GET detail, and GET `/v1/story-development/decisions/{node_id}/path`.",
      "output_data_schema": "Service functions should return typed `StoryDecisionNode[]`, `StoryDecisionNode`, and `StoryDecisionPath` preserving `project_id`, node ids, and ancestor ordering from `parent_path`.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/services/decisions.ts",
        "F:/Dev/Narrative-Engine/frontend/src/types/decisions.ts",
        "F:/Dev/Narrative-Engine/app/api/story_development.py"
      ]
    },
    "utilized_features": [
      "shared Axios client in `frontend/src/lib/api.ts`",
      "existing decision backend endpoints"
    ],
    "expected_outcomes": [
      "Decision-path service results preserve the ancestor path and current node in a typed structure that the UI can render directly.",
      "Optional subject filters can be passed through without inventing new query parameters."
    ]
  },
  {
    "task_id": "0a74f666-5638-4413-b55e-d11b75d65431",
    "purpose": "Keep the FE-024C inspect-links service aligned with the shipped review API contract so list reads continue to use `project_id`, `object_kind`, `object_id`, and `run_id` exactly as the backend expects. This task should preserve the existing detail-read contract and avoid reintroducing the removed `finding_id` query shape.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/services/inspectLinks.ts",
    "knowledge_base": [
      "getInspectLinks()",
      "getInspectLink()",
      "shared Axios client usage via `api.get()`",
      "InspectRunLink type"
    ],
    "references_and_schema": {
      "input_data_schema": "Optional query params `project_id`, `object_kind`, `object_id`, and `run_id`; path param `link_id` for detail reads.",
      "output_data_schema": "Resolved `InspectRunLink[]` list envelopes and single `InspectRunLink` detail objects.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/services/inspectLinks.ts",
        "F:/Dev/Narrative-Engine/frontend/src/types/inspectLinks.ts",
        "F:/Dev/Narrative-Engine/app/api/story_development.py"
      ]
    },
    "utilized_features": [
      "shared Axios client in `frontend/src/lib/api.ts`",
      "existing inspect-links backend endpoints"
    ],
    "expected_outcomes": [
      "List fetches preserve only the supported query params `project_id`, `object_kind`, `object_id`, and `run_id`.",
      "Detail fetches return the backend object unchanged."
    ]
  },
  {
    "task_id": "d0d3db03-34d1-429d-a420-f198de9cd1c1",
    "purpose": "Finish the remaining FE-024C list behavior by keeping filter inputs and navigation wiring aligned with the shipped inspect-links service contract. The component should filter by `object_kind`, `object_id`, `run_id`, and `run_kind`, and it should only trigger inspect/review navigation patterns that the current route-driven workspace can render.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/inspectLinks/InspectRunLinksList.tsx",
    "knowledge_base": [
      "filterByObjectKind/filterByObjectId/filterByRunId/filterByKind local state",
      "getInspectLinks() query",
      "InspectRunLinkCard rendering",
      "existing workspace/inspect navigation patterns in the app"
    ],
    "references_and_schema": {
      "input_data_schema": "Component prop `projectId?: string` plus filters `object_kind`, `object_id`, `run_id`, and `run_kind`.",
      "output_data_schema": "Rendered list that filters live inspect-link records and triggers only real inspect/review navigation or state updates when a card is selected.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/components/inspectLinks/InspectRunLinksList.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/components/inspectLinks/InspectRunLinkCard.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/components/inspect/InspectMode.tsx"
      ]
    },
    "utilized_features": [
      "@tanstack/react-query",
      "existing route-driven inspect/review UI state patterns",
      "existing InspectRunLinkCard component"
    ],
    "expected_outcomes": [
      "The list supports filter-by-object-kind, filter-by-object-id, filter-by-run-id, and filter-by-kind.",
      "Selecting a link triggers a real inspect/review context change instead of rendering static text only."
    ]
  },
  {
    "task_id": "91f13356-5310-4993-b312-ff2ba97b3b49",
    "purpose": "Create the FE-025 mock manuscript-aids service contract so the writing workspace can request suggestion-like responses deterministically while the backend write endpoint is still absent. The mock must match the existing `RevisionSuggestion` read schema shape and respect the `VITE_USE_MOCKS` flag.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/services/mocks/manuscriptAidsMock.ts",
    "knowledge_base": [
      "mock-service patterns in `draftingMock.ts`, `reviewMock.ts`, and `checkerMock.ts`",
      "RevisionSuggestion type",
      "existing `VITE_USE_MOCKS` gating used in drafting services"
    ],
    "references_and_schema": {
      "input_data_schema": "Aid request payload should include at minimum `project_id`, `target_kind`, `target_id`, `anchor_text`, and requested action label such as `rewrite` or `summarize`.",
      "output_data_schema": "Promise resolving after a fixed delay to a `RevisionSuggestion`-shaped object with `suggestion_id`, `project_id`, `target_kind`, `target_id`, `anchor_text`, `proposed_revision`, `state`, and `created_at`.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/services/mocks/draftingMock.ts",
        "F:/Dev/Narrative-Engine/frontend/src/services/mocks/reviewMock.ts",
        "F:/Dev/Narrative-Engine/frontend/src/types/drafting.ts"
      ]
    },
    "utilized_features": [
      "existing mock-service delay pattern",
      "existing `VITE_USE_MOCKS` environment flag",
      "existing revision suggestion type contracts"
    ],
    "expected_outcomes": [
      "The mock returns deterministic `RevisionSuggestion` objects after the configured delay.",
      "The file does not invent backend-only fields outside the current revision-suggestion schema."
    ]
  },
  {
    "task_id": "58bca1ad-1246-4ccc-9fd3-537b57a23310",
    "purpose": "Implement FE-026 selection tracking as a reusable editor hook so aids and diff workflows can preserve selected text through async requests. This file should derive `selectedText`, `selectionRange`, and `hasSelection` from the existing editor integration rather than storing opaque DOM state only.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/hooks/useSelection.ts",
    "knowledge_base": [
      "existing hook patterns in `frontend/src/hooks`",
      "TipTap editor state selection APIs referenced by the TODO spec",
      "selection lifecycle requirements from FE-026"
    ],
    "references_and_schema": {
      "input_data_schema": "Editor instance or selection source capable of exposing current anchor/head positions and selected text.",
      "output_data_schema": "Hook return object with `selectedText`, `selectionRange`, `hasSelection`, and explicit capture/restore helpers if needed by aids workflows.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/TODO.md",
        "F:/Dev/Narrative-Engine/frontend/src/components/drafting/DraftPreview.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/hooks/useStoryboard.ts"
      ]
    },
    "utilized_features": [
      "React hooks",
      "existing editor integration points in the writing workspace"
    ],
    "expected_outcomes": [
      "Consumers can read the current selection and determine whether any text is selected.",
      "The hook exposes enough state to restore a saved selection after an async aid action."
    ]
  },
  {
    "task_id": "d2a63ebe-62e3-4d64-b055-2a43ac0f40f0",
    "purpose": "Persist FE-026 selection state across workspace interactions so async manuscript-aid and diff flows can restore the exact anchor/head range after tab switches or rerenders.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/stores/selectionStore.ts",
    "knowledge_base": [
      "zustand store patterns in `uiStore.ts`, `workspaceStore.ts`, and `notesStore.ts`",
      "selection state fields from FE-026",
      "store persistence patterns already used in the frontend"
    ],
    "references_and_schema": {
      "input_data_schema": "Selection state should minimally include `selectedText`, `from`, `to`, target document/chapter context, and a boolean or derived `hasSelection`.",
      "output_data_schema": "Zustand store actions for capture, clear, and restore lookup keyed to the active writing context.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/stores/uiStore.ts",
        "F:/Dev/Narrative-Engine/frontend/src/stores/workspaceStore.ts",
        "F:/Dev/Narrative-Engine/TODO.md"
      ]
    },
    "utilized_features": [
      "zustand",
      "existing frontend store conventions"
    ],
    "expected_outcomes": [
      "Selection state survives component rerenders and tab switches within the current session.",
      "Calling the store clear action removes stale selection state deterministically."
    ]
  },
  {
    "task_id": "fd0209f2-c32b-4210-ad8c-0952074b45f5",
    "purpose": "Create FE-027 as a dedicated diff-review component for suggestion/manuscript comparisons using the existing drafting and review type system. The component should render before/after text regions and be ready to consume either mock or future backend diff payloads.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/review/DiffReview.tsx",
    "knowledge_base": [
      "review component composition patterns in `FindingCard.tsx`, `FindingsList.tsx`, and `DecisionForm.tsx`",
      "drafting and review types",
      "selection lifecycle requirements from FE-026"
    ],
    "references_and_schema": {
      "input_data_schema": "Props should accept stable identifiers plus `originalText`, `proposedText`, and optional metadata linking the diff to a suggestion or finding.",
      "output_data_schema": "A rendered side-by-side or inline diff review UI with explicit accept/reject hooks left to parent components.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/components/review/FindingCard.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/types/review.ts",
        "F:/Dev/Narrative-Engine/frontend/src/types/drafting.ts"
      ]
    },
    "utilized_features": [
      "existing review UI patterns",
      "React component composition",
      "Tailwind styling already used in review components"
    ],
    "expected_outcomes": [
      "The new component can render a deterministic before/after diff from passed props.",
      "The component contains no hard-coded placeholder copy unrelated to the supplied texts."
    ]
  },
  {
    "task_id": "aaf80208-f48b-497e-96d0-f4d6d266a025",
    "purpose": "Extend the existing review mock layer for FE-028 so suggestion history can be listed and filtered by project and target object without a backend write endpoint. The mock should remain consistent with existing review/drafting types rather than inventing a new store shape.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/services/mocks/reviewMock.ts",
    "knowledge_base": [
      "current mock review service exports",
      "RevisionSuggestion and ReviewDecision type usage",
      "in-memory mock patterns from other frontend mock services"
    ],
    "references_and_schema": {
      "input_data_schema": "Project id plus optional target filters such as `target_kind` and `target_id`.",
      "output_data_schema": "An in-memory list of revision-suggestion/history objects that remain compatible with existing review or drafting components.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/services/mocks/reviewMock.ts",
        "F:/Dev/Narrative-Engine/frontend/src/services/mocks/draftingMock.ts",
        "F:/Dev/Narrative-Engine/frontend/src/types/review.ts"
      ]
    },
    "utilized_features": [
      "existing mock-service in-memory storage pattern",
      "existing review and drafting type contracts"
    ],
    "expected_outcomes": [
      "The mock layer can return deterministic suggestion-history collections per project.",
      "The file preserves the existing mock-only boundary instead of calling nonexistent backend endpoints."
    ]
  },
  {
    "task_id": "8c989370-ef12-4688-8cac-1d612c57c62c",
    "purpose": "Build FE-029 as a brainstorm workspace component over the existing backend BrainstormService domain vocabulary, while keeping the UI mock-backed until write APIs are surfaced. The component should use current brainstorm item fields such as `content`, `status`, `tags`, and `cluster_key`.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/brainstorm/BrainstormWorkspace.tsx",
    "knowledge_base": [
      "BrainstormService concepts: capture, cluster, promote",
      "workspace component patterns from planning/review/drafting views",
      "toast and loading-state patterns used elsewhere in the frontend"
    ],
    "references_and_schema": {
      "input_data_schema": "Project-scoped brainstorm items with `item_id`, `project_id`, `content`, `status`, `tags`, and optional `cluster_key`.",
      "output_data_schema": "A workspace UI that can render brainstorm items, cluster groupings, and promotion affordances using mock/local state compatible with the backend vocabulary.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/services/brainstorm.py",
        "F:/Dev/Narrative-Engine/frontend/src/types/workspace.ts",
        "F:/Dev/Narrative-Engine/TODO.md"
      ]
    },
    "utilized_features": [
      "existing React workspace patterns",
      "toast store",
      "mock/local component state"
    ],
    "expected_outcomes": [
      "The component renders brainstorm items using the backend-aligned field names `content`, `status`, `tags`, and `cluster_key`.",
      "The component does not call nonexistent brainstorm API routes."
    ]
  },
  {
    "task_id": "326d59d5-c738-4d81-af30-8f56398a696a",
    "purpose": "Build FE-030 as a foundation-screen component using the existing foundation profile schema instead of ad-hoc fields. The UI should align with `premise`, `logline`, `thematic_spine`, `emotional_promise`, `tone_and_voice_direction`, `target_audience`, `narrative_constraints`, `complexity_level`, and `success_definition`.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/foundation/FoundationScreen.tsx",
    "knowledge_base": [
      "FoundationProfileInput field names in `app/services/foundation.py`",
      "frontend form patterns from `ProjectList.tsx` and other edit screens",
      "loading and empty-state patterns used in the app"
    ],
    "references_and_schema": {
      "input_data_schema": "Foundation profile fields exactly matching the backend foundation service vocabulary.",
      "output_data_schema": "A form/view component that renders and edits those fields without renaming them or collapsing them into generic text blobs.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/services/foundation.py",
        "F:/Dev/Narrative-Engine/tests/test_foundation_service.py",
        "F:/Dev/Narrative-Engine/TODO.md"
      ]
    },
    "utilized_features": [
      "existing React form patterns",
      "Tailwind component styling"
    ],
    "expected_outcomes": [
      "The component uses the exact backend-aligned foundation field names.",
      "The component includes deterministic loading/empty/edit states rather than placeholder prose only."
    ]
  },
  {
    "task_id": "83dc1ca4-bb55-4667-a0ca-3808f61647eb",
    "purpose": "Build FE-031 as a character-builder component that maps to the current story-development character vocabulary instead of inventing a separate local schema. The component should be ready to bind to canonical profile fields already implied by character-related planning and foundation records.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/character/CharacterBuilder.tsx",
    "knowledge_base": [
      "story-development repository character profile records",
      "existing writing/planning component patterns",
      "workspace mode composition"
    ],
    "references_and_schema": {
      "input_data_schema": "Character profile data should align with repository fields such as `character_id`, `display_name`, `role_in_story`, `archetype`, `external_goal`, `internal_need`, `misbelief_or_wound`, `core_fear`, `primary_strength`, and `fatal_flaw_or_limitation`.",
      "output_data_schema": "A component tree that can render and edit canonical character fields with deterministic section structure and no placeholder-only cards.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/app/persistence/story_development.py",
        "F:/Dev/Narrative-Engine/TODO.md"
      ]
    },
    "utilized_features": [
      "existing React form/component patterns",
      "Tailwind layout utilities"
    ],
    "expected_outcomes": [
      "The component surfaces canonical character profile fields rather than generic notes only.",
      "The UI is structured so future service wiring can bind directly to backend field names."
    ]
  },
  {
    "task_id": "0bb67a3c-7d6b-4691-8f88-d747aafd9ac2",
    "purpose": "Build FE-032 as a world-bible workspace component using the existing story-development terminology around world context and reference material. The component should be shaped to support future persistence without requiring a new client-side schema migration later.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/bible/WorldBibleWorkspace.tsx",
    "knowledge_base": [
      "existing `bibleStore.ts` and `types/bible.ts`",
      "foundation impacts on `world_bible` in `app/services/foundation.py`",
      "workspace component patterns elsewhere in the frontend"
    ],
    "references_and_schema": {
      "input_data_schema": "World-bible UI state should align with existing bible types/store state already present in the frontend plus backend terminology referring to `world_bible` as a downstream impacted area.",
      "output_data_schema": "A workspace component that renders world-bible entries, navigation, and empty/edit states using the current type/store contract.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/stores/bibleStore.ts",
        "F:/Dev/Narrative-Engine/frontend/src/types/bible.ts",
        "F:/Dev/Narrative-Engine/app/services/foundation.py"
      ]
    },
    "utilized_features": [
      "existing bible store",
      "existing React workspace patterns",
      "Tailwind layout utilities"
    ],
    "expected_outcomes": [
      "The component is driven by the existing bible type/store contract rather than a new ad-hoc data shape.",
      "The component includes explicit empty and populated states for world-bible content."
    ]
  }
]
