# Studio Desk Adaptive 3-Panel Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement one stage at a time. Do not execute a later stage until the previous stage passes its final verification.

**Goal:** Define the serial post-Stage-5 frontend delta that refines Studio into a cleaner adaptive three-panel workspace.

**Architecture:** Stages 6-8 treat the implemented Stage 5 Studio as the baseline. The delta preserves the stable center writing surface, keeps the left rail and right context panel bounded, and replaces the floating-panels direction with adaptive docked/overlay behavior and persisted layout preferences.

**Tech Stack:** React 18, TypeScript, React Router, Zustand, Tailwind CSS, Testing Library, Vitest.

---

## Baseline Assumption

Stages 1-5 are already implemented and passing. This roadmap does not re-implement any previous stage.

## Stage Order

1. **Stage 6: Adaptive Shell Foundation**
   - Plan: `docs/superpowers/plans/2026-05-16-studio-desk-stage-6-adaptive-shell.md`
   - Outcome: Studio store and view support bounded left/right panel modes and widths.

2. **Stage 7: Context Modes And Persistence**
   - Plan: `docs/superpowers/plans/2026-05-16-studio-desk-stage-7-context-modes.md`
   - Outcome: Right context panel supports `docked`, `overlay`, and `closed` modes with persisted layout preferences.

3. **Stage 8: Layout Controls And Polish**
   - Plan: `docs/superpowers/plans/2026-05-16-studio-desk-stage-8-layout-polish.md`
   - Outcome: Command bar and context header expose deterministic layout controls and reset behavior without route or API changes.

## Shared Verification Gate

Before starting each next stage, the current stage must satisfy all stage-specific criteria and this shared verification gate:

```powershell
cd frontend; cmd /c npm.cmd run lint
cd frontend; cmd /c npm.cmd run typecheck
cd frontend; cmd /c npm.cmd run build
cd frontend; cmd /c npm.cmd run test
```

Expected: all commands exit `0`.

## Stage Exit Criteria

### Stage 6 Exit Criteria

- `studioStore.ts` exposes `leftRailMode`, `contextPanelMode`, `contextPanelPinned`, `leftRailWidth`, and `contextPanelWidth`.
- `StudioView.tsx` still renders exactly one `WritingView`.
- Desktop Studio remains a three-panel shell.
- Collapsed left rail renders at fixed width `64`.
- Docked context panel width is driven by `contextPanelWidth`.
- `StudioCommandBar.tsx` and `StudioContextPanel.tsx` no longer rely on Stage 5 boolean store selectors.
- Small-screen `Project` and `Context` buttons open overlay drawers through adaptive modes.
- Existing mobile/tablet drawer tests still pass.
- Stage 6 focused tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Proceed to Stage 7 only when all above checks pass and the shared verification gate in this roadmap also passes.

### Stage 7 Exit Criteria

- `contextPanelMode` supports exact values `docked`, `overlay`, and `closed`.
- `studio-layout-v1` persists only layout preferences.
- Invalid persisted widths are clamped back to bounded defaults.
- `parseStoredStudioLayout()` provides a deterministic hydration seam for store tests.
- Overlay context mode renders without unmounting the center `WritingView`.
- `BottomUtilityLayer` remains owned by `Workspace.tsx` only.
- Stage 7 focused tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
cd frontend; cmd /c npm.cmd run test -- studioStore
```

Proceed to Stage 8 only when all above checks pass and the shared verification gate in this roadmap also passes.

### Stage 8 Exit Criteria

- `StudioCommandBar` exposes a `Layout` control.
- `StudioCommandBar` exposes a desktop-visible `Rail` collapse/expand control.
- `StudioCommandBar` exposes deterministic `Rail Width` and `Panel Width` controls.
- `StudioContextPanel` exposes `Pin`, `Dock`, `Overlay`, and `Close` controls.
- `resetLayout()` restores the exact default values from the delta spec.
- Command bar panel switches do not navigate away from `/workspace/:projectId/studio`.
- Existing Studio panel components continue to load through the same frontend services and hooks.
- Stage 8 focused tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
cd frontend; cmd /c npm.cmd run test -- WorkspaceShell
```

The adaptive Studio delta is complete only when Stage 8 and the shared verification gate both pass.

## Scope Lock

- Frontend UI/UX only.
- Existing Studio route only.
- Existing services only.
- Existing backend endpoints only.
- Existing `BottomUtilityLayer` ownership only.
- Do not install or use floating-window drag libraries for this delta.
- Do not create new route families.
