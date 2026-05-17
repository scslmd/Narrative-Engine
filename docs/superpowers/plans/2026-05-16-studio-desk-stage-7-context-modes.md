# Studio Desk Stage 7 Context Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add deterministic context-panel modes and persisted Studio layout preferences without changing any backend or route behavior.

**Architecture:** Stage 7 keeps the Stage 6 adaptive shell and adds local-only persistence plus overlay and closed context modes. The center `WritingView` stays mounted and `BottomUtilityLayer` remains workspace-owned.

**Tech Stack:** React 18, TypeScript, Zustand, Tailwind CSS, Testing Library, Vitest.

---

## Contract

| Task | Responsible file | Purpose |
| --- | --- | --- |
| S7-T001 | `frontend/src/stores/studioStore.ts` | Add `studio-layout-v1` persistence and bounded hydration |
| S7-T002 | `frontend/src/views/StudioView.tsx` | Render `overlay` and `closed` context modes on top of Stage 6 shell |
| S7-T003 | `frontend/src/stores/studioStore.test.ts` | Add deterministic store persistence tests |
| S7-T004 | `frontend/src/views/StudioView.test.tsx` | Add overlay/closed mode render tests |

## Guardrails

- Do not modify any backend service file.
- Do not modify `frontend/src/components/BottomUtilityLayer.tsx`.
- Do not add a new persistent storage library.
- Persist layout preferences only; do not persist `activePanel`.
- Keep the route `/workspace/:projectId/studio` unchanged.
- Add an explicit hydration seam in `studioStore.ts`; do not require test code to depend on module reload timing.

## Tasks

### S7-T001: Persist Adaptive Layout Preferences

**Responsible file:** `frontend/src/stores/studioStore.ts`

**Dependencies:** Stage 6 complete

- [x] Add these exact file-level constants:

```ts
const STUDIO_LAYOUT_STORAGE_KEY = 'studio-layout-v1';
const DEFAULT_LEFT_RAIL_WIDTH = 224;
const DEFAULT_CONTEXT_PANEL_WIDTH = 416;
const MIN_LEFT_RAIL_WIDTH = 192;
const MAX_LEFT_RAIL_WIDTH = 320;
const MIN_CONTEXT_PANEL_WIDTH = 320;
const MAX_CONTEXT_PANEL_WIDTH = 520;
```

- [x] Add these exact exported helper types and functions:

```ts
export interface PersistedStudioLayout {
  leftRailMode: StudioRailMode;
  contextPanelMode: StudioContextMode;
  contextPanelPinned: boolean;
  leftRailWidth: number;
  contextPanelWidth: number;
}

export function clampStudioWidth(value: unknown, min: number, max: number, fallback: number): number
export function parseStoredStudioLayout(raw: string | null): PersistedStudioLayout | null
```

- [x] `clampStudioWidth` must return `fallback` when `value` is not a finite number.
- [x] `parseStoredStudioLayout` must:
  - return `null` when `raw` is `null`
  - return `null` when `raw` is invalid JSON
  - return `null` when `leftRailMode` is not one of `expanded | collapsed | overlay`
  - return `null` when `contextPanelMode` is not one of `docked | overlay | closed`
  - return a sanitized `PersistedStudioLayout` when parsing succeeds
  - sanitize `leftRailWidth` through `clampStudioWidth(..., 192, 320, 224)`
  - sanitize `contextPanelWidth` through `clampStudioWidth(..., 320, 520, 416)`

- [x] Persist exactly these fields to `localStorage` after each state change that mutates them:
  - `leftRailMode`
  - `contextPanelMode`
  - `contextPanelPinned`
  - `leftRailWidth`
  - `contextPanelWidth`

- [x] Implement one local helper in `studioStore.ts` that writes the persisted layout object to `localStorage`.

- [x] Call that one local persistence helper from:
  - `setLeftRailMode`
  - `setContextPanelMode`
  - `setContextPanelPinned`
  - `setLeftRailWidth`
  - `setContextPanelWidth`
  - `resetLayout`

- [x] Do not persist `activePanel`.

- [x] Hydrate once during store initialization by calling:

```ts
parseStoredStudioLayout(localStorage.getItem('studio-layout-v1'))
```

- [x] If parsing fails, ignore the stored value and use defaults.

- [x] Keep the hydrated state merge bounded to these fields only:
  - `leftRailMode`
  - `contextPanelMode`
  - `contextPanelPinned`
  - `leftRailWidth`
  - `contextPanelWidth`

- [x] Keep `resetLayout()` responsible for restoring defaults and writing the new defaults back to storage.

- [x] Verify typecheck.

### S7-T002: Render Overlay And Closed Context Modes

**Responsible file:** `frontend/src/views/StudioView.tsx`

**Dependencies:** S7-T001

- [x] Preserve the Stage 6 docked desktop grid behavior unchanged when `contextPanelMode === 'docked'`.

- [x] When `contextPanelMode === 'closed'`:
  - do not render the desktop third column content
  - do not render the desktop third column border
  - keep the center `WritingView` mounted

- [x] When `contextPanelMode === 'overlay'` on desktop:
  - do not render the docked third column content
  - render one right-aligned absolute overlay panel above the center editor
  - use exact class substring `absolute right-4 top-4 bottom-4 z-30`
  - set inline width style to `contextPanelWidth`
  - render `StudioContextPanel` inside the overlay container

- [x] When `contextPanelMode === 'overlay'`, also render one backdrop button with exact `aria-label="Close Studio context overlay"`.

- [x] Clicking the backdrop must call `setContextPanelMode('closed')`.

- [x] Do not render an additional job tray or runtime bar.

- [x] Verify typecheck.

### S7-T003: Add Store Persistence Tests

**Responsible file:** `frontend/src/stores/studioStore.test.ts`

**Dependencies:** S7-T001

- [x] Create this new test file.

- [x] Add deterministic tests for:
  - default state values when storage is empty
  - `parseStoredStudioLayout()` returning sanitized `leftRailMode`, `contextPanelMode`, `contextPanelPinned`, `leftRailWidth`, and `contextPanelWidth`
  - `parseStoredStudioLayout()` returning `null` for invalid JSON
  - `parseStoredStudioLayout()` clamping stored width values outside bounds back into legal ranges
  - `resetLayout()` restoring the exact default values
  - `openPanel('review')` reopening `contextPanelMode` from `closed` to `docked`
  - setter persistence writing only the five layout fields and never `activePanel`

- [x] Use `localStorage.clear()` in `beforeEach`.

- [x] Do not mount React components in this file; test the exported helpers and the store state directly.

- [x] Verify focused tests.

```powershell
cd frontend; cmd /c npm.cmd run test -- studioStore
```

Expected: exits `0`.

### S7-T004: Add Studio Overlay/Closed Mode Tests

**Responsible file:** `frontend/src/views/StudioView.test.tsx`

**Dependencies:** S7-T002

- [x] Add a test that sets store state to `contextPanelMode: 'overlay'` before render and asserts the overlay close button with `aria-label="Close Studio context overlay"` exists.

- [x] Add a test that clicks the overlay close button and asserts `useStudioStore.getState().contextPanelMode === 'closed'`.

- [x] Add a test that sets store state to `contextPanelMode: 'closed'`, renders `StudioView`, clicks `Inspect`, and asserts the inspect guidance text becomes visible.

- [x] Keep existing Stage 6 tests intact unless they referenced removed boolean fields.

## Final Verification

```powershell
cd frontend; cmd /c npm.cmd run lint
cd frontend; cmd /c npm.cmd run typecheck
cd frontend; cmd /c npm.cmd run build
cd frontend; cmd /c npm.cmd run test -- studioStore
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Expected: all commands exit `0`.

## Stage 7 To Stage 8 Precedence

Do not begin Stage 8 until both of these are true:

1. The Stage 7 focused verification block below exits `0`:

```powershell
cd frontend; cmd /c npm.cmd run test -- studioStore
cd frontend; cmd /c npm.cmd run test -- StudioView
```

2. The full Stage 7 final verification block above exits `0` in the same workspace state.

## Stage 7 Pass Criteria

Stage 7 is complete only when all of these are true:

- `studio-layout-v1` persists only layout preferences.
- Invalid stored values do not break Studio initialization.
- `parseStoredStudioLayout()` provides a deterministic hydration seam for tests.
- Overlay context mode renders above the editor without replacing `WritingView`.
- Closed context mode can be reopened by command selection through `openPanel`.
- Focused tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- studioStore
cd frontend; cmd /c npm.cmd run test -- StudioView
```
