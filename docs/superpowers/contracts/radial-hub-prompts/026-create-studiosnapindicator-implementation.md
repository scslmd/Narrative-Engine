# Executor Prompt: RH-T026 - Create StudioSnapIndicator implementation

You are implementing exactly one deterministic task from the radial-hub contract.

## Task Identity
- Task ID: `RH-T026`
- Stage: `S3 - Interaction Polish`
- Responsible file: `frontend/src/components/studio/StudioSnapIndicator.tsx`
- Serial dependencies: RH-T007
- Same-file serial group: none

## Objective
Create the snap-zone detector and overlay component used during drag operations.

## Stage Entry Criteria
- Stage 2 pass criteria are all green.

## Required Identifiers
- `SnapZone`
- `detectSnapZone`
- `StudioSnapIndicator`

## Task Guardrails
- frontend/src/components/studio/StudioRadialHub.tsx

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
1. Modify only `frontend/src/components/studio/StudioSnapIndicator.tsx`.
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

## Stage Gate
Do not begin any task from the next stage until all tasks in `S3` are complete and every stage pass criterion below is green.

### Stage Pass Criteria
- `cd frontend; cmd /c npm.cmd run test -- StudioSnapIndicator.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioFloatingWindow.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioHoverPreview.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- usePanelKeyboard.test.ts`
- `cd frontend; cmd /c npm.cmd run test -- studioStore.layoutPersistence.test.ts`
- `cd frontend; cmd /c npm.cmd run test -- StudioLayoutPreset.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioCommandBar.layoutPreset.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioFloatingPanel.phase3.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioRadialHub.phase3.test.tsx`
- `cd frontend; cmd /c npm.cmd run test`
- `cd frontend; cmd /c npm.cmd run typecheck`
- `cd frontend; cmd /c npm.cmd run lint`
- `cd frontend; cmd /c npm.cmd run build`

### Move To Next Stage Only If
- All Stage 3 focused tests and the full frontend test suite are green.
- Snap-zone and portal code compiles cleanly.
- Layout preset UI is mounted in the command bar.
- The store now supports debounced persistence plus import/export.

## Failure Codes
- `BLOCKED_MISSING_INPUT`
- `BLOCKED_AMBIGUOUS_INSTRUCTION`
- `BLOCKED_NONDETERMINISTIC_CHECK`
- `BLOCKED_PLAN_VIOLATION`
