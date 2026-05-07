# Stage-Based Navigation Redesign

**Date:** 2026-05-07  
**Status:** Draft — awaiting user review

## Problem

The workspace UI duplicates navigation across two areas:
- **Header pill group**: 7 mode buttons (Planning, Brain Dump, Canon, Generate, Writing, Review, Inspect)
- **Left sidebar rail**: 5 mode buttons (Brain Dump, Planning, Writing, Review, Inspect)

Both sets perform identical actions (`setMode()` + route navigation). This wastes horizontal header space (~280px pill group), increases cognitive load (scan 12 nav items instead of 6–7), and provides no contextual grouping. Additionally, Canon and Generate are missing from the sidebar.

## Goal

Eliminate redundant navigation while improving stage-level context awareness. Header answers "what phase am I in?", sidebar answers "what can I do here?"

## Design

### Stage Groupings

| Stage | Modes |
|-------|-------|
| Planning | Brain Dump, Planning, Canon, Generate |
| Writing | Writing |
| Review | Review, Inspect |

This mapping already exists as `stageMap` in `Layout.tsx` (line 16–24). The redesign makes it the primary navigation dimension.

### Header Bar (`Layout.tsx`)

**Before:** Horizontal pill group with 7 mode buttons (icons + labels), visible on `sm:` breakpoint and up.

**After:** 3-stage selector replacing the pill group:
- Each stage rendered as a button: `Planning | Writing | Review`
- Active stage highlighted (same visual treatment as current active pill)
- Clicking a stage navigates to its default mode:
  - Planning → `/workspace/:id/plan`
  - Writing → `/workspace/:id/write`
  - Review → `/workspace/:id/review`
- Stage button is active when `stageMap[uiMode] === stage`

**Unchanged:** Logo (home link), project name breadcrumb, theme toggle, settings button remain in header.

### Sidebar (`WorkspaceShell.tsx`)

**Before:** Static list of 5 nav items (Brain Dump, Planning, Writing, Review, Inspect). Canon and Generate are missing.

**After:** Filtered list showing only modes belonging to the active stage:
- Derive `activeStage` from `stageMap[mode]`
- Filter `navItems` to include only items whose stage matches `activeStage`
- Add `Canon` and `Generate` entries to complete the Planning stage
- Remove modes not in the active stage from the sidebar

**New nav config:**
```ts
const navItems: NavItem[] = [
  // Planning stage
  { key: 'braindump', label: 'Brain Dump', icon: Lightbulb, stage: 'planning', ... },
  { key: 'plan', label: 'Planning', icon: LayoutList, stage: 'planning', ... },
  { key: 'canon', label: 'Canon', icon: BookOpen, stage: 'planning', ... },
  { key: 'generate', label: 'Generate', icon: Sparkles, stage: 'planning', ... },
  // Writing stage
  { key: 'write', label: 'Writing', icon: BookOpen, stage: 'writing', ... },
  // Review stage
  { key: 'review', label: 'Review', icon: Search, stage: 'review', ... },
  { key: 'inspect', label: 'Inspect', icon: Sparkles, stage: 'review', ... },
]
```

Each item gains a `stage` property. Sidebar filters: `navItems.filter(item => item.stage === activeStage)`.

### State

No new state needed. `activeStage` is derived from existing `useUIStore().mode` via the `stageMap` mapping. Both components read from the same store, so stage changes propagate to both header and sidebar.

### Mobile

Existing mobile tab bar (below header on `<sm:` screens) already shows mode-level tabs. No change needed — it continues to show all modes regardless of stage, which is appropriate for mobile where screen real estate favors flat navigation.

## Files Affected

| File | Change |
|------|--------|
| `frontend/src/components/Layout.tsx` | Replace 7-mode pill group with 3-stage selector |
| `frontend/src/components/WorkspaceShell.tsx` | Add `stage` property to nav items, filter by active stage, add Canon + Generate entries |
| `frontend/src/components/Layout.test.tsx` | Update tests for stage selector |
| `frontend/src/components/WorkspaceShell.test.tsx` | (if exists) update for filtered sidebar |

## Error Handling / Edge Cases

- **Unknown mode:** If `mode` doesn't map to a stage, fall back to `planning` stage
- **Empty sidebar stage:** Writing stage has only 1 item — the single-item sidebar is acceptable (matches Figma's "Design" tab behavior)
- **Route sync:** `useRouteSync` already keeps store in sync with URL; no change needed

## Testing

- Verify stage selector highlights correctly when switching modes within a stage
- Verify sidebar shows correct items for each stage
- Verify clicking a stage button navigates to the default mode and updates sidebar
- Verify Canon and Generate appear in Planning stage sidebar
- Verify mobile tab bar is unchanged
- Run full frontend test suite: `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build`
