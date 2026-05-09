# Mixed API Surface Migration Contract (Deterministic / Atomic)
Status: **Superseded** — split into executable plan files PR-A through PR-E (2026-05-08)

> **This contract has been superseded by the following plan files.** Execute the plans in order, respecting cross-plan dependencies. Do not implement tasks from this document directly.
>
> 1. **[PR-A: Route Inventory & Classification](./2026-05-08-api-migration-pr-a-inventory.md)** — Tasks 001-005 (no dependencies)
> 2. **[PR-B: Backend Canonical Routes](./2026-05-08-api-migration-pr-b-backend-canonical.md)** — Tasks 006-011 (depends on PR-A)
> 3. **[PR-C: Parity Tests, Telemetry & Cutover Gates](./2026-05-08-api-migration-pr-c-parity-telemetry.md)** — Tasks 012-013 + 017-018 (depends on PR-B)
> 4. **[PR-D: Frontend Endpoint Migration](./2026-05-08-api-migration-pr-d-frontend.md)** — Tasks 014-016 (depends on PR-B, parallel with PR-C)
> 5. **[PR-E: Legacy Removal & Closure](./2026-05-08-api-migration-pr-e-removal-closure.md)** — Tasks 019-022 (depends on PR-C + PR-D)

Date: 2026-05-08
Scope: Migrate mixed API surface (`/v1` + unversioned) to canonical `/v1` contract with compatibility phase, telemetry, and controlled legacy removal.

## 1) Objective

Eliminate architectural drift caused by mixed route versioning while preserving behavioral compatibility during migration.

## 2) Target End State

1. Canonical client-facing API surface is `/v1/*`.
2. Legacy unversioned routes are either deprecated wrappers or removed.
3. Frontend production services call canonical `/v1` routes only.
4. OpenAPI clearly marks legacy routes as deprecated.
5. Parity + error semantics are covered by deterministic tests.
6. Legacy endpoint usage is measurable and used as a hard removal gate.

## 3) Non-Goals

1. No business-logic redesign.
2. No schema redesign unless required to align legacy/canonical parity.
3. No broad refactors outside route/service/test/docs surfaces.

## 4) Preconditions

1. Work from clean branch off current `codex/main`.
2. Baseline tests pass before migration start.
3. Route inventory script can run against app startup in local env.

## 5) Atomic Task Cards

Each card is atomic, deterministic, and independently verifiable.

### API-SURFACE-001 Route Inventory Snapshot
Purpose: Capture full runtime route table.
Write scope:
1. `scripts/api_route_inventory.py` (new)
2. `docs/api-migration/route_inventory.json` (generated)
Steps:
1. Add script that imports app and emits `{method, path, name, tags}` list.
2. Run script and persist JSON.
Verification:
1. `python scripts/api_route_inventory.py`
2. `python -c "import json;print(len(json.load(open('docs/api-migration/route_inventory.json','r',encoding='utf-8'))))"`
Done when:
1. Inventory file exists and is non-empty.

### API-SURFACE-002 Route Classification Table
Purpose: Classify all routes by contract role.
Write scope:
1. `docs/api-migration/route_classification.csv` (new)
Steps:
1. Classify every route from inventory into one of:
   - `canonical_v1`
   - `legacy_unversioned`
   - `dual`
   - `internal`
Verification:
1. `python - << 'PY'\nimport csv,json\ninv=json.load(open('docs/api-migration/route_inventory.json','r',encoding='utf-8'))\nrows=list(csv.DictReader(open('docs/api-migration/route_classification.csv','r',encoding='utf-8')))\nprint(len(inv),len(rows))\nassert len(inv)==len(rows)\nPY`
Done when:
1. Row count equals inventory count.
2. Every row has one valid classification.

### API-SURFACE-003 Legacy-to-Canonical Mapping Spec
Purpose: Define authoritative endpoint mapping.
Write scope:
1. `docs/api-migration/legacy_to_v1_mapping.md` (new)
Steps:
1. Add table columns: `legacy_method`, `legacy_path`, `v1_method`, `v1_path`, `status_parity`, `schema_parity_notes`.
2. Ensure no legacy route remains unmapped.
Verification:
1. `rg -n "TODO|TBD|UNMAPPED" docs/api-migration/legacy_to_v1_mapping.md`
Done when:
1. Mapping is complete and has no unresolved placeholders.

### API-SURFACE-004 Compatibility & Sunset Policy
Purpose: Establish deterministic deprecation behavior.
Write scope:
1. `docs/api-migration/compatibility_policy.md` (new)
Steps:
1. Define required legacy response headers: `Deprecation`, `Sunset`, `Link`.
2. Define objective removal gate (zero hits for N days).
3. Define default compatibility window and change control.
Verification:
1. `rg -n "Deprecation|Sunset|zero hits" docs/api-migration/compatibility_policy.md`
Done when:
1. Policy is concrete and date/threshold based.

### API-SURFACE-005 v1 Gap Checklist
Purpose: Determine missing canonical routes before implementation.
Write scope:
1. `docs/api-migration/v1_gap_checklist.md` (new)
Steps:
1. Enumerate each legacy route and mark canonical status:
   - exists
   - missing (implementation required)
Verification:
1. `rg -n "\\[ \\]" docs/api-migration/v1_gap_checklist.md`
Done when:
1. Checklist is complete and actionable.

### API-SURFACE-006 Canonicalize Projects Endpoints
Purpose: Add/confirm `/v1/projects/*` canonical surface.
Write scope:
1. `app/api/projects.py`
2. `tests/test_projects_api.py` (or equivalent route tests)
Steps:
1. Add missing `/v1` project route registrations.
2. Preserve payload and status parity.
Verification:
1. `python -m pytest -q -p no:cacheprovider tests/test_projects_api.py`
Done when:
1. `/v1` project endpoints pass route tests.

### API-SURFACE-007 Canonicalize Auth Endpoints
Purpose: Add/confirm `/v1/auth/*`.
Write scope:
1. `app/api/auth.py` (or current auth router module)
2. `tests/test_authentication.py`
Steps:
1. Register canonical `/v1/auth` endpoints for existing auth features.
2. Preserve status semantics (`401`, `403`, etc.).
Verification:
1. `python -m pytest -q -p no:cacheprovider tests/test_authentication.py`
Done when:
1. Auth tests pass with canonical routes.

### API-SURFACE-008 Canonicalize Backup Endpoints
Purpose: Add/confirm `/v1/backup/*`.
Write scope:
1. `app/api/backup.py` (or current backup router module)
2. `tests/test_backup.py`
Steps:
1. Register canonical backup routes with parity.
Verification:
1. `python -m pytest -q -p no:cacheprovider tests/test_backup.py`
Done when:
1. Backup tests pass with canonical routes.

### API-SURFACE-009 Health Versioning Decision (Prerequisite: human policy decision required before implementation execution)
Purpose: Make health route policy explicit and enforced.
Write scope:
1. `app/api/health.py`
2. `docs/api-migration/compatibility_policy.md`
3. `tests/test_health_api.py`
Steps:
1. Decide health route policy:
   - canonical `/v1/health/*` plus optional legacy alias, or
   - explicit permanent unversioned exception.
2. Implement and test policy.
Verification:
1. `python -m pytest -q -p no:cacheprovider tests/test_health_api.py`
Done when:
1. Health behavior matches documented policy.

### API-SURFACE-010 Legacy Compatibility Wrappers
Purpose: Preserve old clients while migrating.
Write scope:
1. relevant router modules in `app/api/*.py`
2. shared helper (new): `app/api/deprecation.py`
Steps:
1. Keep legacy route paths as wrappers forwarding to canonical handlers.
2. Inject deprecation headers per policy.
Verification:
1. Route-level tests asserting payload parity and headers.
Done when:
1. Legacy behavior remains functional and marked deprecated.

### API-SURFACE-011 OpenAPI Canonicalization
Purpose: Reflect canonical vs deprecated routes in API docs.
Write scope:
1. route decorators / metadata in `app/api/*.py`
2. optional OpenAPI config in `app/main.py`
Steps:
1. Mark legacy endpoints as `deprecated=True`.
2. Ensure canonical `/v1` endpoints are primary.
Verification:
1. `python - << 'PY'\nfrom app.main import build_app\napp=build_app();o=app.openapi();\nprint('paths',len(o.get('paths',{})))\nPY`
Done when:
1. OpenAPI exposes deprecation flags for legacy routes.

### API-SURFACE-012 Backend Route Parity Tests
Purpose: Lock identical behavior between legacy and canonical endpoints.
Write scope:
1. `tests/test_api_route_parity.py` (new)
Steps:
1. Add parametric tests over mapping table.
2. Assert response status/body equivalence for route pairs.
Verification:
1. `python -m pytest -q -p no:cacheprovider tests/test_api_route_parity.py`
Done when:
1. All route pairs pass parity.

### API-SURFACE-013 Error Semantics Contract Tests
Purpose: Ensure parity for non-2xx behavior.
Write scope:
1. `tests/test_api_error_semantics.py` (new)
Steps:
1. Assert `401/403/404/409/5xx` parity across legacy and `/v1`.
Verification:
1. `python -m pytest -q -p no:cacheprovider tests/test_api_error_semantics.py`
Done when:
1. Error behavior is deterministic and identical.

### API-SURFACE-014 Frontend Endpoint Inventory
Purpose: Determine all frontend route references.
Write scope:
1. `scripts/frontend_endpoint_inventory.py` (new)
2. `docs/api-migration/frontend_endpoint_inventory.csv` (generated)
Steps:
1. Scan frontend service files for endpoint strings.
2. Export inventory with file/function/endpoint.
Verification:
1. `python scripts/frontend_endpoint_inventory.py`
Done when:
1. Inventory file exists and contains all service endpoints.

### API-SURFACE-015 Frontend Service Migration to Canonical `/v1`
Purpose: Eliminate legacy endpoint usage from production UI.
Write scope:
1. `frontend/src/services/**/*.ts`
2. `frontend/src/lib/**/*.ts` (API wrappers)
Steps:
1. Switch all production calls to canonical `/v1` paths.
2. Keep parameter naming/status handling unchanged.
Verification:
1. `rg -n "api\\.(get|post|patch|put|delete)\\((`|'|\")/(?!v1)" frontend/src/services frontend/src/lib -S`
2. `rg -n "API_BASE|fetch\\(|axios\\.(get|post|patch|put|delete)\\((`|'|\")/(?!v1)" frontend/src/services frontend/src/lib -S`
3. `cd frontend && npm run typecheck`
4. `cd frontend && npm run test`
Done when:
1. No legacy endpoint strings remain in production service layer.

### API-SURFACE-016 Frontend Tests & Mocks Migration
Purpose: Align test fixtures with canonical API.
Write scope:
1. `frontend/src/**/*.test.ts*`
2. `frontend/src/__tests__/setup.ts` (MSW handlers)
Steps:
1. Update MSW handlers to canonical routes.
2. Keep UI behavior assertions intact.
Verification:
1. `cd frontend && npm run test`
Done when:
1. Frontend test suite passes with canonical route mocks.

### API-SURFACE-017 Legacy Route Usage Telemetry
Purpose: Quantify safe removal readiness.
Write scope:
1. `app/middleware/request_telemetry.py` (or currently active structured logging middleware module if different)
2. `app/main.py` (middleware registration, if needed)
3. `docs/api-migration/legacy_usage_query.md` (new)
Steps:
1. Emit structured event `legacy_route_hit` with path/method/client info.
2. Add query instructions for zero-usage checks.
Verification:
1. test that legacy request produces telemetry event.
Done when:
1. Legacy usage can be measured objectively.

### API-SURFACE-018 Cutover Gate Definition
Purpose: Remove subjective go/no-go.
Write scope:
1. `docs/api-migration/cutover_gate.md` (new)
Steps:
1. Define deterministic criteria:
   - parity tests green
   - frontend canonical-only checks green
   - legacy hits = 0 for N days
Verification:
1. `rg -n "legacy hits = 0|parity tests|frontend canonical-only" docs/api-migration/cutover_gate.md`
Done when:
1. Gate is measurable and enforceable.

### API-SURFACE-019 Legacy Removal Batch 1
Purpose: Remove low-risk legacy paths after gate.
Write scope:
1. legacy wrappers in `app/api/*.py`
2. parity tests/docs updated accordingly
Steps:
1. Remove first eligible subset with zero usage.
2. Keep canonical routes unchanged.
Verification:
1. full backend suite segment + parity suite.
Done when:
1. Removed routes are absent from route inventory.

### API-SURFACE-020 Legacy Removal Batch 2 (Final)
Purpose: Complete removal phase.
Write scope:
1. remaining legacy wrappers in `app/api/*.py`
2. docs/tests cleanup
Steps:
1. Remove all remaining legacy routes except policy exceptions.
Verification:
1. regenerate route inventory and confirm absence.
Done when:
1. Canonical `/v1` is sole client surface (except explicit exceptions).

### API-SURFACE-021 Documentation Finalization
Purpose: Align all docs to canonical contract.
Write scope:
1. `README.md`
2. `AGENTS.md`
3. `docs/User Guide v1.7.0.md`
4. `docs/Narrative Engine User Walkthrough v1.7.0.md`
5. `docs/api-migration/upgrade_guide.md` (new)
Steps:
1. Update endpoint references and migration notes.
2. Add breaking/non-breaking guidance.
Verification:
1. `rg -n "/projects|/auth|/backup|/health" docs README.md AGENTS.md -S`
Done when:
1. Canonical endpoint references are consistent.

### API-SURFACE-022 Full Verification & Closure Report
Purpose: Ensure merge-readiness and audit trail.
Write scope:
1. `docs/api-migration/verification_report.md` (new)
Steps:
1. Run required backend + frontend validations.
2. Record pass/fail outputs and timestamps.
Verification commands:
1. `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py --ignore=tests/test_smoke.py --ignore=tests/test_local_executor_manuscript_assist.py --ignore=tests/test_story_generation_e2e.py`
2. `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records tests/test_smoke.py tests/test_local_executor_manuscript_assist.py tests/test_story_generation_e2e.py tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters`
3. `cd frontend && npm run lint`
4. `cd frontend && npm run typecheck`
5. `cd frontend && npm run build`
6. `cd frontend && npm run test`
Done when:
1. All checks are green and report is committed.

## 6) Recommended PR Slices

Dependency graph (must honor order):
1. 001 -> 002 -> 003 -> 004 -> 005
2. 003 and 005 must complete before 006, 007, 008, 009, 010, 011
3. 006-011 must complete before 012 and 013
4. 012, 013, and 017 must complete before 018
5. 018 must complete before 019 and 020
6. 014 should run before 015, and 015 before 016

Execution decomposition note: this contract is policy-level. Execute as five separate plan files aligned to PR-A through PR-E before assigning to worker agents.

1. PR-A: `001-005` (inventory/spec/policy)
2. PR-B: `006-011` (backend canonical + wrappers + OpenAPI)
3. PR-C: `012-013,017-018` (parity/error/telemetry/gates)
4. PR-D: `014-016` (frontend migration)
5. PR-E: `019-022` (removal + final docs + verification)

## 7) Hard Safety Rules

1. Do not remove legacy endpoints before telemetry gate passes.
2. Do not merge frontend canonicalization before backend `/v1` parity is proven.
3. Do not change business logic semantics during route migration.
4. All route behavior changes must be backed by explicit tests.

## 8) Completion Criteria

1. Canonical `/v1` contract is complete and documented.
2. Legacy usage is zero for policy window.
3. Legacy routes removed (or explicitly excepted).
4. Full verification suite passes.
