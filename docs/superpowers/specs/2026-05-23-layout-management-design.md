# Layout Management System — Design Spec

**Date:** 2026-05-23
**Status:** Design (pending implementation plan)
**Author:** AI Agent

## Goal

Enable users to create, save, rename, delete, and load named workspace layouts. Provide author-oriented presets based on established writing processes. Reset to a locked factory default.

## Architecture Decision: 2-Layer Split

### Chosen Architecture

| Layer | File | Role |
|-------|------|------|
| Config | stores/layoutPresets.ts | Factory default, built-in presets, user CRUD, localStorage |
| UI | components/studio/StudioLayoutManager.tsx | Dropdown, save/load/rename/delete/reset UI |

The existing studioStore.ts imports getFactoryDefault() and getBuiltInPresets() from layoutPresets.ts. StudioLayoutManager.tsx imports from both modules.

### Why Not 3-Layer?

A 3-layer approach (config → hook → UI) was considered:

- stores/layoutPresets.ts — config + persistence
- domains/layout/useLayoutManager.ts — hook bridging store + presets
- components/studio/StudioLayoutManager.tsx — UI

**Rejected** because:

1. **The hook would be thin** — 5 wrapper functions around layoutPresets.ts, adding indirection without value
2. **No shared state** — layout management doesn't need React Query caching, complex async flow, or form state that justifies a hook
3. **Existing precedent** — StudioCommandBar.tsx already imports directly from both stores/studioStore.ts and components/studio/StudioPanelMenu.tsx. The 2-layer pattern works
4. **Future-proofing** — if the feature grows (cloud sync, versioning, sharing), extracting to domains/layout/ is a 5-minute refactor. Premature abstraction costs more than deferred extraction

### Module Responsibilities

`
layoutPresets.ts (NEW, ~200 lines)
├── Types: UserLayout, FactoryLayout, BuiltInPreset
├── Constants: factory default, built-in presets
├── CRUD: saveUserLayout, loadUserLayout, renameUserLayout, deleteUserLayout
├── List: listAllPresets (built-in + user, sorted)
├── Reset: factoryReset() → returns default V1 + V2 state
├── Persistence: localStorage key "studio-user-layouts"
└── No Zustand, no React — pure functions + types

studioStore.ts (MODIFIED, ~50 lines removed)
├── Imports: getFactoryDefault, getBuiltInPresets from layoutPresets.ts
├── Replaces: inline LAYOUT_PRESETS constant → imported
├── Adds: factoryReset() action (resets to locked default)
├── Keeps: V1/V2 runtime state, panel ops, persistence
└── Loses: LAYOUT_PRESETS constant, applyPreset logic (moved to layoutPresets)

StudioLayoutManager.tsx (NEW, ~180 lines)
├── Dropdown: built-in presets (locked) + user layouts (editable)
├── Save: text input for name, saves current layout state
├── Rename/Delete: inline actions per user layout
├── Factory Reset: destructive action, confirms with user
├── Replaces: StudioLayoutPreset.tsx (removed)
└── Imports from: layoutPresets.ts, studioStore.ts

StudioCommandBar.tsx (MODIFIED, ~3 lines changed)
├── Replaces: <StudioLayoutPreset /> → <StudioLayoutManager />
└── Otherwise unchanged
`

## Factory Default Layout

Locked in code, cannot be modified by user. One reset button restores it.

### V1 State (Rail/Context)

`	s
leftRailMode: 'expanded'
contextPanelMode: 'closed'
contextPanelPinned: true
leftRailWidth: 224
contextPanelWidth: 416
`

### V2 State (Floating Panels)

Three panels, logical positioning:

| Panel | Position | Size | Role |
|-------|----------|------|------|
| Manuscripts | center-top, wide | 320×400 | Primary writing surface |
| Suggestions | bottom-left | 320×400 | Review/revision cues |
| Characters | bottom-right | 360×420 | Quick character reference |

Grid layout:
`
┌──────────┬─────────────────────────────────────┐
│  RAIL    │  Manuscripts (center, primary)      │
│  NAV     ├─────────────────┬───────────────────┤
│          │  Suggestions    │  Characters       │
│          └─────────────────┴───────────────────┘
`

### Why This Default?

- **Writing-first** — Manuscripts is the default focus; user opens the app to write
- **Context available** — Suggestions + Characters provide immediate reference without cluttering
- **Rail expanded** — Navigation visible, user can switch sections
- **Context panel closed** — Clean workspace, no split-screen distraction

## Built-In Presets (Locked)

### Existing 4 (unchanged)

| Preset | Panels | Description |
|--------|--------|-------------|
| Idea-First (Pantser) | Ideas, Manuscripts, Characters | Discovery-driven, freeform |
| Character-First | Characters, Relationships, Arcs, Ideas | Character-centric development |
| Outline-First (Plotter) | Structure, Chapters, Generation | Pre-planned, structured |
| World-First | World Bible, Characters, Arcs, Structure | Setting-driven, immersive |

### New 5 (author-oriented, process-based)

| Preset | Panels | Writing Process |
|--------|--------|-----------------|
| Beat-Sheet | Structure, Chapters, Notes, Generation | Save the Cat / Seven-Point beat-driven writing |
| Theme-Driven | Characters, Arcs, World Bible, Notes, Review | Literary fiction, thematic exploration |
| Showrunner | Characters, Relationships, Arcs, Chapters, Generation | Episodic/serial, TV-style season arcs |
| Revision Lab | Manuscripts, Review, Suggestions, Notes, Drafts | Editing-focused, revision-pass workflow |
| World-Builder+ | World Bible, Characters, Relationships, Canon, Notes | Deep setting-first, expanded world bible |

### Total: 9 built-in presets

Locked — cannot be renamed, deleted, or modified. User can only apply them.

## Custom Layout System

### Data Model

`	s
interface UserLayout {
  id: string;                    // UUID
  name: string;                  // User-defined, unique
  panels: PanelLayoutState[];    // Current panel arrangement
  v1State: PersistedStudioLayout; // Rail/context state at save time
  createdAt: number;             // Timestamp
  updatedAt: number;             // Timestamp
}
`

### CRUD Operations

| Operation | Function | localStorage |
|-----------|----------|-------------|
| Save | saveUserLayout(name, state) | Creates/overwrites in array |
| Load | loadUserLayout(id) | Returns layout or null |
| Rename | enameUserLayout(id, newName) | Updates name, validates uniqueness |
| Delete | deleteUserLayout(id) | Removes from array |
| List | listUserLayouts() | Returns sorted array |

### Persistence

- **Key:** studio-user-layouts (separate from V1/V2)
- **Format:** JSON array of UserLayout objects
- **Capacity:** No hard limit, but ~50 layouts suggested for UX (localStorage quota)
- **Validation:** Name must be unique, non-empty, max 50 characters

### Loading a User Layout

1. Clear current V2 panels (except pinned)
2. Apply saved panel positions, sizes, visibility
3. Apply saved V1 state (rail mode, context mode, widths)
4. Set ctivePanel to the first visible panel
5. Update layoutPreset to the user layout name

### Error Handling

- Corrupt localStorage: return empty array, log warning
- Name collision: return error, UI shows toast
- Storage full: graceful degradation, show warning

## UI Design (StudioLayoutManager)

### Dropdown Structure

`
Layout ▼
┌─────────────────────────────────────┐
│ PRESETS (built-in, locked)          │
│ ▸ Idea-First (Pantser)              │
│ ▸ Character-First                   │
│ ▸ Outline-First (Plotter)           │
│ ▸ World-First                       │
│ ▸ Beat-Sheet                        │
│ ▸ Theme-Driven                      │
│ ▸ Showrunner                        │
│ ▸ Revision Lab                      │
│ ▸ World-Builder+                    │
├─────────────────────────────────────┤
│ MY LAYOUTS (user-defined)           │
│ ▸ My Layout A  [✎] [🗑]            │
│ ▸ Chapter Draft  [✎] [🗑]          │
│                                     │
│ [+ Save Current Layout]             │
├─────────────────────────────────────┤
│ [⟲ Reset to Factory Default]        │
└─────────────────────────────────────┘
`

### Interactions

| Action | Behavior |
|--------|----------|
| Click preset | Apply preset, close dropdown |
| Click user layout | Load layout, close dropdown |
| Save Current | Inline text input appears, enter name → saves |
| Rename (✎) | Inline text input replaces name |
| Delete (🗑) | Confirmation toast "Delete 'Layout Name'?", confirm → delete |
| Factory Reset | Confirmation toast "Reset to default layout?", confirm → reset |

### Visual Design

- Follows existing StudioLayoutPreset.tsx styling (dropdown, border, text sizes)
- Presets section has PRESETS header (uppercase, tracking, secondary text)
- User layouts section has MY LAYOUTS header
- Locked presets show ▸ indicator, user layouts show ✎ / 🗑 actions
- Factory reset button at bottom, separated by border, uses ⟲ symbol

## Testing Strategy

### Unit Tests

| Test | Description |
|------|-------------|
| layoutPresets.ts — factory default | Returns expected V1 + V2 state |
| layoutPresets.ts — save/load | Round-trips layout data |
| layoutPresets.ts — rename | Updates name, validates uniqueness |
| layoutPresets.ts — delete | Removes layout, persists |
| layoutPresets.ts — list | Returns sorted presets + user layouts |
| StudioLayoutManager.tsx — renders | Shows presets + user layouts |
| StudioLayoutManager.tsx — save | Creates layout, shows in list |
| StudioLayoutManager.tsx — rename | Renames layout, updates UI |
| StudioLayoutManager.tsx — delete | Deletes layout, removes from UI |
| StudioLayoutManager.tsx — factory reset | Resets to default, clears V2 |

### Integration Tests

| Test | Description |
|------|-------------|
| Load preset → verify panels | Apply preset, check panel count/keys |
| Save layout → reload → verify | Save, simulate refresh, load, compare |
| Factory reset → verify V1/V2 | Reset, check all fields match default |

## Data Flow

`
User clicks preset
  → StudioLayoutManager calls layoutPresets.loadPreset(key)
  → Returns layout data
  → StudioLayoutManager calls studioStore.applyLayout(data)
  → studioStore updates panels + V1 state
  → persistLayoutV2(debounced)

User saves layout
  → StudioLayoutManager captures name from input
  → Reads current state from studioStore
  → Calls layoutPresets.saveUserLayout(name, state)
  → Persists to localStorage
  → StudioLayoutManager re-renders (layout list updated)

User clicks factory reset
  → Confirmation toast
  → StudioLayoutManager calls studioStore.factoryReset()
  → studioStore loads factory default from layoutPresets.getFactoryDefault()
  → Resets V1 + V2 to locked defaults
  → Persisted immediately (no debounce)
`

## Migration Plan

### Phase 1: Extract layoutPresets.ts

1. Create stores/layoutPresets.ts with factory default, built-in presets, CRUD functions
2. Move LAYOUT_PRESETS constant from studioStore.ts to layoutPresets.ts
3. Update studioStore.ts to import from layoutPresets.ts
4. Add actoryReset() action to studioStore

### Phase 2: Build StudioLayoutManager.tsx

1. Create component with dropdown UI
2. Wire save/load/rename/delete/reset to layoutPresets.ts + studioStore
3. Replace <StudioLayoutPreset /> in StudioCommandBar.tsx
4. Remove StudioLayoutPreset.tsx

### Phase 3: Tests & Cleanup

1. Add unit tests for layoutPresets.ts
2. Add component tests for StudioLayoutManager.tsx
3. Update StudioView.test.tsx for new layout UI
4. Run full validation suite

## Constraints

- **localStorage only** — no server-side storage, layouts are per-device
- **No cloud sync** — out of scope for v1
- **No layout sharing** — export/import remains JSON clipboard (existing feature)
- **Max 50 user layouts** — soft limit, UI shows warning at 45+
- **Built-in presets immutable** — locked in code, no user modification

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| localStorage quota exceeded | Can't save layouts | Warning at 45 layouts, graceful error at limit |
| Corrupt layout data | Failed load | JSON parse guard, return null, show toast |
| Name collision | User confusion | Validate uniqueness, show error |
| Layout schema drift | Old layouts break | Version field in UserLayout, migration function |

## File Inventory

| File | Status | Lines (est.) |
|------|--------|-------------|
| stores/layoutPresets.ts | NEW | ~200 |
| stores/studioStore.ts | MODIFIED | -50 (net -10%) |
| components/studio/StudioLayoutManager.tsx | NEW | ~180 |
| components/studio/StudioCommandBar.tsx | MODIFIED | +3 (import swap) |
| components/studio/StudioLayoutPreset.tsx | REMOVED | -118 |
| stores/layoutPresets.test.ts | NEW | ~120 |
| components/studio/StudioLayoutManager.test.tsx | NEW | ~150 |

**Net change:** ~370 lines added, ~168 lines removed, ~202 net new
