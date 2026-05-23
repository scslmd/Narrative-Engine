# Layout Management System — Design Spec

**Date:** 2026-05-23
**Status:** Design (adverse-reviewed, ready for implementation)
**Author:** AI Agent

## Goal

Enable users to create, save, rename, delete, and load named workspace layouts. Provide author-oriented presets based on established writing processes. Reset to a locked factory default.

## Architecture Decision: 2-Layer Split

### Chosen Architecture

| Layer | File | Role |
|-------|------|------|
| Config | `stores/layoutPresets.ts` | Factory default, built-in presets, user CRUD, localStorage |
| UI | `components/studio/StudioLayoutManager.tsx` | Dropdown, save/load/rename/delete/reset UI |

The existing `studioStore.ts` imports `getFactoryDefault()` and `getBuiltInPresets()` from `layoutPresets.ts`. `StudioLayoutManager.tsx` imports from both modules.

### Why Not 3-Layer?

A 3-layer approach (`config -> hook -> UI`) was considered and rejected:

1. **The hook would be thin** — 5 wrapper functions around `layoutPresets.ts`, adding indirection without value
2. **No shared state** — layout management doesn't need React Query caching, complex async flow, or form state that justifies a hook
3. **Existing precedent** — `StudioCommandBar.tsx` already imports directly from both `stores/studioStore.ts` and `components/studio/StudioPanelMenu.tsx`
4. **Future-proofing** — if the feature grows (cloud sync, versioning, sharing), extracting to `domains/layout/` is a 5-minute refactor

### Module Responsibilities

**`layoutPresets.ts` (NEW, ~220 lines)**
- Types: `UserLayout`, `FactoryLayout`, `BuiltInPreset`, expanded `AuthorPreset`
- Constants: factory default (locked), built-in presets map (9 presets)
- CRUD: `saveUserLayout(name, layout)`, `loadUserLayout(id)`, `renameUserLayout(id, newName)`, `deleteUserLayout(id)`
- List: `listUserLayouts()` returns sorted array
- Persistence: localStorage key `studio-user-layouts`
- No Zustand, no React — pure functions + types

**`studioStore.ts` (MODIFIED, ~30 lines removed)**
- Imports: `getFactoryDefault`, `getBuiltInPresets` from `layoutPresets.ts`
- Replaces: inline `LAYOUT_PRESETS` constant with import from `layoutPresets.ts`
- Keeps: `applyPreset()` inside Zustand `create()` — CANNOT move to pure module because it mutates store state via `set()`
- Adds: `factoryReset()` action — resets V1 + V2 to locked factory default
- Adds: `applyUserLayout(id)` action — loads user layout from `layoutPresets`, applies to store
- Expands: `AuthorPreset` type to include 5 new preset keys (see below)

**`StudioLayoutManager.tsx` (NEW, ~200 lines)**
- Dropdown: built-in presets (locked) + user layouts (editable)
- Save: inline text input for name, saves current layout state
- Rename/Delete: inline actions per user layout row (appears on hover)
- Factory Reset: destructive action, confirms with toast
- Replaces `StudioLayoutPreset.tsx` (deleted)
- Imports from: `layoutPresets.ts`, `studioStore.ts`
- Keeps: export/import functionality from old `StudioLayoutPreset` (moved to new component)

**`StudioCommandBar.tsx` (MODIFIED, ~3 lines changed)**
- Replaces `<StudioLayoutPreset />` with `<StudioLayoutManager />`
- Otherwise unchanged

**`StudioLayoutPreset.tsx` (DELETED)**
- File removed. `LAYOUT_PRESETS_MENU` moves to `layoutPresets.ts`
- Export/import UI moves to `StudioLayoutManager.tsx`

## Factory Default Layout

Locked in code, cannot be modified by user. One reset button restores it.

### V1 State (Rail/Context)

```ts
leftRailMode: 'expanded'
contextPanelMode: 'closed'
contextPanelPinned: true
leftRailWidth: 224
contextPanelWidth: 416
```

### V2 State (Floating Panels)

Three panels with deterministic grid positioning (8px grid):

| Panel | ID | Position {x, y} | Size {w, h} | zIndex | Role |
|-------|----|-----------------|-------------|--------|------|
| Manuscripts | `factory-manuscripts` | {x: 80, y: 0} | {320, 400} | 100 | Primary writing surface |
| Suggestions | `factory-suggestions` | {x: 0, y: 420} | {320, 400} | 101 | Review/revision cues |
| Characters | `factory-characters` | {x: 340, y: 420} | {360, 420} | 102 | Quick character reference |

Visual layout:
```
┌──────────┬─────────────────────────────────────┐
│  RAIL    │         Manuscripts (z:100)         │
│  NAV     ├─────────────────┬───────────────────┤
│          │  Suggestions    │  Characters       │
│          │     (z:101)     │    (z:102)        │
│          └─────────────────┴───────────────────┘
```

All panels: `visible: true`, `pinned: false`, `floating: false`, `collapsedSections: {}`, `scrollY: 0`.

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

| Preset | Key | Panels | Writing Process |
|--------|-----|--------|-----------------|
| Beat-Sheet | `beat-sheet` | Structure, Chapters, Notes, Generation | Save the Cat / Seven-Point beat-driven |
| Theme-Driven | `theme-driven` | Characters, Arcs, World Bible, Notes, Review | Literary fiction, thematic exploration |
| Showrunner | `showrunner` | Characters, Relationships, Arcs, Chapters, Generation | Episodic/serial, TV-style season arcs |
| Revision Lab | `revision-lab` | Manuscripts, Review, Suggestions, Notes, Drafts | Editing-focused, revision-pass workflow |
| World-Builder+ | `world-builder-plus` | World Bible, Characters, Relationships, Canon, Notes | Deep setting-first, expanded world bible |

### Updated `AuthorPreset` type

```ts
export type AuthorPreset =
  | 'idea-first'
  | 'character-first'
  | 'outline-first'
  | 'world-first'
  | 'beat-sheet'
  | 'theme-driven'
  | 'showrunner'
  | 'revision-lab'
  | 'world-builder-plus';
```

### Total: 9 built-in presets

Locked — cannot be renamed, deleted, or modified. User can only apply them.

## Custom Layout System

### Data Model

```ts
interface UserLayout {
  id: string;                         // UUID
  name: string;                       // User-defined, unique
  panels: Record<string, PanelLayoutState>; // Matches store's Record format
  v1State: PersistedStudioLayout;     // Rail/context state at save time
  createdAt: number;                  // Timestamp (ms)
  updatedAt: number;                  // Timestamp (ms)
}
```

**Note:** `panels` is a `Record<string, PanelLayoutState>` (object map), NOT an array. This matches the store's internal `layout.panels` format, avoiding conversion on save/load.

### CRUD Operations

| Operation | Function | localStorage | Notes |
|-----------|----------|-------------|-------|
| Save | `saveUserLayout(name, layout)` | Creates or updates in array | Validates unique name |
| Load | `loadUserLayout(id)` | Returns layout or null | Lookup by UUID |
| Rename | `renameUserLayout(id, newName)` | Updates name | Validates unique new name |
| Delete | `deleteUserLayout(id)` | Removes from array | |
| List | `listUserLayouts()` | Returns sorted array | Alphabetical by name |

### Persistence

- **Key:** `studio-user-layouts` (separate from V1 `studio-layout-v1` and V2 `studio-layout-v2-{projectId}`)
- **Format:** JSON array of `UserLayout` objects
- **Capacity:** Soft limit 50 layouts, UI shows warning at 45+
- **Validation:** Name must be unique, non-empty, max 50 characters

### Loading a User Layout (store action: `applyUserLayout(id)`)

1. Call `layoutPresets.loadUserLayout(id)` to get the layout
2. Clear current V2 panels (except pinned panels)
3. Apply saved panel records from `layout.panels` (direct merge, same format)
4. Apply saved V1 state via `setLeftRailMode`, `setContextPanelMode`, etc.
5. Set `activePanel` to the first visible panel's key (or `'suggestions'` fallback)
6. Set `layoutPreset` to the user layout name (string)
7. Persist V2 immediately via `persistLayoutV2` (no debounce)

### Save Current Layout (component -> store -> layoutPresets)

1. Component captures name from inline input
2. Reads current state: `layout.panels` (Record) + V1 state from store
3. Calls `layoutPresets.saveUserLayout(name, { panels, v1State })`
4. Layout persisted to `studio-user-layouts` localStorage
5. Component re-renders (layout list updated via reactive localStorage polling or state)

### Error Handling

- Corrupt localStorage: return empty array, console.warn
- Name collision: return `{ error: 'duplicate' }`, UI shows toast
- Storage full: catch `QuotaExceededError`, show toast warning
- Layout not found: return null, UI shows toast

## UI Design (StudioLayoutManager)

### Dropdown Structure

```
Layout ▼
┌─────────────────────────────────────┐
│ PRESETS                             │
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
│ MY LAYOUTS                          │
│ ▸ My Draft Setup  [pencil] [trash]  │
│ ▸ Revision Session [pencil] [trash] │
│                                     │
│ [+ Save Current Layout]             │
├─────────────────────────────────────┤
│ Export Layout (copy to clipboard)   │
│ Import Layout (paste JSON)          │
├─────────────────────────────────────┤
│ ⟲ Reset to Factory Default          │
└─────────────────────────────────────┘
```

### Interactions

| Action | Behavior |
|--------|----------|
| Click preset | Call `studioStore.applyPreset(key)`, close dropdown |
| Click user layout | Call `studioStore.applyUserLayout(id)`, close dropdown |
| Hover user layout row | Show rename (pencil) + delete (trash) buttons |
| Save Current | Inline text input replaces button, Enter saves, Escape cancels |
| Rename (pencil) | Inline text input replaces label in that row, Enter saves |
| Delete (trash) | Confirmation toast "Delete 'Layout Name'?", confirm -> delete |
| Export Layout | Copy `studioStore.exportLayout()` JSON to clipboard |
| Import Layout | Toggle textarea, paste JSON, click "Apply" |
| Factory Reset | Confirmation toast "Reset to factory default?", confirm -> reset |

### Visual Design

- Follows existing `StudioLayoutPreset.tsx` styling (dropdown, border, text sizes)
- Presets section has "PRESETS" header (uppercase, tracking, tertiary text)
- User layouts section has "MY LAYOUTS" header
- Locked presets show `▸` indicator (chevron)
- User layouts show pencil icon (rename) / trash icon (delete) on hover
- Factory reset at bottom, separated by border, uses `⟲` symbol
- Lucide icons: `Pencil` for rename, `Trash2` for delete, `Plus` for save

### State Management

The component uses local `useState` for:
- `open` — dropdown visibility
- `showImport` — import textarea visibility
- `importText` — import text value
- `showSaveInput` — save name input visibility
- `editingId` — which user layout is being renamed (null | string)
- `editName` — rename text input value

Layout list reactivity: component re-renders when `listUserLayouts()` result changes. Since `layoutPresets.ts` is pure functions (no reactive state), the component stores layouts in local state (`useState`) and updates on CRUD operations.

## Testing Strategy

### Unit Tests for `layoutPresets.ts`

| Test | Description |
|------|-------------|
| Factory default returns correct V1 state | Match all 5 fields |
| Factory default returns 3 panels | Correct IDs, keys, positions |
| Save creates layout | Round-trip save + load |
| Save overwrites existing name | Update behavior |
| Save rejects duplicate name | Returns error |
| Save rejects empty name | Returns error |
| Save rejects name > 50 chars | Returns error |
| Rename updates name | New name on load |
| Rename rejects duplicate name | Returns error |
| Delete removes layout | Returns null on load |
| List returns empty array initially | No layouts saved |
| List returns sorted layouts | Alphabetical by name |
| List returns 9 built-in presets | All presets present |
| Corrupt localStorage handled | Returns empty array |

### Component Tests for `StudioLayoutManager.tsx`

| Test | Description |
|------|-------------|
| Renders 9 preset buttons | All presets visible |
| Renders "My Layouts" section | Even when empty |
| Save creates layout | Input + Enter -> layout appears |
| Click preset applies | Calls store action |
| Click user layout applies | Calls store action with ID |
| Rename flow works | Pencil click -> input -> Enter -> renamed |
| Delete flow works | Trash click -> toast confirm -> deleted |
| Factory reset confirmation | Shows toast with confirm button |
| Export copies to clipboard | Clipboard API called |
| Import applies JSON | Textarea + Apply -> layout applied |

### Integration Tests

| Test | Description |
|------|-------------|
| Apply preset -> verify panel count | Check panel keys match preset |
| Save layout -> reload -> verify | Save, simulate refresh, load, compare |
| Factory reset -> verify V1 + V2 | Reset, check all fields match factory default |

## Data Flow

**Apply preset:**
```
User clicks preset
  -> StudioLayoutManager calls studioStore.applyPreset(key)
  -> applyPreset imports presets from layoutPresets.ts
  -> Creates panels, preserves pinned, persists V2
  -> StudioLayoutManager closes dropdown
```

**Save layout:**
```
User enters name, presses Enter
  -> StudioLayoutManager reads store state (panels + V1)
  -> Calls layoutPresets.saveUserLayout(name, { panels, v1State })
  -> Persists to localStorage key "studio-user-layouts"
  -> Component updates local state with listUserLayouts()
  -> Dropdown re-renders with new layout in list
```

**Load user layout:**
```
User clicks user layout row
  -> StudioLayoutManager calls studioStore.applyUserLayout(id)
  -> Store calls layoutPresets.loadUserLayout(id)
  -> Clears panels (except pinned), applies saved panels + V1
  -> Sets activePanel to first visible panel's key
  -> Persists V2 immediately (no debounce)
  -> StudioLayoutManager closes dropdown
```

**Factory reset:**
```
User clicks factory reset -> toast confirmation
  -> User confirms
  -> StudioLayoutManager calls studioStore.factoryReset()
  -> Store loads factory default from layoutPresets.getFactoryDefault()
  -> Resets V1 (rail mode, context mode, widths)
  -> Resets V2 (3 panels: manuscripts, suggestions, characters)
  -> Persists immediately (no debounce)
  -> StudioLayoutManager closes dropdown
```

## Migration Plan

### Phase 1: Extract `layoutPresets.ts`

1. Create `stores/layoutPresets.ts` with:
   - Types: `UserLayout`, `FactoryLayout`
   - Factory default constant (V1 state + 3 V2 panels)
   - Built-in presets map (9 presets, includes menu labels)
   - CRUD functions with localStorage persistence
2. Move `LAYOUT_PRESETS` constant from `studioStore.ts` to `layoutPresets.ts`
3. Move `AuthorPreset` type from `studioStore.ts` to `layoutPresets.ts` (re-export from studioStore for backward compat)
4. Update `studioStore.ts` to import from `layoutPresets.ts`
5. Add `factoryReset()` and `applyUserLayout(id)` actions to `studioStore`

### Phase 2: Build `StudioLayoutManager.tsx`

1. Create component with dropdown UI matching design
2. Wire presets, save/load/rename/delete/reset to `layoutPresets.ts` + `studioStore`
3. Include export/import functionality from old `StudioLayoutPreset`
4. Replace `<StudioLayoutPreset />` in `StudioCommandBar.tsx`
5. Delete `StudioLayoutPreset.tsx`

### Phase 3: Tests & Cleanup

1. Add unit tests for `layoutPresets.ts` (13 tests)
2. Add component tests for `StudioLayoutManager.tsx` (10 tests)
3. Update `StudioView.test.tsx` for new layout UI
4. Run full validation suite

## Constraints

- **localStorage only** — no server-side storage, layouts are per-device
- **No cloud sync** — out of scope for v1
- **Export/import retained** — JSON clipboard copy/paste preserved from old component
- **Max 50 user layouts** — soft limit, UI shows warning at 45+
- **Built-in presets immutable** — locked in code, no user modification

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| localStorage quota exceeded | Can't save layouts | Warning at 45 layouts, graceful error at limit |
| Corrupt layout data | Failed load | JSON parse guard, return null, show toast |
| Name collision | User confusion | Validate uniqueness, show error toast |
| Layout schema drift | Old layouts break | Version field in UserLayout, migration function |

## File Inventory

| File | Status | Lines (est.) |
|------|--------|-------------|
| `stores/layoutPresets.ts` | NEW | ~220 |
| `stores/studioStore.ts` | MODIFIED | -30 (net, after adding actions) |
| `components/studio/StudioLayoutManager.tsx` | NEW | ~200 |
| `components/studio/StudioCommandBar.tsx` | MODIFIED | +3 (import swap) |
| `components/studio/StudioLayoutPreset.tsx` | DELETED | -118 |
| `stores/layoutPresets.test.ts` | NEW | ~150 |
| `components/studio/StudioLayoutManager.test.tsx` | NEW | ~180 |

**Net change:** ~423 lines added, ~148 lines removed, ~275 net new

## Adverse Review Fixes Applied

1. **`UserLayout.panels` type** — Changed from `PanelLayoutState[]` to `Record<string, PanelLayoutState>` to match store format
2. **`applyPreset` stays in store** — Only `LAYOUT_PRESETS` constant moves to `layoutPresets.ts`. `applyPreset()` remains in Zustand `create()` because it calls `set()`
3. **`AuthorPreset` expanded** — Type union now includes all 9 preset keys
4. **Factory default coordinates** — Exact grid positions: Manuscripts {80,0}, Suggestions {0,420}, Characters {340,420}
5. **Rename flow specified** — Inline text input replaces label in the user layout row during rename
6. **Export/Import retained** — New component includes export/import buttons from old `StudioLayoutPreset`
7. **`layoutPreset` field** — Updated to accept both `AuthorPreset` keys and user layout names (both are strings)
8. **Panel key verified** — "notes" is a valid `StudioPanelKey` (line 18)
9. **`LAYOUT_PRESETS_MENU`** — Only used in `StudioLayoutPreset.tsx`, safe to move to `layoutPresets.ts`
10. **User layout click handler** — Passes `id` (UUID) to handler, not `name`
