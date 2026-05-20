# Executor Prompt: RH-T016 - Add StudioStructurePanel tests

You are implementing exactly one deterministic task from the radial-hub contract.

## Task Identity
- Task ID: `RH-T016`
- Stage: `S2 - Panel Migration`
- Responsible file: `frontend/src/components/studio/StudioStructurePanel.test.tsx`
- Serial dependencies: RH-T015
- Same-file serial group: none

## Objective
Add focused rendering and empty-state coverage for the structure panel.

## Stage Entry Criteria
- Stage 1 pass criteria are all green.
- StudioPanelContent, StudioRadialHub, StudioFloatingPanel, and layout actions already exist.

## Required Identifiers
- `StudioStructurePanel`
- `data-structure-panel`

## Task Guardrails
- frontend/src/components/studio/StudioStructurePanel.tsx

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
1. Modify only `frontend/src/components/studio/StudioStructurePanel.test.tsx`.
2. Satisfy all required identifiers exactly as listed.
3. Do not edit files listed in task guardrails.
4. Do not expand scope beyond this task.
5. If this task cannot be completed within the responsible file, stop with `BLOCKED_PLAN_VIOLATION`.
6. If a dependency is not already complete, stop with `BLOCKED_PLAN_VIOLATION`.
7. After editing, run the exact verification commands below.
8. Report completion only if every verification command for this task succeeds.

## Verification Commands
- `cd frontend; cmd /c npm.cmd run test -- StudioStructurePanel.test.tsx`

## Expected Result
- Focused StudioStructurePanel tests pass.

## Stage Gate
Do not begin any task from the next stage until all tasks in `S2` are complete and every stage pass criterion below is green.

### Stage Pass Criteria
- `cd frontend; cmd /c npm.cmd run test -- StudioDraftsPanel.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioStructurePanel.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioChaptersPanel.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioCanonPanel.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioStatusBar.test.tsx`
- `cd frontend; cmd /c npm.cmd run typecheck`
- `cd frontend; cmd /c npm.cmd run build`

### Move To Next Stage Only If
- All Stage 2 focused tests pass.
- The panel router resolves drafts, structure, chapters, and canon without placeholder fallback.
- StudioView renders the status bar below the hub.

## Failure Codes
- `BLOCKED_MISSING_INPUT`
- `BLOCKED_AMBIGUOUS_INSTRUCTION`
- `BLOCKED_NONDETERMINISTIC_CHECK`
- `BLOCKED_PLAN_VIOLATION`
