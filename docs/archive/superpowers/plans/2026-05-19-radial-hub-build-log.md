# Radial Hub Build Log

**Branch:** `codex/radial-hub`
**Started:** 2026-05-19
**Status:** Complete, ready for merge
**Total effort:** 5 phases, 5 commits, 49 TDD contract prompts (001–049)
**Diff summary:** 51 files changed, +3870 insertions, −102 deletions

---

## Executive Summary

Built a complete floating panel system for the Studio view — replacing the static left-rail + WritingView layout with a drag-and-drop, resizable, tear-off panel workspace. All 5 phases implemented, tested, and validated against the existing 736-test baseline.

---

## Phase-by-Phase Progress

### Phase 1: Core Infrastructure (`4bd8469`)

**Goal:** Establish foundation — store, floating panel, radial hub, panel menu, content router.

**Completed:**
- Extended `studioStore.ts` with `PanelLayoutState`, `StudioLayoutState`, and layout actions (`addPanel`, `removePanel`, `movePanel`, `resizePanel`, `togglePanel`, `pinPanel`, `tearOffPanel`)
- Created `StudioFloatingPanel.tsx` — draggable/resizable panel wrapper using DndKit
- Created `StudioRadialHub.tsx` — layout manager with DndContext, pointer sensors, snap grid
- Created `StudioPanelMenu.tsx` — dropdown panel menu with active-state indicators
- Created `StudioPanelContent.tsx` — router switch mapping `panelKey` to component
- Updated `StudioView.tsx` and `StudioCommandBar.tsx` to integrate new components

**Key Decisions:**
- **DndKit over react-dnd** — DndKit has smaller bundle, better TypeScript support, and pointer sensors for touch/mobile
- **Zustand over Redux** — store already uses Zustand; adding layout state to existing store avoids provider overhead
- **Custom resize handles over react-resizable-panels** — simpler, no virtual DOM reconciliation overhead, full control over snap behavior
- **Tear-off as React portal to `document.body`** — same-tab isolation without OS window complexity (which would require Electron or browser API not available in a web app)

**Findings:**
- DndKit's `useDraggable` + `useDraggableControls` pair was needed because panel drag handle must be decoupled from the panel body (to allow selection inside panel while dragging by header)
- Panel z-index management required careful ordering: floating panels (1000–1999) > radial hub (100) > WritingView (1) > context panel (50)

**Interesting Progress:**
- The snap grid system emerged naturally from testing — without it, panels landed at awkward pixel positions. The grid (20px default) gives predictable alignment while still allowing free-form placement.

---

### Phase 2: Panel Migration (`244c92d`)

**Goal:** Migrate existing panels to new system, add new panels, layout presets, status bar.

**Completed:**
- Migrated `StudioDraftsPanel` from `project` prop to `projectId` string prop (consistent API)
- Created `StudioStructurePanel.tsx` — story framework beat progression
- Created `StudioChaptersPanel.tsx` — chapter list and navigation
- Created `StudioCanonPanel.tsx` — canon profiles and annotations
- Created `StudioStatusBar.tsx` — bottom status bar with panel count, keyboard hints
- Added layout presets (`default`, `writing`, `review`, `explorer`) + `applyPreset` action to store
- Wired all panels in `StudioPanelContent.tsx` (16 `StudioPanelKey` values total)

**Key Decisions:**
- **`projectId` prop over `project` object** — consistent with existing Studio component pattern; avoids prop drilling of large objects
- **16 panel keys** — covers all workspace stages plus utility panels (generating, inspect, braindump, canon, etc.)
- **Layout presets as data, not UI** — presets are plain `StudioLayoutState` objects stored in the module; UI component (`StudioLayoutPreset`) added in Phase 3

**Findings:**
- `StudioManuscriptsPanel` kept its `onSelect`-only callback API — the `useWritingView` hook wasn't refactored yet, so this panel remains a write-only consumer until that work is scoped
- Three new panels (`structure`, `chapters`, `canon`) filled gaps where the old workspace had dedicated routes but no panel representation

**Interesting Progress:**
- The "writing" preset (single large manuscript panel, minimal chrome) and "review" preset (dual-panel side-by-side) emerged from actual usage patterns observed in the existing workspace layout.

---

### Phase 3: Interaction Polish (`6f5d49d`)

**Goal:** Debounced persistence, import/export, preset UI, hover preview, snap indicator, floating window, keyboard hooks, glass morphism.

**Completed:**
- Added debounced localStorage persistence (300ms debounce, writes to `studio-layout-v2-{projectId}`)
- Layout import/export via JSON + `importLayout`/`exportLayout` store actions
- Created `StudioLayoutPreset.tsx` — UI for selecting/applying presets
- Created `StudioHoverPreview.tsx` — ghost panel preview during drag
- Created `StudioSnapIndicator.tsx` — visual feedback for snap grid alignment
- Created `StudioFloatingWindow.tsx` — tear-off panel implementation as React portal
- Created `usePanelKeyboard.ts` — keyboard shortcuts (`Ctrl+1-9` switch panel, `Ctrl+0` reset layout, `Escape` close floating)
- Glass morphism polish (backdrop-filter blur, semi-transparent backgrounds, subtle borders)

**Key Decisions:**
- **300ms debounce** — balances persistence frequency against localStorage write cost; fast enough that data loss on crash is unlikely
- **JSON import/export** — human-readable, easy to share, no binary format needed for this scope
- **`Ctrl+1-9` panel switching** — matches VS Code conventions; users expect this for quick navigation
- **Floating window as portal, not iframe** — portal shares React context (store, theme, queries) with parent; iframe would require postMessage bridge

**Findings:**
- Glass morphism (`backdrop-filter: blur(12px)`) has minimal performance impact at small panel sizes; the real cost is compositing layers, which Chrome handles well
- The snap indicator needed a separate component because it must render *outside* the panel being dragged (positioned absolutely on the hub), which DndKit's drop animation doesn't provide

**Interesting Progress:**
- The hover preview system (ghost panel showing where a dropped panel will land) was built by listening to DndKit's `over` event and rendering a 30% opacity clone at the target position — this alone made the system feel "professional" to test.

---

### Phase 4: Route Migration (`fc952e0`)

**Goal:** Two-way URL sync, route migration, backward-compatible redirects.

**Completed:**
- Created `usePanelUrlSync.ts` — syncs active panel with URL `?tab=` query parameter
- Integrated hook into `StudioView.tsx`
- Replaced workspace routes with backward-compatible redirects (old `/workspace/:projectId/write` → `/studio`)
- Updated `WorkspaceShell.tsx` navigation, `useRouteSync.ts`, Layout stage derivation
- Updated `StudioProjectRail.tsx` links
- Added `panelToStage` mapping, `studioUrl()` helper, `routesLegacy` in `routes.ts`

**Key Decisions:**
- **`?tab=` query param, not path segment** — query params don't trigger React Router's navigation lifecycle; panel switching stays instant while still being URL-serializable
- **Backward-compatible redirects** — old URLs (`/write`, `/write/:chapterId`) redirect to `/studio` with appropriate `?tab=` param, so bookmarks and shared links still work
- **Two-way sync** — URL changes update store (for deep links), store changes update URL (for bookmarkability), with `useEffect` deps carefully managed to avoid loops

**Findings:**
- The old `useRouteSync` hook was tightly coupled to the stage-based workspace model; refactoring it to work with the panel-based Studio model required adding `panelToStage` mapping so Layout could still derive the correct navigation stage
- Deep links to specific panels (e.g., `?tab=chapters`) work on first load and after refresh — this was the key acceptance criterion

**Interesting Progress:**
- The URL sync hook needed a "last committed" pattern to avoid infinite loops: the `useEffect` that writes to URL checks whether the current URL already matches the active panel, and skips if so. Without this, every render would trigger a URL change, triggering a navigation event, triggering a render.

---

### Phase 5: Accessibility & Responsive (`28db5bb`)

**Goal:** ARIA semantics, keyboard navigation, responsive mobile modes, accessibility tests.

**Completed:**
- Added ARIA semantics across all panel components (`role="dialog"`, `aria-label`, `aria-modal`, `aria-describedby`)
- Keyboard navigation: Tab/Shift+Tab within panels, arrow keys in panel menu, Escape to close floating panels
- Created `useMediaQuery.ts` — SSR-safe media query hook
- Responsive mobile modes: bottom sheet panels, single-column layout, full-screen overlay
- Created `accessibility.test.tsx` — 4 integrated ARIA tests
- Updated test setup with `matchMedia` mock for jsdom
- Final validation: **736 tests passed**, typecheck 0 errors, lint 1 pre-existing warning, build 2019 modules

**Key Decisions:**
- **`role="dialog"` for floating panels** — screen readers announce these correctly; `aria-modal` prevents focus from escaping floating panels
- **Mobile bottom sheet, not modal** — bottom sheets are native mobile UX patterns; they slide up from bottom, dim background, dismiss on swipe down
- **SSR-safe `useMediaQuery`** — the hook checks `typeof window !== 'undefined'` before accessing `window.matchMedia`; returns `false` in SSR to avoid hydration mismatch

**Findings:**
- jsdom doesn't implement `window.matchMedia`, requiring a mock in the test setup — this is a common gotcha with responsive hooks in React testing
- ARIA `aria-modal="true"` on floating panels correctly traps focus, but only when combined with the `usePanelKeyboard` hook's Escape handler — both pieces are needed

**Interesting Progress:**
- The accessibility tests use `@testing-library/userEvent` to simulate keyboard navigation through the panel menu — this caught a bug where focus wasn't returning to the trigger button after closing the menu with Escape.

---

## Architecture Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Drag library | DndKit | Smaller bundle, better TS, touch support |
| Resize approach | Custom mouse events | No virtual DOM overhead, full snap control |
| Tear-off approach | React portal to body | Shares context, no OS window complexity |
| Panel state | Zustand (existing store) | Already in use, no provider needed |
| URL sync | `?tab=` query param | No router lifecycle overhead, bookmarkable |
| Persistence | localStorage + debounce | Simple, per-project, crash-safe |
| Import/export | JSON | Human-readable, shareable |
| Mobile panels | Bottom sheet | Native mobile UX pattern |
| Layout presets | Data objects, not UI | Separates data from presentation |
| Panel switching | `Ctrl+1-9` | VS Code convention, user expectation |

## Validation Baseline

| Check | Result |
|-------|--------|
| `npm run test` | 736 passed (93 files) |
| `npm run typecheck` | 0 errors |
| `npm run lint` | 1 pre-existing warning (unrelated) |
| `npm run build` | 2019 modules, 0 errors |

## Files of Interest

### New Components (12 files)
- `StudioFloatingPanel.tsx` — core draggable/resizable panel
- `StudioRadialHub.tsx` — layout manager, DndContext
- `StudioPanelMenu.tsx` — dropdown panel selector
- `StudioPanelContent.tsx` — panel key → component router
- `StudioStructurePanel.tsx` — story framework beats
- `StudioChaptersPanel.tsx` — chapter list/navigation
- `StudioCanonPanel.tsx` — canon profiles/annotations
- `StudioStatusBar.tsx` — bottom status bar
- `StudioFloatingWindow.tsx` — tear-off portal
- `StudioHoverPreview.tsx` — drag ghost preview
- `StudioSnapIndicator.tsx` — snap grid visual feedback
- `StudioLayoutPreset.tsx` — preset selector UI

### New Hooks (3 files)
- `usePanelUrlSync.ts` — URL ↔ active panel two-way sync
- `usePanelKeyboard.ts` — keyboard shortcuts for panel management
- `useMediaQuery.ts` — SSR-safe media query hook

### Modified Files (12 files)
- `studioStore.ts` — +363 lines: layout state, actions, presets, persistence
- `StudioView.tsx` — integrated StudioRadialHub + StudioStatusBar
- `StudioCommandBar.tsx` — added StudioPanelMenu + reset button
- `App.tsx` — backward-compatible route redirects
- `routes.ts` — panelToStage mapping, studioUrl(), routesLegacy
- `useRouteSync.ts` — adapted for panel-based Studio model
- `WorkspaceShell.tsx` — updated navigation
- `StudioProjectRail.tsx` — updated panel links
- `Layout.tsx` — updated stage derivation
- `StudioDraftsPanel.tsx` — migrated to projectId prop
- `setup.ts` — matchMedia mock for jsdom
- `accessibility.test.tsx` — 4 integrated ARIA tests

### Test Files (18 new/updated)
All new components have dedicated tests; existing tests updated for new prop signatures.

## Known Limitations & Future Work

1. **StudioManuscriptsPanel `onSelect`-only API** — needs `useWritingView` refactoring to support two-way content sync
2. **Multi-monitor tear-off** — portal approach is same-tab only; true OS window tear-off would require Electron or `window.open()` with postMessage bridge
3. **Collaborative layouts** — no real-time sync of panel positions across users; would require WebSocket + CRDT
4. **Panel minimize/maximize** — not yet implemented; would be natural extensions of the floating panel system

---

## Post-Merge Polish (2026-05-21)

**Branch:** `codex/radial-hub`
**Commits:** `d2fb0bd`, `a212790`, `ed71f5d`, `1b08e46`, `484cb1b`, `a825eab`, `13d2524`, `31d5ac1`

### Panel Sizing (`d2fb0bd`, `a212790`, `ed71f5d`)

**Goal:** Resize panel text, buttons, and spacing to fit properly inside 300–460px wide panels.

**Changes:**
- Headings: `text-lg` → `text-sm` across all panels
- Subtext/metadata: `text-sm` → `text-[10px]`/`text-xs`
- Buttons: `px-3 py-1.5 text-xs` → `px-2 py-1 text-[10px]`
- Card padding: `p-4` → `p-2.5`
- Spacing: `space-y-4` → `space-y-2`
- Empty states: `py-8 text-sm` → `py-6 text-xs`
- Icons: `w-4 h-4` → `w-3.5 h-3.5`
- All panels use `flex h-full flex-col` with `shrink-0` header and `flex-1 overflow-y-auto` content
- Updated 14 files: Characters, Arcs, Relationships, Generation, Review, Inspect, Structure, Chapters, Canon, Drafts, Manuscripts, AidsPanel, StudioContextPanel, StudioPanelContent

**Key Decisions:**
- **Per-panel default sizes** — replaced uniform 280x360 with `PANEL_DEFAULT_SIZES` map (e.g., characters 360x420, relationships 400x460, generation 380x460)
- **Compact sizing for narrow panels** — 300–460px width requires smaller text/buttons to avoid overflow
- **Consistent scale** — same size classes across all panel types for visual coherence

### Pin Behavior (`1b08e46`)

**Goal:** Implement pinned panel behavior — pinned panels survive reset and preset changes.

**Changes:**
- `pinPanel` action in store toggles `pinned` flag
- `removePanel` blocks removal of pinned panels
- `resetLayout` preserves pinned panels, removes unpinned
- `applyPreset` preserves pinned panels, adds preset panels without duplicating pinned keys
- Pin button in `StudioFloatingPanel` header shows amber color when pinned, hides close button
- 4 unit tests in `studioStore.pin.test.tsx`

**Key Decisions:**
- **Pin = persistent** — pinned panels survive layout resets and preset changes, acting as "always-on" workspace elements
- **Pin button in header** — replaces close button when pinned; visual feedback via amber color
- **No pin-to-position** — pinning preserves current position/size; does not lock position during drag

### Resize & Snap Fixes (`484cb1b`)

**Goal:** Fix resize handle visibility, duplicate panel creation, and snap-on-mouseup behavior.

**Changes:**
- Resize handles now visible during drag with accent color highlight
- Fixed duplicate panel creation in `StudioFloatingPanel` (removed duplicate `useDraggable` call)
- Snap detection triggers on mouseup for final position alignment
- Improved resize handle edge detection for left/top resize directions

### Panel-to-Panel Snapping (`a825eab`, `31d5ac1`)

**Goal:** Enable panels to snap to each other for adjacent layout (side-by-side, stacked).

**Changes:**
- `detectPanelSnap` function checks for nearby panel edges within `SNAP_THRESHOLD` (64px)
- **Snap directions:** right of, left of, above, below
- **Best-match selection:** collects all candidate snaps, returns the one with smallest gap (fixes horizontal snapping issue)
- **Visual feedback:** Blue snap line appears between panels showing alignment
- **Priority:** Panel snaps take precedence over workspace-edge snaps
- **Grid alignment:** Snap positions still grid-snapped (8px) for clean alignment
- Updated `StudioSnapIndicator.tsx` with `PanelRect` type, `detectPanelSnap`, panel snap visuals
- Updated `StudioRadialHub.tsx` to pass `otherPanels` to snap detection

**Key Decisions:**
- **Panel snaps override edge snaps** — when a panel is near another panel, panel snapping takes priority over workspace edge snapping
- **Overlap requirement** — horizontal snaps (left/right) require vertical overlap; vertical snaps (above/below) require horizontal overlap. This prevents snapping panels that are diagonally far apart.
- **Best-match over first-match** — the original implementation returned on first match, which could skip horizontal snaps if vertical checks ran first. Best-match ensures the closest snap wins regardless of direction.

### Panel Singularity (`13d2524`)

**Goal:** Enforce one instance per panel type — no duplicate panels.

**Changes:**
- `addPanel` checks for existing panel with same `key`; if found, brings it to front instead of creating duplicate
- `loadLayout` deduplicates saved panels on load, keeping only first instance of each panel type
- Existing duplicate panels are cleaned up on next layout load

**Key Decisions:**
- **Bring-to-front on duplicate** — clicking a panel menu item for an already-open panel brings it to front (raises z-index, ensures visibility) rather than creating a duplicate
- **Dedup on load** — saved layouts with duplicate panels are cleaned up automatically, preventing stale duplicates from persisting across sessions
- **No dedup on drag** — panels retain their individual positions; dedup only applies to `addPanel` and `loadLayout`

### Validation

| Check | Result |
|-------|--------|
| `npm run test` | 742 passed |
| `npm run typecheck` | 0 errors |
| `npm run build` | 2070 modules, 0 errors |
