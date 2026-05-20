# Executor Prompt: RH-T041 - Simplify useRouteSync for the single-route workspace

You are implementing exactly one deterministic task from the radial-hub contract.

## Task Identity
- Task ID: `RH-T041`
- Stage: `S4 - Route Migration`
- Responsible file: `frontend/src/hooks/useRouteSync.ts`
- Serial dependencies: RH-T039
- Same-file serial group: none

## Objective
Preserve transient segment-based mode derivation for redirect routes, but converge studio renders on the single-route model.

## Stage Entry Criteria
- Stage 3 pass criteria are all green.

## Required Identifiers
- `matchPath('/workspace/:projectId/:segment?')`
- `setMode('plan')`
- `segment`

## Task Guardrails
- frontend/src/hooks/usePanelUrlSync.ts

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
1. Modify only `frontend/src/hooks/useRouteSync.ts`.
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
- Non-workspace routes still reset mode safely.

## Stage Gate
Do not begin any task from the next stage until all tasks in `S4` are complete and every stage pass criterion below is green.

### Stage Pass Criteria
- `cd frontend; cmd /c npm.cmd run test -- App.redirects.test.tsx`
- `cd frontend; cmd /c npm.cmd run typecheck`
- `cd frontend; cmd /c npm.cmd run build`
- `Manual redirect checks for /plan, /review, /inspect/:jobId, /braindump, /canon?tab=mythos, /generate, /write/:chapterId resolve to /studio query URLs.`

### Move To Next Stage Only If
- Focused redirect tests are green.
- Legacy workspace URLs redirect to studio query-param URLs without 404s.
- Stage buttons and left-rail navigation link directly to studio query URLs.
- StudioView reads initial tab/job/chapter URL state without type errors.

## Failure Codes
- `BLOCKED_MISSING_INPUT`
- `BLOCKED_AMBIGUOUS_INSTRUCTION`
- `BLOCKED_NONDETERMINISTIC_CHECK`
- `BLOCKED_PLAN_VIOLATION`
