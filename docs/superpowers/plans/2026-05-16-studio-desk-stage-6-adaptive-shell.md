# Studio Desk Stage 6 Adaptive Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Replace the Stage 5 boolean drawer shell with a bounded adaptive three-panel desktop shell while keeping the same Studio route and one stable center writing surface.

**Architecture:** Stage 6 updates only local Studio layout state, the Studio view shell, the left rail presentation, and Studio view tests. No backend contracts, route contracts, or panel content services change.

**Tech Stack:** React 18, TypeScript, Zustand, Tailwind CSS, Testing Library, Vitest.

---

## Contract

| Task | Responsible file | Purpose |
| --- | --- | --- |
| S6-T001 | `frontend/src/stores/studioStore.ts` | Replace boolean rail/context state with bounded adaptive layout state |
| S6-T002 | `frontend/src/components/studio/StudioProjectRail.tsx` | Add compact rail mode for collapsed desktop width |
| S6-T003 | `frontend/src/views/StudioView.tsx` | Render the adaptive desktop shell with exactly one `WritingView` |
| S6-T004 | `frontend/src/views/StudioView.test.tsx` | Replace Stage 5 boolean assertions with adaptive shell assertions |
| S6-T005 | `frontend/src/components/studio/StudioCommandBar.tsx` | Migrate mobile Studio controls onto adaptive layout state |
| S6-T006 | `frontend/src/components/studio/StudioContextPanel.tsx` | Migrate panel close control onto adaptive layout state |

## Guardrails

- Do not modify `frontend/src/views/Workspace.tsx`.
- Do not modify `frontend/src/components/BottomUtilityLayer.tsx`.
- Do not add new routes.
- Do not add any drag-and-drop or floating-window library.
- `StudioView.tsx` must continue to mount exactly one `WritingView`.
- Preserve `StudioPanelKey` literals exactly as currently defined.
- Stage 6 must remain typecheck-safe after `S6-T001`; do not leave dependent Studio files broken between tasks.

## Tasks

### S6-T001: Replace Boolean Layout State With Adaptive State

**Responsible file:** `frontend/src/stores/studioStore.ts`

**Dependencies:** Stage 5 complete

- [x] Replace `leftRailOpen` and `contextPanelOpen` with these exact exported types:

```ts
export type StudioRailMode = 'expanded' | 'collapsed' | 'overlay';
export type StudioContextMode = 'docked' | 'overlay' | 'closed';
```

- [x] Replace the store interface with these exact fields and methods:

```ts
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
  toggleLeftRail: () => void;
  toggleContextPanel: () => void;
  closeDrawers: () => void;
}
```

- [x] Use these exact default values:

```ts
activePanel: 'suggestions'
leftRailMode: 'expanded'
contextPanelMode: 'docked'
contextPanelPinned: true
leftRailWidth: 224
contextPanelWidth: 416
```

- [x] Clamp widths inside setters with these exact bounds:
  - `leftRailWidth`: `192` to `320`
  - `contextPanelWidth`: `320` to `520`

- [x] Implement `openPanel(panel)` with this exact behavior:

```ts
openPanel: (activePanel) =>
  set((state) => ({
    activePanel,
    contextPanelMode: state.contextPanelMode === 'closed' ? 'docked' : state.contextPanelMode,
  }))
```

- [x] Implement `resetLayout()` to restore these exact values:

```ts
activePanel: 'suggestions'
leftRailMode: 'expanded'
contextPanelMode: 'docked'
contextPanelPinned: true
leftRailWidth: 224
contextPanelWidth: 416
```

- [x] Keep temporary compatibility helpers in Stage 6 so typecheck stays green while `S6-T005` and `S6-T006` migrate consumers:

```ts
toggleLeftRail: () =>
  set((state) => ({
    leftRailMode: state.leftRailMode === 'overlay' ? 'collapsed' : 'overlay',
  })),
toggleContextPanel: () =>
  set((state) => ({
    contextPanelMode: state.contextPanelMode === 'overlay' ? 'closed' : 'overlay',
  })),
closeDrawers: () =>
  set({
    leftRailMode: 'collapsed',
    contextPanelMode: 'closed',
  }),
```

- [x] Do not remove these compatibility helpers in Stage 6. They may remain unused after consumer migration, but they must stay available until a later cleanup stage.

- [x] Verify typecheck.

```powershell
cd frontend; cmd /c npm.cmd run typecheck
```

Expected: exits `0`.

### S6-T002: Add Compact Left Rail Presentation

**Responsible file:** `frontend/src/components/studio/StudioProjectRail.tsx`

**Dependencies:** S6-T001

- [x] Add this exact optional prop:

```ts
compact?: boolean;
```

- [x] Preserve `projectId: string`.

- [x] When `compact` is falsy, keep the existing rail labels and footer links.
- [x] When `compact` is truthy:
  - render the same rail items in the same order
  - keep the same `openPanel(item.panel)` behavior
  - hide visible text labels for rail item names
  - keep each button accessible by setting `aria-label={item.label}`
  - hide the footer links section entirely
  - render the rail root with exact fixed width class substring `w-16`

- [x] Add an exact class branch for the compact button layout:

```tsx
compact ? 'justify-center px-0 py-2' : 'gap-2 rounded-lg px-2.5 py-2'
```

- [x] Do not change `railItems` labels or panel mappings.

- [x] Verify typecheck.

### S6-T003: Render Adaptive Desktop Shell

**Responsible file:** `frontend/src/views/StudioView.tsx`

**Dependencies:** S6-T001, S6-T002

- [x] Replace boolean drawer selectors with these exact store selectors:
  - `leftRailMode`
  - `contextPanelMode`
  - `leftRailWidth`
  - `contextPanelWidth`

- [x] Keep this guard unchanged:

```tsx
if (!projectId) {
  return <div className="text-sm text-slate-500">No project selected.</div>;
}
```

- [x] Keep `<StudioCommandBar />` as the first child inside the outer shell.

- [x] Render exactly one center editor block with this exact child:

```tsx
<main className="min-h-0 overflow-hidden bg-[var(--bg-primary)]">
  <WritingView />
</main>
```

- [x] For desktop (`xl` and above), render a three-column container whose `style.gridTemplateColumns` uses these exact rules:
  - if `leftRailMode === 'expanded'`, first column is ``${leftRailWidth}px``
  - if `leftRailMode === 'collapsed'`, first column is `64px`
  - if `contextPanelMode === 'docked'`, third column is ``${contextPanelWidth}px``
  - if `contextPanelMode !== 'docked'`, third column is `0px`

- [x] Use the exact desktop grid class substring:

```tsx
xl:grid-cols-[minmax(0,0)_minmax(0,1fr)_minmax(0,0)]
```

- [x] Render `StudioProjectRail` in the first desktop column with:
  - `compact={leftRailMode === 'collapsed'}`
  - `projectId={projectId}`

- [x] Render `StudioContextPanel` in the third desktop column only when `contextPanelMode === 'docked'`.

- [x] Keep the existing small-screen absolute drawer wrappers in place for now, but map them from adaptive modes with these exact rules:
  - left mobile drawer is open only when `leftRailMode === 'overlay'`
  - right mobile/context drawer is open only when `contextPanelMode === 'overlay'`

- [x] Replace the backdrop close behavior so it does not depend on legacy store helpers:

```tsx
onClick={() => {
  setLeftRailMode('collapsed');
  setContextPanelMode('closed');
}}
```

- [x] Add no new resize listeners, no second `WritingView`, and no floating window containers.

- [x] Verify typecheck.

### S6-T004: Update StudioView Adaptive Shell Tests

**Responsible file:** `frontend/src/views/StudioView.test.tsx`

**Dependencies:** S6-T001, S6-T003

- [x] Replace the `afterEach` store reset state with these exact values:

```ts
useStudioStore.setState({
  activePanel: 'suggestions',
  leftRailMode: 'expanded',
  contextPanelMode: 'docked',
  contextPanelPinned: true,
  leftRailWidth: 224,
  contextPanelWidth: 416,
});
```

- [x] Remove tests that assert `leftRailOpen`, `contextPanelOpen`, or `closeDrawers`.

- [x] Add these deterministic assertions:
  - rendering `StudioView` still shows `Studio Desk`
  - `Studio project map` navigation still renders
  - setting store state to `leftRailMode: 'collapsed'` before render still leaves the project map accessible
  - clicking `Generate` still opens the compact generation panel
  - setting store state to `contextPanelMode: 'closed'` before clicking `Review` causes `openPanel` to reopen the context area so `Findings` becomes visible
  - clicking the small-screen `Project` button sets `leftRailMode` to `'overlay'`
  - clicking the small-screen `Context` button sets `contextPanelMode` to `'overlay'`
  - clicking the backdrop close button sets `leftRailMode` to `'collapsed'` and `contextPanelMode` to `'closed'`

- [x] Do not add CSS-visibility assertions that depend on real browser layout.

### S6-T005: Migrate StudioCommandBar To Adaptive Layout State

**Responsible file:** `frontend/src/components/studio/StudioCommandBar.tsx`

**Dependencies:** S6-T001

- [x] Remove direct reliance on `toggleLeftRail` and `toggleContextPanel`.

- [x] Add these exact store selectors:
  - `leftRailMode`
  - `contextPanelMode`
  - `setLeftRailMode`
  - `setContextPanelMode`

- [x] Keep the existing `Project` and `Context` buttons visible only below `xl`.

- [x] Preserve the existing `commands` array and `openPanel(command.panel)` behavior unchanged.

- [x] Make the `Project` button use this exact click behavior:

```ts
onClick={() => {
  setLeftRailMode(leftRailMode === 'overlay' ? 'collapsed' : 'overlay');
}}
```

- [x] Make the `Context` button use this exact click behavior:

```ts
onClick={() => {
  setContextPanelMode(contextPanelMode === 'overlay' ? 'closed' : 'overlay');
}}
```

- [x] Do not add a `Layout` button in Stage 6.

- [x] Verify typecheck.

### S6-T006: Migrate StudioContextPanel Close Control

**Responsible file:** `frontend/src/components/studio/StudioContextPanel.tsx`

**Dependencies:** S6-T001

- [x] Remove direct reliance on `setContextPanelOpen`.

- [x] Add these exact store selectors:
  - `contextPanelMode`
  - `setContextPanelMode`

- [x] Keep the existing `panelLabels` record and `renderPanel()` switch unchanged.

- [x] Keep the existing header title text unchanged.

- [x] Keep the existing `Close panel` button label unchanged.

- [x] Make the close button use this exact behavior:

```ts
onClick={() => setContextPanelMode('closed')}
```

- [x] Do not add `Pin`, `Dock`, or `Overlay` controls in Stage 6.

- [x] Verify typecheck.

## Final Verification

```powershell
cd frontend; cmd /c npm.cmd run lint
cd frontend; cmd /c npm.cmd run typecheck
cd frontend; cmd /c npm.cmd run build
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Expected: all commands exit `0`.

## Stage 6 To Stage 7 Precedence

Do not begin Stage 7 until both of these are true:

1. The focused Stage 6 test below exits `0`:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
```

2. The full Stage 6 final verification block above exits `0` in the same workspace state.

## Stage 6 Pass Criteria

Stage 6 is complete only when all of these are true:

- `studioStore.ts` exposes bounded adaptive layout state.
- `StudioProjectRail.tsx` supports compact mode without changing panel mappings.
- `StudioView.tsx` keeps one mounted `WritingView` and a three-panel desktop shell.
- Closed docked context behavior reopens deterministically through `openPanel`.
- `StudioCommandBar.tsx` and `StudioContextPanel.tsx` no longer depend on Stage 5 boolean store fields.
- Small-screen `Project` and `Context` controls open overlay drawers through adaptive modes.
- Focused test passes:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
```
