# Studio Desk Adaptive 3-Panel Delta Spec

Date: 2026-05-16
Status: Proposed post-Stage-5 delta
Supersedes for implementation direction: `docs/superpowers/specs/2026-05-16-floating-panels-implementation.md`

## Goal

Refine the implemented Stage 1-5 Studio experience into a cleaner adaptive three-panel workspace without introducing a floating window manager. The result keeps the existing Studio route, the stable center writing surface, and the existing backend/frontend service contracts while adding bounded layout flexibility.

## Current Baseline

These are already assumed to exist:

- `/workspace/:projectId/studio`
- Left project rail
- Center writing surface
- Right context panel
- Mobile/tablet drawer behavior
- Existing Studio panel set: `suggestions`, `ideas`, `characters`, `worldBible`, `relationships`, `generation`, `review`, `inspect`, `notes`, `jobs`
- Existing workspace-owned `BottomUtilityLayer`

No task in this delta may remove or replace the above architecture.

## What Changes

### Keep

- Three-panel desktop shell
- Stable center manuscript/editor surface
- Drawer behavior on smaller screens
- Existing Studio panel components and existing backend APIs
- Existing workspace-owned bottom utility tray

### Add

- Adaptive left rail modes: `expanded`, `collapsed`, `overlay`
- Adaptive right context modes: `docked`, `overlay`, `closed`
- Bounded persistent width preferences for left and right side panels
- Context pin behavior so command changes do not auto-close the right panel
- One reset action that restores the default Studio layout
- Cleaner command bar and context header controls for layout behavior

### Explicitly Reject

These are not part of this delta:

- Freeform draggable windows
- Arbitrary `x`/`y` panel coordinates
- Multiple simultaneous floating context windows
- Per-panel z-index stacks
- Duplicate runtime/status bar inside Studio
- New backend endpoints
- Route changes beyond the existing Studio route

## Final Interaction Model

### Desktop

The Studio remains a three-panel shell:

```text
[ Left Rail ] [ Stable Center Editor ] [ Right Context Panel ]
```

Behavior:

- Left rail supports `expanded` and `collapsed` widths.
- Right context panel supports `docked` width resizing and `overlay` mode.
- Center editor remains mounted and visually central in all desktop modes.
- `BottomUtilityLayer` remains owned by `Workspace.tsx` and is not duplicated.

### Tablet / Mobile

- Existing drawer behavior remains the base.
- `overlay` context mode reuses the current small-screen drawer pattern instead of introducing a second mobile model.
- There must still be exactly one mounted `WritingView` in `StudioView.tsx`.

## Store Model Delta

`frontend/src/stores/studioStore.ts` should evolve from simple booleans to bounded layout state.

Use these exact fields:

```ts
export type StudioRailMode = 'expanded' | 'collapsed' | 'overlay';
export type StudioContextMode = 'docked' | 'overlay' | 'closed';

interface StudioState {
  activePanel: StudioPanelKey;
  leftRailMode: StudioRailMode;
  contextPanelMode: StudioContextMode;
  contextPanelPinned: boolean;
  leftRailWidth: number;
  contextPanelWidth: number;
  setActivePanel: (panel: StudioPanelKey) => void;
  setLeftRailMode: (mode: StudioRailMode) => void;
  setContextPanelMode: (mode: StudioContextMode) => void;
  setContextPanelPinned: (pinned: boolean) => void;
  setLeftRailWidth: (width: number) => void;
  setContextPanelWidth: (width: number) => void;
  openPanel: (panel: StudioPanelKey) => void;
  resetLayout: () => void;
}
```

Exact width bounds:

- `leftRailWidth`: min `192`, max `320`, default `224`
- `contextPanelWidth`: min `320`, max `520`, default `416`

`openPanel(panel)` rules:

- always set `activePanel = panel`
- if `contextPanelMode === 'closed'`, set it to `docked`
- never mutate `contextPanelPinned`

`resetLayout()` must restore:

```ts
leftRailMode = 'expanded'
contextPanelMode = 'docked'
contextPanelPinned = true
leftRailWidth = 224
contextPanelWidth = 416
activePanel = 'suggestions'
```

## Persistence Rules

Persist only layout preferences, not content state.

Exact storage key:

```text
studio-layout-v1
```

Persist exactly these fields:

- `leftRailMode`
- `contextPanelMode`
- `contextPanelPinned`
- `leftRailWidth`
- `contextPanelWidth`

Do not persist:

- `activePanel`
- any manuscript selection
- any query data
- any generated content

Load behavior:

- read storage after store creation
- validate persisted widths against min/max bounds before use
- if the persisted value is missing or invalid, use the default value

## Layout Rules

### Left Rail

- `expanded`: render full rail at `leftRailWidth`
- `collapsed`: render icon/compact rail at fixed width `64`
- `overlay`: desktop-only temporary overlay rail; used only when explicitly toggled from collapsed state

### Right Context Panel

- `docked`: render as the right column at `contextPanelWidth`
- `overlay`: render above the center editor, right-aligned, with backdrop and close control
- `closed`: remove from desktop flow but keep command bar access

### Command Routing

Studio command buttons continue to switch `activePanel`.

Additional exact controls:

- `Layout` button in `StudioCommandBar`
- `Pin` toggle in the context panel header
- `Dock` button in the context panel header
- `Overlay` button in the context panel header
- `Close` button in the context panel header

Behavior rules:

- Clicking a command when `contextPanelMode === 'closed'` opens that panel in `docked` mode.
- Clicking a command when `contextPanelMode === 'overlay'` swaps the content in place and keeps overlay mode.
- `Pin` affects whether explicit close actions are needed; it does not alter routing or APIs.
- No command may navigate away from `/workspace/:projectId/studio`.

## Visual Direction

This is a utility refinement, not a visual reinvention.

- Keep the existing Studio visual language.
- Prefer quieter chrome and clearer hierarchy over novelty.
- Reserve stronger emphasis for the active command and active panel only.
- Do not introduce window-manager visuals such as stacked cards, floating shadows across the canvas, or snap grids.

## Implementation Shape

Serial post-implementation stages:

1. Stage 6: adaptive shell foundation
2. Stage 7: context modes and persistence
3. Stage 8: command/header polish and layout reset

## Verification Requirements

Every stage must pass:

```powershell
cd frontend; cmd /c npm.cmd run lint
cd frontend; cmd /c npm.cmd run typecheck
cd frontend; cmd /c npm.cmd run build
cd frontend; cmd /c npm.cmd run test
```

Expected: all commands exit `0`.

## API Alignment Constraints

- Frontend only
- Reuse existing services, hooks, and route contracts
- No backend route additions
- No query key renames unless required by local Studio layout state only
- No changes to inspect deep-link route behavior
- No changes to `BottomUtilityLayer` ownership in `Workspace.tsx`
