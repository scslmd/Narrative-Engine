# ViewShell Standardization

Date: 2026-05-17
Scope: Frontend layout + theme standardization. Extract Studio Desk's shell into a shared `ViewShell` component. Migrate all workspace views to use it. Replace `isDark` ternaries with CSS variables.

## Product Intent

Studio Desk established a reference layout: command bar, adaptive left rail, center content, context panel, bottom utility tray. The other 7 workspace views (Planning, Review, Generation, Canon, Inspect, BrainDump, Writing) each have their own layout, padding, tab colors, and theme strategy. This spec extracts Studio's shell into a reusable `ViewShell` component and migrates all views to use it.

**Goal**: One layout pattern, one theme strategy, one tab component across all workspace views.

## Current State

### Layout Inconsistencies

| View | Layout | Padding | Tabs | Theme |
|------|--------|---------|------|-------|
| StudioView | `h-full grid`, 3-column | `p-4` | N/A (command bar) | CSS variables |
| PlanningView | `h-full flex flex-col` | `p-4` | 12 color-coded tabs | `isDark` ternary |
| ReviewView | `h-full flex flex-col` | `p-5` | Amber tabs | `isDark` ternary |
| GenerationView | `space-y-4`, no wrapper | N/A | N/A | Mixed |
| CanonView | No wrapper, delegates to CanonWorkshop | N/A | CanonWorkshop tabs | Mixed |
| InspectView | `h-full`, delegates to InspectMode | N/A | N/A | `dark:` modifiers |
| BrainDumpView | `flex flex-col h-full` | `p-4` | N/A | CSS variables (correct) |
| WritingView | `h-full grid` | N/A | N/A | `isDark` ternary |

### Theme Strategies (3 different approaches)

1. **CSS variables** (correct): `bg-[var(--bg-primary)]`, `text-[var(--text-primary)]` — used by StudioView, BrainDumpView
2. **`isDark` ternary** (anti-pattern): `isDark ? 'bg-slate-900' : 'bg-white'` — used by PlanningView, ReviewView, WritingView
3. **Hardcoded `dark:` classes**: `bg-gray-50 dark:bg-slate-900` — used by InspectView, GenerationView

### Tab Implementations (4 different implementations)

1. **PlanningView**: 12 color-coded tabs (amber, emerald, indigo, etc.)
2. **ReviewView**: Amber tabs with `isDark` ternary
3. **CanonWorkshop**: Purple tabs
4. **StudioCommandBar**: No tabs, uses command bar verbs

### Right Sidebar

`Workspace.tsx` renders a static right sidebar with `NotesPanel` and `JobLaunchPanel`. StudioView has no right sidebar — it uses the context panel. The standard should be: unified context panel that adapts per view.

## Proposed Architecture

### ViewShell Component

```tsx
interface ViewShellProps {
  /** View title (e.g. "Planning", "Review") */
  title: string;
  /** Optional subtitle (e.g. project name, chapter title) */
  subtitle?: string;
  /** Action buttons (e.g. "New", "Save", "Generate") */
  actions?: React.ReactNode[];
  /** Left rail content (project map, navigation, etc.) */
  leftRailContent?: React.ReactNode;
  /** Right panel content (controlled by view) */
  rightPanelContent?: React.ReactNode;
  /** Show/hide right panel */
  showRightPanel?: boolean;
  /** Toggle right panel */
  onToggleRightPanel?: () => void;
  /** Left rail mode: collapsed, expanded, overlay */
  railMode?: 'collapsed' | 'expanded' | 'overlay';
  /** Children = main content area */
  children: React.ReactNode;
}
```

### ViewTabs Component

```tsx
interface ViewTab {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

interface ViewTabsProps {
  tabs: ViewTab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}
```

Single active color from `--color-primary` (stage-aware, CSS variable). Replaces all 4 tab implementations.

### ContextPanel Component

```tsx
interface ContextPanelTab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
}

interface ContextPanelProps {
  tabs: ContextPanelTab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}
```

Unified right panel. Each view passes its own panel tabs. Notes and JobLaunch become default panels available to all views.

### Layout Structure

```
ViewShell
├── CommandBar (title, subtitle, actions, panel toggle)
├── Grid: [left_rail] [main_content] [right_panel]
│   ├── LeftRail (adaptive: 80px collapsed / 280px expanded / overlay mobile)
│   ├── <children /> (the view's content)
│   └── RightPanel (view-controlled, 320px, shared panel components)
└── BottomUtilityLayer (jobs, suggestions, status)
```

### Store

Generalize `studioStore` → `viewShellStore` (or keep `studioStore` and rename internally). The store manages:
- Left rail mode (`collapsed` / `expanded` / `overlay`)
- Right panel visibility
- Left rail width (bounded 80-320px)
- localStorage persistence (`view-shell-layout-v1`)

## View Migration Plan

### Phase 1: Shell Components
1. Extract `ViewShell` from StudioView layout
2. Extract `ViewTabs` from PlanningView/ReviewView/CanonWorkshop
3. Extract `ContextPanel` from StudioView context panel
4. Migrate StudioView to use `ViewShell`

### Phase 2: View Wrappers
Each view gets a `ViewShell` wrapper. Internal content becomes `<children>`.

| View | Changes |
|------|---------|
| PlanningView | Replace 12-tab color map with `ViewTabs`. Remove `isDark` ternary. Wrap in `ViewShell`. |
| ReviewView | Replace amber tabs with `ViewTabs`. Remove `isDark` ternary. Change `p-5` → `p-4`. Wrap in `ViewShell`. |
| GenerationView | Add `ViewShell` wrapper. Add `p-4` content padding. Migrate hardcoded classes to CSS variables. |
| CanonView | Add `ViewShell` wrapper. Use `ViewTabs` for canon sub-tabs. Migrate hardcoded classes. |
| InspectView | Add `ViewShell` wrapper. Migrate `dark:` classes to CSS variables. |
| BrainDumpView | Minor: wrap in `ViewShell`, align padding, migrate auth error amber to CSS variables. |
| WritingView | Replace `isDark` ternaries with CSS variables. Wrap in `ViewShell`. |

### Phase 3: Workspace Shell
Replace `WorkspaceShell`'s static right sidebar with the adaptive context panel. `Workspace.tsx` becomes a thin router that renders `ViewShell`-wrapped views.

## Theme Migration Rules

| Current (anti-pattern) | After |
|------------------------|-------|
| `isDark ? 'bg-slate-900' : 'bg-white'` | `bg-[var(--bg-primary)]` |
| `isDark ? 'border-slate-800' : 'border-slate-200'` | `border-[var(--border-primary)]` |
| `isDark ? 'text-slate-100' : 'text-slate-900'` | `text-[var(--text-primary)]` |
| `isDark ? 'text-slate-400' : 'text-slate-500'` | `text-[var(--text-secondary)]` |
| `bg-gray-50 dark:bg-slate-900` | `bg-[var(--bg-secondary)]` |
| `tabActiveBgMap[tab.key]` (12 colors) | `bg-[var(--color-primary)]` (stage-aware) |
| `dark:bg-slate-800` | `bg-[var(--bg-elevated)]` |

### CSS Variable Reference

All tokens exist in `frontend/src/theme/variables.css`:

| Variable | Purpose |
|----------|---------|
| `--bg-primary` | Main background |
| `--bg-secondary` | Elevated surfaces |
| `--bg-elevated` | Cards, panels |
| `--border-primary` | Borders, dividers |
| `--border-secondary` | Subtle borders |
| `--text-primary` | Primary text |
| `--text-secondary` | Secondary text, labels |
| `--text-tertiary` | Muted text, placeholders |
| `--color-primary` | Active states, accents (stage-aware) |
| `--shadow-sm`, `--shadow-md`, `--shadow-lg` | Shadows |
| `--radius-sm`, `--radius-md`, `--radius-lg` | Border radii |

### Removing `isDark`

After migration, `resolveEffectiveMode()` and `isDark` become unnecessary in view components. The CSS variables handle theme switching at the DOM level via `data-theme` and `data-stage` attributes on `<html>`.

## New Files

```
frontend/src/components/shell/
├── ViewShell.tsx        # Shared layout shell
├── ViewTabs.tsx         # Shared tab bar
├── ContextPanel.tsx     # Unified right panel
├── ViewShell.test.tsx   # Tests
├── ViewTabs.test.tsx    # Tests
└── ContextPanel.test.tsx # Tests
```

## Modified Files

```
frontend/src/views/
├── StudioView.tsx       # Use ViewShell (was reference, now consumer)
├── PlanningView.tsx     # Wrap in ViewShell, migrate theme
├── ReviewView.tsx       # Wrap in ViewShell, migrate theme
├── GenerationView.tsx   # Wrap in ViewShell, migrate theme
├── CanonView.tsx        # Wrap in ViewShell, migrate theme
├── InspectView.tsx      # Wrap in ViewShell, migrate theme
├── BrainDumpView.tsx    # Wrap in ViewShell, minor theme fixes
├── WritingView.tsx      # Wrap in ViewShell, migrate theme
└── Workspace.tsx        # Replace right sidebar with ViewShell context panel

frontend/src/stores/
└── viewShellStore.ts    # Generalized from studioStore (or rename studioStore)
```

## Non-Goals

- No backend changes.
- No new routes.
- No removal of existing routes.
- No component extraction from large existing views (PlanningView internals, CanonWorkshop internals remain unchanged).
- No mobile-specific redesign beyond responsive collapse.

## Success Criteria

- All 8 workspace views use `ViewShell`.
- All `isDark` ternaries removed from views.
- All hardcoded `dark:` classes replaced with CSS variables.
- Single `ViewTabs` component replaces 4 tab implementations.
- `npm run lint`, `npm run typecheck`, `npm run build`, `npm run test` pass.
- Visual consistency: same padding, same active colors, same border treatment across all views.
