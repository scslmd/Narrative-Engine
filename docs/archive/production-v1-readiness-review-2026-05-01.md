# Production v1.0 Readiness Review

Date: 2026-05-01

## Verdict

Initial review verdict: the codebase was not production v1.0 ready.

It is in a strong development state, with broad targeted test coverage passing, but there are still production blockers in the story import continuity/drafting contract and in the repository validation baseline.

Implementation update: the P0 blockers identified in this review have been fixed in the current working tree. The final remaining caveats are two pre-existing frontend Fast Refresh lint warnings and one pre-existing React `act(...)` warning in the passing frontend test suite.

## Current Validation Snapshot

Post-fix validation:

- `python -m pytest tests/test_continuity_drafting.py tests/test_story_import_service.py tests/test_multi_pass_import.py tests/test_smoke.py -q -p no:cacheprovider -n 0`
- Result: `165 passed`

- `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py`
- Result: `1269 passed, 10 skipped`

- `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records`
- Result: `43 passed`

- `cd frontend && npm run build`
- Result: passed without the prior chunk-size warning

- `cd frontend && npm run lint`
- Result: passed with 2 existing Fast Refresh warnings

- `cd frontend && npm run typecheck`
- Result: passed

- `cd frontend && npm run test`
- Result: `286 passed`, with one existing React `act(...)` warning

Initial validation snapshot:

Passing checks:

- `python -m pytest tests/test_continuity_drafting.py tests/test_story_import_service.py tests/test_multi_pass_import.py -q -p no:cacheprovider`
- Result: `157 passed`

- `python -m pytest tests/test_story_development_persistence.py tests/test_planning_service.py tests/test_import_jobs.py tests/test_json_extract.py -q -p no:cacheprovider`
- Result: `80 passed`

- `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records`
- Result: `43 passed`

- `python -m pytest tests/test_smoke.py -q -p no:cacheprovider -n 0`
- Result: `5 passed`

- `cd frontend && npm run typecheck`
- Result: passed

- `cd frontend && npm run lint`
- Result: passed with 2 existing warnings

- `cd frontend && npm run test`
- Result: `286 passed`

- `cd frontend && npm run build`
- Result: passed, with a Vite chunk-size warning

Failing checks:

- `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py`
- Result: `2 failed, 1264 passed, 10 skipped`
- Failing file: `tests/test_smoke.py`
- Observed behavior: smoke tests pass serially but fail inside the xdist cluster, which indicates test isolation or global fixture coupling.

## Production Blockers

### P0-1: Drafting consolidation exists but is not wired into the import pipeline

Finding:

- `app/services/multi_pass_import.py::_run_drafting_consolidation()` exists.
- It has no production call site.
- `draft_briefs` and `drafting_context_packets` persistence exists, but story import does not create those artifacts.

Impact:

- Any claim that import creates drafting-ready artifacts is currently false.
- The codebase has tables, repository support, and tests for drafting artifacts, but the live pipeline does not complete the feature.

Required fix:

- Either wire drafting consolidation into the multi-pass import pipeline and persist its outputs, or explicitly mark the drafting phase deferred and remove production-facing claims.

### P0-2: Continuity gates exist but do not affect import outcome

Finding:

- `MultiPassImportService._check_continuity_gate()` exists.
- `MultiPassImportService._check_drafting_readiness()` exists.
- The live import path does not use the continuity gate to warn, downgrade, block drafting output, or mark the response as degraded.

Impact:

- Weak continuity analysis can pass through the import flow without a user-visible signal.
- Drafting readiness is currently a helper-level concept, not an enforced pipeline invariant.

Required fix:

- Run continuity gating after continuity consolidation.
- Convert gate failures into explicit import warnings and degraded statuses.
- Prevent drafting consolidation when continuity gates fail.

### P0-3: Continuity findings with only contradictions or unresolved questions can be dropped

Finding:

- `StoryImportService._import_continuity()` returns early when there are no threads and no states.
- A valid finding that contains only `contradictions` or `unresolved_questions` is not persisted.

Impact:

- The most important continuity output can be lost if the model reports problems without structured thread/state records.

Required fix:

- Persist overall continuity findings whenever a `ContinuityFinding` exists, even if `threads` and `states` are empty.

### P0-4: Continuity findings are not idempotent on retry

Finding:

- `continuity_findings` uses an autoincrement `finding_id`.
- Import inserts an overall finding with plain `INSERT`.
- Most other import artifacts use deterministic IDs and upserts.

Impact:

- Retrying an import can append duplicate continuity findings for the same project/import evidence.
- This breaks the idempotency principle used elsewhere in the import path.

Required fix:

- Add a deterministic import-scoped key or finding identifier.
- Upsert continuity findings by that deterministic key.

### P0-5: Backend xdist validation baseline fails

Finding:

- The recommended parallel backend validation command fails in `tests/test_smoke.py`.
- The same smoke tests pass serially.

Impact:

- The repo cannot satisfy its documented merge-readiness gate.
- Production v1.0 readiness cannot be claimed while the baseline validation command is red.

Required fix:

- Isolate smoke-test runtime state or exclude/mark smoke tests consistently if they are serial-only.
- Ensure the documented xdist command passes.

## Production Risks

### P1-1: Frontend build has a large chunk warning

Finding:

- `npm run build` passes but Vite warns that the main JS chunk is above 500 kB.

Impact:

- Not a correctness blocker, but it is a production packaging concern.

Required fix:

- Add route-level or feature-level code splitting, or configure chunking intentionally.

### P1-2: Runtime project folders remain untracked

Finding:

- Multiple generated `data/projects/...` folders are untracked.

Impact:

- This is not a source-code bug, but it adds release noise and can hide accidental generated files.

Required fix:

- Confirm `data/projects/` is ignored, or clean generated runtime output before release validation.

## Production v1.0 Definition

The codebase should not be called production v1.0 ready until all of these are true:

1. Import continuity findings persist even when only contradictions or unresolved questions exist.
2. Continuity findings are idempotent across retries.
3. Continuity gates affect import output and block drafting artifacts when needed.
4. Drafting consolidation is either fully wired and persisted or explicitly deferred from product claims.
5. The documented backend xdist validation command passes.
6. Serial backend tests pass.
7. Frontend lint, typecheck, tests, and build pass.
8. Release validation runs from a clean tracked worktree, excluding intentional ignored runtime data.
