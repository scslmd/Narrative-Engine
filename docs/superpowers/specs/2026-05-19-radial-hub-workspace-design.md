# Radial Hub Workspace — Design Spec

Date: 2026-05-19
Supersedes: `2026-05-16-studio-desk-redesign-design.md`, `2026-05-16-floating-panels-implementation.md`
Scope: Frontend UI/UX redesign. Replaces route-based navigation with Photoshop-style radial hub workspace.
Status: **APPROVED** — Visual mockup reviewed and confirmed by user (2026-05-19).

## Product Intent

Transform Narrative Engine from a route-driven feature collection into a single, fluid writing workspace. The writer spends the entire session in one place, with the manuscript in the center and supporting tools as draggable, resizable, tear-off panels around it.

**Core principle:** The tool adapts to the author's natural flow. No forced navigation. All activities accessible simultaneously.

Research documented in `docs/superpowers/research/2026-05-19-radial-hub-workspace-research.md`.

## Design Decisions

### Why Radial Hub?

Authors move between activities fluidly during a writing session. The current route-based architecture forces context-switching for every activity change. The radial hub keeps the writing surface stable while surrounding it with contextual tools.

### Why Photoshop-Style Panels?

Photoshop's workspace model is the proven industry standard for multi-panel creative work:
- Draggable, resizable panels
- Tear-off into floating windows (multi-monitor support)
- User-defined layouts with presets
- No forced navigation — all tools accessible simultaneously

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Single central route `/workspace/:projectId/studio` | Eliminates route-based context switching |
| 12 available panels | Covers all backend capabilities without overwhelming |
| User chooses visible panels | Different author types (pantser, plotter, etc.) need different tools |
| Hover to preview, click to expand | Reduces clicks to access information |
| Drag to reposition | Fluid workspace adaptation |
| ⊡ button to tear-off | Multi-monitor support for power users |
| Layout persistence per project | Each project can have its own optimal layout |
| No forced default layout | User builds workspace to match their workflow |
| Old routes remain during transition | Backward compatibility, gradual migration |

## Layout Architecture

```
+------------------------------------------------------------------+
| Top Bar: Project name | Chapter context | Framework | Status      |
+------------+-------------------------------------------+----------+
|            |                                           |          |
|  Panel     |        Central Writing Surface            |  Panel   |
|  (drag     |                                           |  (drag   |
|   able,    |     Stable editor / active artifact       |   able,  |
|  resizable)|                                           | resizable)|
|            |                                           |          |
|  [or       |                                           |  [or     |
|   torn     |                                           |   torn   |
|   off)]    |                                           |   off)]  |
|            |                                           |          |
+------------+-------------------------------------------+----------+
| Bottom Panel: Ideas / Status / Runtime (collapsible)              |
+------------------------------------------------------------------+
```

### Panel Behavior

- **Hover:** Preview quick information (character summary, world entry, etc.)
- **Click:** Expand panel to full view
- **Drag header:** Reposition panel within workspace
- **Drag edges:** Resize panel
- **⊡ button:** Tear off into floating window (multi-monitor capable)
- **✕ button:** Close panel (can be reopened from panel menu)
- **Pin (📌):** Prevent auto-collapse, maintain size/position

## Panel Catalog

12 panels available. User chooses which to show:

| Panel | Icon | Content | Source Component |
|-------|------|---------|-----------------|
| **Characters** | 👤 | Character profiles, roles, archetypes | `StudioCharactersPanel` |
| **Relationships** | 🔗 | Relationship graph, edges | `StudioRelationshipsPanel` |
| **World Bible** | 🌍 | World entries, rules, geography | `StudioWorldBiblePanel` |
| **Arcs** | 📈 | Character arcs, stage maps | (new, from arcs API) |
| **Structure** | 📋 | Story framework, beat progression | (new, from planning API) |
| **Chapters** | 📑 | Chapter list, navigation, packets | (new, from planning API) |
| **Ideas** | 💡 | Brainstorm items, quick notes | `StudioIdeasPanel` |
| **Manuscripts** | 📖 | Manuscript documents, navigation | (existing drafting components) |
| **Generation** | ⚡ | Generation wizard, run status | `StudioGenerationPanel` |
| **Review** | 🔍 | Suggestions, findings, decisions | `StudioReviewPanel` |
| **Inspect** | 🔬 | Job steps, lineage, attempts | `StudioInspectPanel` |
| **Canon** | 📜 | Canon scope, profiles, annotations | (existing canon components) |

## Author Entry Point Support

The workspace supports all 4 author entry points by letting the user configure which panels are visible:

| Entry Type | Default Panels | Workflow |
|------------|---------------|----------|
| **Idea-First** | Ideas, Manuscripts, Characters | Capture → Write → Build character as needed |
| **Character-First** | Characters, Relationships, Arcs, Ideas | Build characters → Define relationships → Let story emerge |
| **Outline-First** | Structure, Chapters, Generation | Plan structure → Outline chapters → Generate |
| **World-First** | World Bible, Characters, Arcs, Structure | Build world → Create characters → Plan story within world |

## Story Framework Integration

The Structure panel displays the active story framework's beat progression:

- Framework selected in project manifest (`manifest.json` → `config.story_structure`)
- Visual beat bar shows completed vs. remaining beats
- Click beat to see chapter mapping
- Color-coded: green (completed), amber (current), gray (upcoming)
- Framework-specific labels (e.g., Save the Cat's 15 beats vs. Three Act's 3 acts)

## Frontend Architecture

### Route Changes

**Before:**
```
/workspace/:projectId/braindump
/workspace/:projectId/plan
/workspace/:projectId/canon
/workspace/:projectId/generate
/workspace/:projectId/write
/workspace/:projectId/review
/workspace/:projectId/inspect
/workspace/:projectId/studio
```

**After:**
```
/workspace/:projectId/studio  ← primary workspace (replaces all above)
/workspace/:projectId/*       ← redirect to /studio (backward compat)
```

### New Components

```
frontend/src/components/studio/
├── StudioRadialHub.tsx          # NEW: Main radial hub layout manager
├── StudioFloatingPanel.tsx      # NEW: Draggable/resizable/tear-off panel wrapper
├── StudioPanelMenu.tsx          # NEW: Panel visibility toggle menu
├── StudioStatusBar.tsx          # NEW: Bottom status bar
├── StudioArcsPanel.tsx          # NEW: Arcs panel content
├── StudioStructurePanel.tsx     # NEW: Story structure panel content
├── StudioChaptersPanel.tsx      # NEW: Chapters panel content
├── StudioCommandBar.tsx         # KEPT: Top command bar
├── StudioProjectRail.tsx        # KEPT: Left rail (becomes a panel)
├── StudioCharactersPanel.tsx    # KEPT: Panel content
├── StudioRelationshipsPanel.tsx # KEPT: Panel content
├── StudioWorldBiblePanel.tsx    # KEPT: Panel content
├── StudioIdeasPanel.tsx         # KEPT: Panel content
├── StudioGenerationPanel.tsx    # KEPT: Panel content
├── StudioReviewPanel.tsx        # KEPT: Panel content
├── StudioInspectPanel.tsx       # KEPT: Panel content
├── StudioSuggestionsPanel.tsx   # KEPT: Panel content
└── StudioMergedSuggestions.tsx  # KEPT: Panel content
```

### Store Changes

`studioStore.ts` expanded to manage panel layout state:

```ts
interface PanelState {
  id: string;              // unique panel instance id
  key: StudioPanelKey;     // panel type identifier
  position: { x: number; y: number };
  size: { width: number; height: number };
  visible: boolean;
  pinned: boolean;
  floating: boolean;       // torn-off into separate window
  zIndex: number;
}

interface StudioLayout {
  panels: Record<string, PanelState>;
  nextZIndex: number;
  layoutPreset: string | null;
}
```

Actions: `addPanel`, `removePanel`, `movePanel`, `resizePanel`, `togglePanel`, `pinPanel`, `tearOffPanel`, `reattachPanel`, `resetLayout`, `saveLayout`, `loadLayout`.

Persist to `localStorage` with key `studio-layout-${projectId}`.

### Dependencies

| Package | Purpose |
|---------|---------|
| `@dnd-kit/core` | Drag panels to reposition |
| `@dnd-kit/utilities` | CSS classnames, sortable helpers |
| `react-resizable-panels` | Resize panels (lightweight, ~6KB) |

## Interaction Details

### Drag Behavior

- Drag from panel header bar only (not content area)
- 8px grid snap using `closestCorners` collision detection
- Snap zones: left edge, right edge, top, bottom, center
- Dragged panel auto-brings-to-front (z-index managed by store)

### Resize Behavior

- Resize handles on right/bottom edges, bottom-right corner
- Visible on hover only
- Min size: 180px width, 120px height
- Max size: workspace bounds minus 16px padding

### Tear-Off Behavior

- Click ⊡ button to tear panel into floating window
- Floating window can be moved to second monitor
- Reattach button (⊡) returns panel to main workspace
- Floating panels maintain state (content, size, scroll position)

### Layout Persistence

- Layout auto-saves on any panel change
- Per-project persistence (each project has its own layout)
- "Reset Layout" button restores user's saved layout
- "Default Layout" button restores factory defaults

## Non-Goals

- No backend API changes
- No new story-generation capability
- No new LLM prompt design
- No new database fields
- No export redesign
- No removal of existing routes during first implementation
- No mobile-specific redesign beyond responsive collapse

## Success Criteria

- User can open `/workspace/:projectId/studio` and see the radial hub workspace
- Panels are draggable, resizable, and tear-able into floating windows
- Hover preview works for all panels
- Layout persists per project (survives page refresh)
- All 12 panels are available and functional
- Existing routes still work (backward compatibility)
- Frontend lint, typecheck, build, and test pass (670+ tests)

## Implementation Phases

### Phase 1: Core Infrastructure
- Install `react-resizable-panels`
- Rewrite `studioStore.ts` with panel layout state
- Create `StudioFloatingPanel.tsx` wrapper
- Create `StudioRadialHub.tsx` layout manager

### Phase 2: Panel Migration
- Migrate existing 13 studio panels to floating panel system
- Create 3 new panels (Arcs, Structure, Chapters)
- Implement panel menu for visibility toggles

### Phase 3: Interaction Polish
- Drag-and-drop with grid snap
- Resize handles
- Tear-off / reattach functionality
- Layout persistence

### Phase 4: Route Migration
- Update `App.tsx` routes
- Add redirects from old routes to studio
- Update `WorkspaceShell` left rail

### Phase 5: Validation
- Full test suite passes
- Lint, typecheck, build clean
- Manual UX testing across all 4 author entry points

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Drag performance with many panels | Limit to 12 max panels; optimize with React.memo |
| Layout breaks on window resize | Clamp positions to viewport on resize event; "reset layout" button |
| Mobile UX | Collapse to single-panel mode below `xl` breakpoint |
| State sync across panels | Zustand handles it; each panel instance is independent |
| Editor panel vs content panels | Editor is special — always centered, can't be closed, only maximized |
| Tear-off windows losing state | Use React Portal; maintain store connection |

## Related Documents

- `docs/superpowers/research/2026-05-19-radial-hub-workspace-research.md` — author behavior research
- `docs/writing_software_review/comparison.md` — competitive analysis (8 tools)
- `docs/superpowers/specs/2026-05-16-studio-desk-redesign-design.md` — previous Concept A (superseded)
- `docs/superpowers/specs/2026-05-16-floating-panels-implementation.md` — previous floating panels plan (superseded)
