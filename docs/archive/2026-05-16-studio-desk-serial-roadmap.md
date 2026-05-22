# Studio Desk Serial Implementation Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement one stage at a time. Do not execute a later stage until the previous stage passes its final verification.

**Goal:** Define the complete serial frontend UI/UX implementation path for Concept A, using existing Narrative Engine capabilities only.

**Architecture:** Stage 1 creates an additive Studio route. Stages 2-5 progressively replace placeholders and route-sized panels with reusable panel-friendly frontend units, then add canon annotation parity and responsive drawer behavior. Stages 6-8 add adaptive shell, persistence, and user-facing layout controls.

**Tech Stack:** React 18, TypeScript, React Router, Zustand, React Query, Tailwind CSS, Vitest, Testing Library.

---

## Stage Order

1. **Stage 1: Studio Shell**
   - Plan: `docs/superpowers/plans/2026-05-16-studio-desk-stage-1-frontend.md`
   - Outcome: `/workspace/:projectId/studio` exists and composes existing surfaces.

2. **Stage 2: Real Suggestions Panel**
   - Plan: `docs/superpowers/plans/2026-05-16-studio-desk-stage-2-suggestions.md`
   - Outcome: Studio suggestions panel uses real merged writing and manuscript-assist suggestions.

3. **Stage 3: Compact Context Panels**
   - Plan: `docs/superpowers/plans/2026-05-16-studio-desk-stage-3-compact-panels.md`
   - Outcome: Generation, Review, and Inspect panels use panel-sized components instead of full route views.

4. **Stage 4: Canon Annotation Parity**
   - Plan: `docs/superpowers/plans/2026-05-16-studio-desk-stage-4-canon-annotations.md`
   - Outcome: Studio character and world bible panels load and create canon annotations using existing canon services.

5. **Stage 5: Responsive Studio Drawers**
    - Plan: `docs/superpowers/plans/2026-05-16-studio-desk-stage-5-responsive-drawers.md`
    - Outcome: Studio rail and context panel collapse into usable mobile/tablet drawers.

6. **Stage 6: Adaptive Shell**
    - Plan: `docs/superpowers/plans/2026-05-16-studio-desk-stage-6-adaptive-shell.md`
    - Outcome: Boolean layout state replaced with adaptive modes (`StudioRailMode`, `StudioContextMode`), bounded width state, compact rail mode, and dynamic grid rendering.

7. **Stage 7: Context Modes**
    - Plan: `docs/superpowers/plans/2026-05-16-studio-desk-stage-7-context-modes.md`
    - Outcome: `studio-layout-v1` localStorage persistence with deterministic hydration seam. Overlay/closed context modes render correctly. Invalid stored values safely ignored.

8. **Stage 8: Layout Polish**
    - Plan: `docs/superpowers/plans/2026-05-16-studio-desk-stage-8-layout-polish.md`
    - Outcome: User-facing layout controls in command bar (`Rail`, `Rail Width`, `Panel Width`, `Layout` reset) and context header (`Pin`, `Dock`, `Overlay`, `Close`). All controls tested through StudioView integration tests.

## Serial Gate

Before starting each next stage, the current stage must satisfy all stage-specific criteria and this shared verification gate:

```powershell
cd frontend; cmd /c npm.cmd run lint
cd frontend; cmd /c npm.cmd run typecheck
cd frontend; cmd /c npm.cmd run build
cd frontend; cmd /c npm.cmd run test
```

Expected: all commands exit 0.

## Stage Exit Criteria

### Stage 1 Exit Criteria

- `/workspace/:projectId/studio` renders without runtime errors.
- Workspace index redirects to `/workspace/:projectId/studio`.
- Existing routes still render: `/plan`, `/write`, `/review`, `/inspect`, `/braindump`, `/canon`, `/generate`.
- Studio command bar can open Ideas, Generation, Review, Inspect, Notes, and Jobs panels.
- Studio project rail can open Characters, World Bible, Relationships, Canon/Generation, Jobs, and Notes panels.
- Stage 1 tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- WorkspaceShell
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Proceed to Stage 2 only when all above checks pass.

### Stage 2 Exit Criteria

- Studio suggestions panel shows real open suggestions from existing writing revision suggestions.
- LLM manuscript-assist suggestions are merged into the same `AidsPanel` list.
- LLM `ARCHIVED` status maps to `REJECTED`, matching existing `WritingView` behavior.
- Accept/reject/archive actions route to the correct existing handlers.
- `WritingView` still shows the same suggestions behavior as before Stage 2.
- Stage 2 tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- useMergedSuggestions
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Proceed to Stage 3 only when all above checks pass.

### Stage 3 Exit Criteria

- Studio Generation panel no longer renders the full route-sized `GenerationView`.
- Studio Review panel no longer renders the full route-sized `ReviewView`.
- Studio Inspect panel no longer renders the full route-sized `InspectView`.
- Full legacy routes for generation, review, and inspect remain unchanged and still pass existing tests.
- Compact panels expose only existing actions and data; no new backend behavior is introduced.
- Stage 3 tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
cd frontend; cmd /c npm.cmd run test -- GenerationView
```

Proceed to Stage 4 only when all above checks pass.

### Stage 4 Exit Criteria

- Studio Characters panel loads existing character canon annotations.
- Studio Characters panel can create a character annotation through `createCanonAnnotation`.
- Studio World Bible panel loads existing world bible canon annotations.
- Studio World Bible panel can create a world bible annotation through `createCanonAnnotation`.
- Annotation query invalidation refreshes only the relevant Studio annotation query keys.
- PlanningView annotation behavior remains unchanged.
- Stage 4 tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
cd frontend; cmd /c npm.cmd run test -- CanonView
```

Proceed to Stage 5 only when all above checks pass.

### Stage 5 Exit Criteria

- Desktop Studio keeps the three-column layout: project rail, center writing surface, context panel.
- Mobile/tablet Studio exposes Project and Context drawer controls.
- Drawer close control is keyboard accessible with `aria-label="Close Studio drawers"`.
- No resize listeners are introduced.
- Existing command bar actions still open the correct panels.
- Stage 5 tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
```

The Studio redesign implementation is complete only when all 8 stages and the shared verification gate pass.

### Stage 6 Exit Criteria

- `StudioRailMode` (`expanded`/`collapsed`/`overlay`) replaces `leftRailOpen` boolean.
- `StudioContextMode` (`docked`/`overlay`/`closed`) replaces `contextPanelOpen` boolean.
- Width state clamped: `leftRailWidth` 192-320, `contextPanelWidth` 320-520.
- Compact rail mode renders 64px icon-only column when collapsed.
- Dynamic `gridTemplateColumns` driven by store state.
- Stage 6 tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- studioStore
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Proceed to Stage 7 only when all above checks pass.

### Stage 7 Exit Criteria

- `studio-layout-v1` persists only layout preferences (never `activePanel`).
- `parseStoredStudioLayout()` returns sanitized layout or `null` for invalid input.
- `clampStudioWidth()` returns fallback for non-finite values.
- Overlay context mode renders above editor without replacing `WritingView`.
- Closed context mode can be reopened by command selection through `openPanel`.
- Stage 7 tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- studioStore
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Proceed to Stage 8 only when all above checks pass.

### Stage 8 Exit Criteria

- `StudioCommandBar` exposes `Layout` reset button with `aria-label="Reset Studio layout"`.
- `StudioCommandBar` exposes desktop-visible `Rail` collapse/expand control.
- `StudioCommandBar` exposes `Rail Width` and `Panel Width` controls that write exact numeric values.
- `StudioContextPanel` exposes `Pin`, `Dock`, `Overlay`, and `Close` controls.
- `resetLayout()` restores the exact default adaptive state.
- Studio navigation stays on `/workspace/:projectId/studio` during command and layout control use.
- Stage 8 tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
cd frontend; cmd /c npm.cmd run test -- WorkspaceShell
```

## Scope Lock

- Frontend UI/UX only.
- Existing services only.
- Existing backend endpoints only.
- Existing LLM behavior only.
- Existing data fields only.
- Do not remove legacy workspace routes until a separate deprecation plan exists.
