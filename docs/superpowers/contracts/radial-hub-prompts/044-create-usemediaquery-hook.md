# Executor Prompt: RH-T044 - Create useMediaQuery hook

You are implementing exactly one deterministic task from the radial-hub contract.

## Task Identity
- Task ID: `RH-T044`
- Stage: `S5 - Validation, Accessibility, And Mobile Behavior`
- Responsible file: `frontend/src/hooks/useMediaQuery.ts`
- Serial dependencies: RH-T035
- Same-file serial group: none

## Objective
Create an SSR-safe, reusable media-query hook used by the radial hub and panel menu with no studio-specific branching or panel-coupled behavior.

## Stage Entry Criteria
- Stage 4 pass criteria are all green.

## Required Identifiers
- `useMediaQuery`
- `typeof window === 'undefined'`
- `window.matchMedia`

## Task Guardrails
- frontend/src/components/studio/StudioRadialHub.tsx
- frontend/src/components/studio/StudioPanelMenu.tsx
- Do not couple the hook to a specific panel key, route, or studio-only condition.

## Global Determinism Choices
- Implement true tear-off as a same-tab React portal mounted to document.body. Do not open OS windows or browser popups.
- Do not create a Phase 2 projectId prop migration for StudioManuscriptsPanel. Keep its current onSelect-only API until useWritingView is explicitly refactored.
- Do not implement the deferred routes.ts rewrite from Phase 4. It is dead code in the current repo and must remain out of scope.
- Treat Phase 5 accessibility work as additive semantics and tests. Do not invent new clickable status-bar behavior.
- Use the existing Axios and service-layer patterns already present in frontend/src/lib/api.ts and frontend/src/services. Do not introduce fetch.

## Global Do-Not Rules
- Do not add backend APIs, schemas, database fields, or prompt contracts.
- Do not remove existing workspace routes until the redirect stage explicitly replaces them with backward-compatible redirects.
- Do not add mock production data.
- Do not use as any, @ts-ignore, or ad hoc API base URLs.
- Do not expand scope to unrelated refactors.

## Instructions
1. Modify only `frontend/src/hooks/useMediaQuery.ts`.
2. Satisfy all required identifiers exactly as listed.
3. Do not edit files listed in task guardrails.
4. Do not expand scope beyond this task.
5. If this task cannot be completed within the responsible file, stop with `BLOCKED_PLAN_VIOLATION`.
6. If a dependency is not already complete, stop with `BLOCKED_PLAN_VIOLATION`.
7. After editing, run the exact verification commands below.
8. Report completion only if every verification command for this task succeeds.

## Verification Commands
- `cd frontend; cmd /c npm.cmd run typecheck`

## Expected Result
- Typecheck exits 0.
- The hook is reusable from any frontend component without studio-specific imports.

## Stage Gate
Do not begin any task from the next stage until all tasks in `S5` are complete and every stage pass criterion below is green.

### Stage Pass Criteria
- `cd frontend; cmd /c npm.cmd run test`
- `cd frontend; cmd /c npm.cmd run lint`
- `cd frontend; cmd /c npm.cmd run typecheck`
- `cd frontend; cmd /c npm.cmd run build`
- `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py --ignore=tests/test_smoke.py --ignore=tests/test_local_executor_manuscript_assist.py --ignore=tests/test_story_generation_e2e.py`
- `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records tests/test_smoke.py tests/test_local_executor_manuscript_assist.py tests/test_story_generation_e2e.py tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters tests/test_discovery_api.py::test_patch_returns_updated tests/test_story_bible_lineage.py::TestStoryBibleLineageContentHash::test_story_bible_content_hash_matches_file_content`

### Move To Next Stage Only If
- All frontend tests pass.
- Lint, typecheck, and build are green.
- Both backend validation commands pass with the repository's documented timeout expectations.
- Manual mobile and accessibility checks do not reveal regressions.

## Failure Codes
- `BLOCKED_MISSING_INPUT`
- `BLOCKED_AMBIGUOUS_INSTRUCTION`
- `BLOCKED_NONDETERMINISTIC_CHECK`
- `BLOCKED_PLAN_VIOLATION`
