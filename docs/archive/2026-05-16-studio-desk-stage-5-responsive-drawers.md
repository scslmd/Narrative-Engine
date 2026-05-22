# Studio Desk Stage 5 Responsive Drawers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make Studio usable on tablet and mobile by turning the project rail and context panel into controlled drawers below desktop width.

**Architecture:** Keep desktop grid behavior. Add responsive controls in `StudioView`, use the existing `studioStore` open/closed state, and update shell tests to verify drawer buttons and accessible labels.

**Tech Stack:** React, Zustand, Tailwind CSS responsive classes, Testing Library.

---

## Contract

| Task | Responsible file | Purpose |
| --- | --- | --- |
| S5-T001 | `frontend/src/stores/studioStore.ts` | Add drawer close helpers |
| S5-T002 | `frontend/src/views/StudioView.tsx` | Responsive grid and overlay drawers |
| S5-T003 | `frontend/src/components/studio/StudioCommandBar.tsx` | Add mobile rail/context buttons |
| S5-T004 | `frontend/src/views/StudioView.test.tsx` | Test drawer controls |

## Guardrails

- Do not introduce a new responsive state store.
- Do not use window resize listeners.
- Do not remove desktop three-column layout.
- Do not hide command bar on mobile.

## Tasks

### S5-T001: Store Drawer Helpers

**Responsible file:** `frontend/src/stores/studioStore.ts`

- [x] Add methods:

```ts
toggleLeftRail: () => void;
toggleContextPanel: () => void;
closeDrawers: () => void;
```

- [x] Implement:

```ts
toggleLeftRail: () => set((state) => ({ leftRailOpen: !state.leftRailOpen })),
toggleContextPanel: () => set((state) => ({ contextPanelOpen: !state.contextPanelOpen })),
closeDrawers: () => set({ leftRailOpen: false, contextPanelOpen: false }),
```

### S5-T002: Responsive Studio Layout

**Responsible file:** `frontend/src/views/StudioView.tsx`

- [x] Replace inline `gridTemplateColumns` with one mounted `WritingView` and responsive rail/context positioning.
- [x] The implementation must render exactly one `<WritingView />` in `StudioView.tsx`.
- [x] Use one shared center column:

```tsx
<main className="min-h-0 overflow-hidden bg-[var(--bg-primary)]">
  <WritingView />
</main>
```

- [x] Desktop rail wrapper must use class substring `hidden xl:block`.
- [x] Desktop context wrapper must use class substring `hidden xl:block`.
- [x] Mobile rail drawer must be separate from the desktop rail and render only when `leftRailOpen`.
- [x] Mobile context drawer must be separate from the desktop context and render only when `contextPanelOpen`.
- [x] The outer layout must include responsive grid class substring:

```tsx
xl:grid-cols-[13rem_minmax(0,1fr)_26rem]
```

- [x] Rail drawer must render when `leftRailOpen` with class substring `absolute left-0 top-0 z-30 h-full w-72`.
- [x] Context drawer must render when `contextPanelOpen` with class substring `absolute right-0 top-0 z-30 h-full w-[min(28rem,100%)]`.
- [x] Add overlay backdrop button when either drawer is open with exact `aria-label="Close Studio drawers"` and `onClick={closeDrawers}`.
- [x] Desktop must still render `StudioProjectRail`, center `WritingView`, and `StudioContextPanel` inline.

### S5-T003: Mobile Drawer Buttons

**Responsible file:** `frontend/src/components/studio/StudioCommandBar.tsx`

- [x] Add two buttons visible below `xl` using class substring `xl:hidden`:
  - `Project`
  - `Context`
- [x] `Project` calls `toggleLeftRail`.
- [x] `Context` calls `toggleContextPanel`.
- [x] Keep existing command buttons unchanged.

### S5-T004: Drawer Tests

**Responsible file:** `frontend/src/views/StudioView.test.tsx`

- [x] Assert `Project` and `Context` buttons render.
- [x] Click `Project` and assert `Studio project map` remains accessible.
- [x] Click `Context` and assert current panel label remains accessible.
- [x] Click `Close Studio drawers` and assert no exception; do not rely on CSS visibility in jsdom.

## Final Verification

```powershell
cd frontend; cmd /c npm.cmd run lint
cd frontend; cmd /c npm.cmd run typecheck
cd frontend; cmd /c npm.cmd run build
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Expected: all exit 0.

## Stage 5 Pass Criteria

Stage 5 is complete only when all of these are true:

- Desktop Studio preserves the three-column working layout.
- Mobile/tablet Studio exposes `Project` and `Context` drawer controls.
- Drawer overlay has an accessible close control with `aria-label="Close Studio drawers"`.
- Store drawer helpers drive drawer state; no window resize listener is added.
- Command bar actions still open the correct context panels.
- Focused test passes:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
```

The serial Studio redesign is complete only when these pass and the final verification commands above exit 0.
