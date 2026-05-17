# Studio Desk Stage 8 Layout Controls And Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Expose deterministic mobile and desktop layout controls in the command bar and context panel header so users can reset, pin, dock, overlay, close, collapse, and resize the adaptive Studio shell without route changes.

**Architecture:** Stage 8 adds only UI controls and tests on top of the Stage 7 adaptive shell. Existing Studio panels, routes, services, and backend APIs remain unchanged.

**Tech Stack:** React 18, TypeScript, Zustand, Tailwind CSS, Testing Library, Vitest.

---

## Contract

| Task | Responsible file | Purpose |
| --- | --- | --- |
| S8-T001 | `frontend/src/components/studio/StudioCommandBar.tsx` | Add deterministic mobile overlay controls, desktop rail controls, width controls, and reset |
| S8-T002 | `frontend/src/components/studio/StudioContextPanel.tsx` | Add exact header controls for pin, dock, overlay, and close |
| S8-T003 | `frontend/src/views/StudioView.test.tsx` | Add layout-control interaction tests |
| S8-T004 | `frontend/src/components/WorkspaceShell.test.tsx` | Re-assert Studio shell navigation remains unchanged |

## Guardrails

- Do not add menu popovers, dropdown frameworks, or modal flows.
- Do not modify `frontend/src/routes.ts`.
- Do not modify any panel content component under `frontend/src/components/studio/*Panel.tsx` other than `StudioContextPanel.tsx`.
- The `Layout` control in this stage means reset only; do not invent additional presets.
- No command bar action may navigate away from `/workspace/:projectId/studio`.
- Every new width control must set exact numeric values; do not introduce drag resizing in this stage.

## Tasks

### S8-T001: Add Layout Reset, Mobile Overlay, Desktop Rail, And Width Controls

**Responsible file:** `frontend/src/components/studio/StudioCommandBar.tsx`

**Dependencies:** Stage 7 complete

- [x] Keep the existing command buttons and `commands` array unchanged.
- [x] Stage 8 does not create `StudioCommandBar.test.tsx`; all command-bar assertions in this stage must be exercised through `frontend/src/views/StudioView.test.tsx`.

- [x] Add these exact store selectors:
  - `leftRailMode`
  - `contextPanelMode`
  - `leftRailWidth`
  - `contextPanelWidth`
  - `setLeftRailMode`
  - `setContextPanelMode`
  - `setLeftRailWidth`
  - `setContextPanelWidth`
  - `resetLayout`

- [x] Keep the existing small-screen `Project` and `Context` buttons using class substring `xl:hidden` only.

- [x] Make the small-screen `Project` button use this exact click behavior:

```ts
onClick={() => {
  setLeftRailMode(leftRailMode === 'overlay' ? 'collapsed' : 'overlay');
}}
```

- [x] Make the small-screen `Context` button use this exact click behavior:

```ts
onClick={() => {
  setContextPanelMode(contextPanelMode === 'overlay' ? 'closed' : 'overlay');
}}
```

- [x] Add one desktop-only button labeled exactly `Rail`.

- [x] The `Rail` button must use class substring `hidden xl:inline-flex`.

- [x] Reflect the desktop rail state on the `Rail` button with exact behavior:

```tsx
aria-pressed={leftRailMode !== 'collapsed'}
```

- [x] Make the desktop `Rail` button use this exact click behavior:

```ts
onClick={() => {
  setLeftRailMode(leftRailMode === 'collapsed' ? 'expanded' : 'collapsed');
}}
```

- [x] Add one desktop-only button labeled exactly `Rail Width`.

- [x] The `Rail Width` button must use class substring `hidden xl:inline-flex`.

- [x] Reflect the current left rail width on the `Rail Width` button with exact behavior:

```tsx
aria-pressed={leftRailWidth === 320}
```

- [x] Make `Rail Width` use this exact click behavior:

```ts
onClick={() => {
  if (leftRailMode === 'collapsed') {
    setLeftRailMode('expanded');
    setLeftRailWidth(224);
    return;
  }

  setLeftRailWidth(leftRailWidth === 224 ? 320 : 224);
}}
```

- [x] Add one desktop-only button labeled exactly `Panel Width`.

- [x] The `Panel Width` button must use class substring `hidden xl:inline-flex`.

- [x] Reflect the current context width on the `Panel Width` button with exact behavior:

```tsx
aria-pressed={contextPanelWidth === 520}
```

- [x] Make `Panel Width` use this exact click behavior:

```ts
onClick={() => {
  setContextPanelWidth(contextPanelWidth === 416 ? 520 : 416);
}}
```

- [x] Add one button labeled exactly `Layout`.

- [x] The `Layout` button must call `resetLayout` directly.

- [x] Add exact `aria-label="Reset Studio layout"` to the `Layout` button.

- [x] `Layout` may remain visible at all breakpoints.

- [x] Verify typecheck.

### S8-T002: Add Context Header Layout Controls

**Responsible file:** `frontend/src/components/studio/StudioContextPanel.tsx`

**Dependencies:** S8-T001

- [x] Keep the existing `panelLabels` record and `renderPanel()` switch unchanged.

- [x] Add these exact store selectors:
  - `contextPanelMode`
  - `contextPanelPinned`
  - `setContextPanelMode`
  - `setContextPanelPinned`

- [x] Replace the current single close button header actions with four exact buttons in this order:
  1. `Pin`
  2. `Dock`
  3. `Overlay`
  4. `Close`

- [x] Button behavior must be exactly:
  - `Pin`: toggles `contextPanelPinned`
  - `Dock`: calls `setContextPanelMode('docked')`
  - `Overlay`: calls `setContextPanelMode('overlay')`
  - `Close`: calls `setContextPanelMode('closed')`

- [x] Add exact `aria-pressed` behavior:
  - `Pin`: `aria-pressed={contextPanelPinned}`
  - `Dock`: `aria-pressed={contextPanelMode === 'docked'}`
  - `Overlay`: `aria-pressed={contextPanelMode === 'overlay'}`

- [x] `Close` does not use `aria-pressed`.

- [x] Do not hide these controls based on the active panel key.

- [x] Keep the panel body `div` structure intact so existing panel components continue to render without prop changes.

### S8-T003: Add Layout Control Tests

**Responsible file:** `frontend/src/views/StudioView.test.tsx`

**Dependencies:** S8-T001, S8-T002

- [x] Add a test that clicks `Layout` after mutating the store away from defaults and asserts the store resets to:

```ts
activePanel: 'suggestions'
leftRailMode: 'expanded'
contextPanelMode: 'docked'
contextPanelPinned: true
leftRailWidth: 224
contextPanelWidth: 416
```

- [x] Add a test that clicks `Overlay` in the context header and asserts `useStudioStore.getState().contextPanelMode === 'overlay'`.

- [x] Add a test that clicks `Dock` after entering overlay mode and asserts `useStudioStore.getState().contextPanelMode === 'docked'`.

- [x] Add a test that clicks `Pin` and asserts `useStudioStore.getState().contextPanelPinned` toggles.

- [x] Add a test that clicks `Close` and asserts `useStudioStore.getState().contextPanelMode === 'closed'`.

- [x] Add a test that clicks desktop `Rail` and asserts `useStudioStore.getState().leftRailMode === 'collapsed'`.

- [x] Add a test that clicks desktop `Rail Width` from default state and asserts `useStudioStore.getState().leftRailWidth === 320`.

- [x] Add a test that clicks desktop `Panel Width` from default state and asserts `useStudioStore.getState().contextPanelWidth === 520`.

- [x] Add a test that clicks small-screen `Project` and asserts `useStudioStore.getState().leftRailMode === 'overlay'`.

- [x] Add a test that clicks small-screen `Context` and asserts `useStudioStore.getState().contextPanelMode === 'overlay'`.

- [x] In `StudioView.test.tsx`, query these buttons with exact role/name pairs:
  - `getByRole('button', { name: 'Rail' })`
  - `getByRole('button', { name: 'Rail Width' })`
  - `getByRole('button', { name: 'Panel Width' })`
  - `getByRole('button', { name: 'Project' })`
  - `getByRole('button', { name: 'Context' })`

- [x] Do not assert CSS visibility for desktop-only or mobile-only buttons in jsdom. Assert only that the button exists and that clicking it changes store state as specified above.

### S8-T004: Re-Assert WorkspaceShell Navigation Stability

**Responsible file:** `frontend/src/components/WorkspaceShell.test.tsx`

**Dependencies:** S8-T001

- [x] Keep all current Studio-writing-stage nav expectations intact.

- [x] Add one explicit assertion to the existing `renders Studio and Writing when mode is studio` test that the buttons count remains `2` after the Stage 8 delta.

- [x] Do not add assertions about any new route labels because Stage 8 adds no new routes.

## Final Verification

```powershell
cd frontend; cmd /c npm.cmd run lint
cd frontend; cmd /c npm.cmd run typecheck
cd frontend; cmd /c npm.cmd run build
cd frontend; cmd /c npm.cmd run test -- StudioView
cd frontend; cmd /c npm.cmd run test -- WorkspaceShell
```

Expected: all commands exit `0`.

## Stage 8 Pass Criteria

Stage 8 is complete only when all of these are true:

- `StudioCommandBar` exposes a deterministic `Layout` reset button.
- `StudioCommandBar` exposes a desktop-visible `Rail` collapse/expand control.
- `StudioCommandBar` exposes deterministic `Rail Width` and `Panel Width` controls that write exact numeric values.
- `StudioContextPanel` exposes `Pin`, `Dock`, `Overlay`, and `Close` controls.
- `resetLayout()` restores the exact default adaptive state.
- Studio navigation stays on `/workspace/:projectId/studio` during command and layout control use.
- Focused tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
cd frontend; cmd /c npm.cmd run test -- WorkspaceShell
```
