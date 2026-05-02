# Production v1.0 Readiness Task List

Date: 2026-05-01

## Task Rules

- Complete tasks in order.
- After each task, run the listed validation command.
- Do not mark a task complete unless the acceptance criteria are met.
- Keep changes scoped to the files listed unless the codebase requires a directly related helper update.

## P0 Tasks

### P0-1: Persist contradiction-only continuity findings

Status: `[x]`

Files:

- `app/services/story_import.py`
- `tests/test_story_import_service.py`
- `tests/test_continuity_drafting.py`

Steps:

1. Update `StoryImportService._import_continuity()` so it returns only when `analysis.continuity_finding is None`.
2. Keep thread and state inserts conditional on those lists being present.
3. Always insert or upsert the overall continuity finding when the finding exists.
4. Add a test where `ContinuityFinding` has no threads and no states, but has `contradictions`.
5. Assert the finding is persisted.

Acceptance criteria:

- A continuity finding with only contradictions is stored.
- A continuity finding with only unresolved questions is stored.
- Existing thread/state persistence still works.

Validation:

- `python -m pytest tests/test_story_import_service.py tests/test_continuity_drafting.py -q -p no:cacheprovider`

### P0-2: Make continuity finding persistence idempotent

Status: `[x]`

Files:

- `app/persistence/sqlite.py`
- `app/persistence/story_development.py`
- `app/services/story_import.py`
- `tests/test_story_development_persistence.py`
- `tests/test_story_import_service.py`

Steps:

1. Add a deterministic `finding_key` or `finding_id` column suitable for import-created continuity findings.
2. Add a unique index for `project_id` plus that deterministic key.
3. Add an additive migration for existing databases.
4. Update repository support to upsert continuity findings by deterministic key.
5. Update story import to use `hash_id("import-continuity-finding", f"{project_id}:story-import")` or equivalent.
6. Add a retry/idempotency test proving repeated imports do not create duplicate continuity findings.

Acceptance criteria:

- Retrying the same import leaves exactly one overall continuity finding for that import.
- Existing continuity finding reads still work.
- Migration is additive and does not require wiping existing databases.

Validation:

- `python -m pytest tests/test_story_development_persistence.py tests/test_story_import_service.py tests/test_continuity_drafting.py -q -p no:cacheprovider`

### P0-3: Enforce continuity gates in the live import path

Status: `[x]`

Files:

- `app/services/multi_pass_import.py`
- `app/services/story_import.py`
- `app/schemas/story_import.py`
- `tests/test_multi_pass_import.py`
- `tests/test_story_import_service.py`

Steps:

1. Run `_check_continuity_gate()` after `_run_continuity_consolidation()`.
2. Store gate result and reasons on `StoryImportAnalysis`, or expose them through a dedicated analysis metadata field.
3. Include gate failure reasons in `StoryImportResponse.warnings`.
4. Ensure gate failure does not erase the continuity finding.
5. Ensure gate failure prevents drafting consolidation if drafting is wired.

Acceptance criteria:

- Low-confidence continuity produces a user-visible import warning.
- Critical contradictions produce a user-visible import warning.
- Continuity findings are still persisted when gates fail.

Validation:

- `python -m pytest tests/test_story_import_service.py tests/test_multi_pass_import.py tests/test_continuity_drafting.py -q -p no:cacheprovider`

### P0-4: Decide and enforce the drafting consolidation contract

Status: `[x]`

Decision: Option A implemented. Multi-pass import now generates and persists draft briefs and drafting context packets only after continuity and drafting readiness gates pass.

Files:

- `app/services/multi_pass_import.py`
- `app/services/story_import.py`
- `app/persistence/story_development.py`
- `frontend/src/components/projects/StoryImportModal.tsx`
- `tests/test_multi_pass_import.py`
- `tests/test_story_import_service.py`
- `tests/test_continuity_drafting.py`

Steps:

1. Choose one contract:
   - Option A: wire drafting consolidation fully into multi-pass import.
   - Option B: defer drafting consolidation and remove production-facing claims.
2. If Option A:
   - call `_run_drafting_consolidation()` after continuity gates pass
   - add returned draft briefs and context packets to `StoryImportAnalysis`
   - persist draft briefs and drafting context packets in `StoryImportService._transactional_import()`
   - add tests proving draft artifacts are created only when continuity gates pass
3. If Option B:
   - remove or mark `_run_drafting_consolidation()` as unused/deferred
   - ensure UI and docs do not imply import creates draft-ready artifacts
   - keep repository support only if needed by another live path

Acceptance criteria:

- The code and UI make the same claim.
- Drafting artifacts are either created by the live import path or clearly not part of import v1.0.
- No unused production feature path claims readiness it does not provide.

Validation:

- `python -m pytest tests/test_story_import_service.py tests/test_multi_pass_import.py tests/test_continuity_drafting.py -q -p no:cacheprovider`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`

### P0-5: Fix xdist smoke-test isolation

Status: `[x]`

Files:

- `tests/test_smoke.py`
- possible supporting fixtures/config in `tests/` or `app/settings.py`

Steps:

1. Reproduce the xdist failure with the documented command.
2. Identify why `test_projects_endpoint_lists_projects()` sees an empty project list under xdist.
3. Identify why `test_job_stub_runs()` fails under xdist but passes serially.
4. Make smoke tests isolated with `tmp_path`, explicit seed data, or serial grouping.
5. Avoid depending on shared `data/projects/` runtime state.
6. Re-run the documented xdist command.

Acceptance criteria:

- `tests/test_smoke.py` passes serially.
- The full documented xdist command passes.
- The fix does not depend on existing local runtime data.

Validation:

- `python -m pytest tests/test_smoke.py -q -p no:cacheprovider -n 0`
- `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py`

## P1 Tasks

### P1-1: Address frontend production chunk warning

Status: `[x]`

Files:

- `frontend/src/`
- `frontend/vite.config.ts`

Steps:

1. Inspect the production bundle composition.
2. Add route-level lazy loading or `manualChunks` where appropriate.
3. Avoid changing UI behavior.
4. Re-run the production build.

Acceptance criteria:

- `npm run build` passes.
- The chunk-size warning is resolved or intentionally documented with a configured threshold.

Validation:

- `cd frontend && npm run build`
- `cd frontend && npm run test`

### P1-2: Clean release worktree noise

Status: `[x]`

Files:

- `.gitignore`
- runtime `data/` directory

Steps:

1. Confirm whether `data/projects/` should be ignored.
2. If not ignored, add the correct ignore rule.
3. Remove generated runtime project folders from the release worktree only when explicitly approved.
4. Verify `git status --short` shows no unintended generated artifacts.

Acceptance criteria:

- Release validation can run from a clean tracked worktree.
- Runtime generated project output does not appear as untracked source noise.

Validation:

- `git status --short`

## Final Production v1.0 Gate

Latest validation after implementation:

- `python -m pytest tests/test_continuity_drafting.py tests/test_story_import_service.py tests/test_multi_pass_import.py tests/test_smoke.py -q -p no:cacheprovider -n 0` -> 165 passed.
- `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py` -> 1269 passed, 10 skipped.
- `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records` -> 43 passed.
- `cd frontend && npm run build` -> passed; main application chunk reduced below Vite's warning threshold.
- `cd frontend && npm run lint` -> passed with two pre-existing Fast Refresh warnings.
- `cd frontend && npm run typecheck` -> passed.
- `cd frontend && npm run test` -> 286 passed; one pre-existing React `act(...)` warning remains in `Layout.test.tsx`.
- `git status --short` -> only intentional tracked edits plus the two new production-readiness docs.

Run all commands below before declaring production v1.0 readiness:

1. `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py`
2. `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records`
3. `cd frontend && npm run lint`
4. `cd frontend && npm run typecheck`
5. `cd frontend && npm run build`
6. `cd frontend && npm run test`
7. `git status --short`

## Completion Definition

Production v1.0 is complete only when:

- all P0 tasks are complete
- all final production gate commands pass
- frontend build warnings are either resolved or explicitly accepted
- generated runtime data is not mixed with release source state
