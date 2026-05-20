# Executor Prompt: RH-T001 - Extend studioStore for floating-panel layout state and panel keys

You are implementing exactly one deterministic task from the radial-hub contract.

## Task Identity
- Task ID: `RH-T001`
- Stage: `S1 - Core Infrastructure`
- Responsible file: `frontend/src/stores/studioStore.ts`
- Serial dependencies: none
- Same-file serial group: studio-store

## Objective
Add structure, chapters, canon to StudioPanelKey and add layout state, persistence helpers, panel actions, currentProjectId, and reset behavior required by the radial hub.

## Stage Entry Criteria
- Use the existing frontend tree under frontend/src.
- Do not modify existing panel content components except through explicitly listed call sites.
- Stage 1 must stay frontend-only.

## Required Identifiers
- `StudioPanelKey`
- `PanelLayoutState`
- `StudioLayoutState`
- `currentProjectId`
- `addPanel`
- `removePanel`
- `movePanel`
- `resizePanel`
- `togglePanel`
- `updatePanelState`
- `pinPanel`
- `tearOffPanel`
- `reattachPanel`
- `bringToFront`
- `loadLayout`
- `STUDIO_LAYOUT_V2_KEY`
- `persistLayoutV2`
- `loadLayoutV2`

## Task Guardrails
- frontend/src/views/StudioView.tsx
- frontend/src/components/studio/**

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
1. Modify only `frontend/src/stores/studioStore.ts`.
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
- The store exposes the full Phase 1 layout API with no as any casts.

## Stage Gate
Do not begin any task from the next stage until all tasks in `S1` are complete and every stage pass criterion below is green.

### Stage Pass Criteria
- `cd frontend; cmd /c npm.cmd run test -- StudioFloatingPanel.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioPanelMenu.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioRadialHub.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioView.test.tsx`
- `cd frontend; cmd /c npm.cmd run typecheck`
- `cd frontend; cmd /c npm.cmd run lint`
- `cd frontend; cmd /c npm.cmd run build`

### Move To Next Stage Only If
- All Stage 1 task verifications are green.
- StudioView renders data-radial-hub on /workspace/:projectId/studio.
- No Stage 1 task changed backend code or legacy route behavior.

## Failure Codes
- `BLOCKED_MISSING_INPUT`
- `BLOCKED_AMBIGUOUS_INSTRUCTION`
- `BLOCKED_NONDETERMINISTIC_CHECK`
- `BLOCKED_PLAN_VIOLATION`
