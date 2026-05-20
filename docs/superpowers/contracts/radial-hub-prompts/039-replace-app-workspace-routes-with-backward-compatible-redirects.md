# Executor Prompt: RH-T039 - Replace App workspace routes with backward-compatible redirects

You are implementing exactly one deterministic task from the radial-hub contract.

## Task Identity
- Task ID: `RH-T039`
- Stage: `S4 - Route Migration`
- Responsible file: `frontend/src/App.tsx`
- Serial dependencies: RH-T038
- Same-file serial group: app-routing

## Objective
Replace the legacy view routes with redirect components that preserve tab, jobId, chapterId, and canon subtab semantics.

## Stage Entry Criteria
- Stage 3 pass criteria are all green.

## Required Identifiers
- `PlanRedirect`
- `ReviewRedirect`
- `InspectRedirect`
- `BrainDumpRedirect`
- `CanonRedirect`
- `GenerateRedirect`
- `WriteRedirect`
- `/workspace/:projectId/studio`

## Task Guardrails
- frontend/src/routes.ts

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
1. Modify only `frontend/src/App.tsx`.
2. Satisfy all required identifiers exactly as listed.
3. Do not edit files listed in task guardrails.
4. Do not expand scope beyond this task.
5. If this task cannot be completed within the responsible file, stop with `BLOCKED_PLAN_VIOLATION`.
6. If a dependency is not already complete, stop with `BLOCKED_PLAN_VIOLATION`.
7. After editing, run the exact verification commands below.
8. Report completion only if every verification command for this task succeeds.

## Verification Commands
- `cd frontend; cmd /c npm.cmd run typecheck`
- `cd frontend; cmd /c npm.cmd run build`

## Expected Result
- Typecheck exits 0.
- Build exits 0.

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
