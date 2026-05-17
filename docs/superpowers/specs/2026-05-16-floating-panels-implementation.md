# Floating Workspace — Implementation Plan

Date: 2026-05-16
Scope: Frontend only. Option C from studio layout options. Replaces fixed grid layout with draggable, resizable floating panels.

## Dependencies

| Package | Status | Purpose |
|---------|--------|---------|
| `@dnd-kit/core` | Installed | Drag panels to reorder/reposition |
| `@dnd-kit/utilities` | Installed | CSS classnames, sortable helpers |
| `react-resizable-panels` | **New** | Resize panels (lightweight, ~6KB, React 18 compatible) |

Install: `npm install react-resizable-panels`

## Architecture Changes

### 1. Store: `studioStore.ts` — panel layout state

Replace single `activePanel` + boolean toggles with a layout state model:

```ts
interface FloatingPanel {
  id: string;           // unique panel instance id
  key: StudioPanelKey;  // which panel type
  position: { x: number; y: number };
  size: { width: number; height: number };
  visible: boolean;
  pinned: boolean;
}

interface StudioLayout {
  panels: Record<string, FloatingPanel>;  // keyed by id
  leftRailVisible: boolean;
  leftRailPinned: boolean;
  editorMaximized: boolean;
  layoutPreset: 'default' | 'custom';
}
```

Actions: `addPanel`, `removePanel`, `movePanel`, `resizePanel`, `togglePanel`, `pinPanel`, `maximizeEditor`, `resetLayout`, `saveLayout`, `loadLayout`.

Persist layout to `localStorage` (key: `studio-layout-${projectId}`).

### 2. New Component: `StudioFloatingPanel.tsx`

Wraps any panel content in a draggable, resizable container:

```tsx
interface StudioFloatingPanelProps {
  panel: FloatingPanel;
  projectId: string;
  onMove: (id: string, pos: { x: number; y: number }) => void;
  onResize: (id: string, size: { width: number; height: number }) => void;
  onClose: (id: string) => void;
  onPin: (id: string) => void;
}
```

Uses `@dnd-kit/core` `useDraggable` for repositioning. Uses `react-resizable-panels` `Resizable`/`ResizablePanel` for resize handles. Renders existing panel components through `StudioContextPanel`'s switch logic.

Header bar: panel title, pin toggle, close button.
Resize handles: right edge, bottom edge, bottom-right corner.

### 3. New Component: `StudioWorkspace.tsx`

Replaces the current grid layout in `StudioView.tsx`. Manages the floating panel area:

```tsx
interface StudioWorkspaceProps {
  projectId: string;
}
```

- Dnd context (`DndContext` from `@dnd-kit`)
- Grid/snap background for panel placement
- Renders all visible `StudioFloatingPanel` instances
- Floating toolbar (bottom center) for quick panel toggles
- Status bar (bottom edge) for job/runtime info

### 4. Updated `StudioView.tsx`

```tsx
export function StudioView() {
  const { projectId } = useParams<{ projectId: string }>();
  if (!projectId) return <div>No project selected.</div>;

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
      <StudioCommandBar />
      <StudioWorkspace projectId={projectId} />
    </div>
  );
}
```

Removes the current grid + drawer logic entirely.

### 5. Updated `StudioCommandBar.tsx`

Add verb-to-panel mapping: clicking "Capture" opens a floating Ideas panel, "Generate" opens a floating Generation panel, etc. Add "Layout" button to reset to default or toggle presets.

### 6. Default Layout Preset

On first open (no saved layout), initialize:

| Panel | Position | Size | Pinned |
|-------|----------|------|--------|
| Left rail | x:16, y:16, left-anchored | 160×(100%-32) | yes |
| Editor | x:192, y:16 | flex-fill to context panel | yes |
| Context (Suggestions) | right-anchored, y:16 | 248×(100%-40) | yes |
| Status bar | bottom-anchored | full-width, 28px | yes |

## Drag Behavior

- **Reposition**: `@dnd-kit/core` `useDraggable` + `useSensor(PointerSensor)` — drag from panel header bar only (not content area)
- **Snap to grid**: 8px grid using `closestCorners` collision detection + custom drop animation to nearest snap point
- **Snap zones**: left edge, right edge, top, bottom, center — panels snap to edges and to each other
- **Z-order**: dragged panel auto-brings-to-front (`z-index` managed by store)

## Resize Behavior

- `react-resizable-panels` on right/bottom edges
- Min size: 180px width, 120px height
- Max size: workspace bounds minus 16px padding
- Resize handles visible on hover only

## File Structure

```
frontend/src/
├── stores/
│   └── studioStore.ts              # rewritten: layout state, panel management, persistence
├── components/studio/
│   ├── StudioFloatingPanel.tsx      # NEW: draggable/resizable panel wrapper
│   ├── StudioWorkspace.tsx          # NEW: dnd context, panel area, floating toolbar, status bar
│   ├── StudioCommandBar.tsx         # updated: verb→panel mapping, layout button
│   ├── StudioProjectRail.tsx        # kept as-is, rendered inside floating panel
│   ├── StudioContextPanel.tsx       # kept as-is, rendered inside floating panel
│   └── [existing panel components]  # untouched
└── views/
    └── StudioView.tsx               # simplified: command bar + workspace only
```

## Implementation Order

1. **Install** `react-resizable-panels`
2. **Rewrite `studioStore.ts`** — new layout state, actions, localStorage persistence
3. **Create `StudioFloatingPanel.tsx`** — wrapper with drag handle, resize handles, close/pin
4. **Create `StudioWorkspace.tsx`** — dnd context, panel rendering, floating toolbar, status bar
5. **Update `StudioView.tsx`** — remove grid, use `StudioWorkspace`
6. **Update `StudioCommandBar.tsx`** — verb→open floating panel, add layout reset button
7. **Tests** — store persistence, panel open/close, layout reset
8. **Validate** — lint, typecheck, build, test

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Drag performance with many panels | Limit to 6 max floating panels; virtualize if needed |
| Layout breaks on window resize | Clamp positions to viewport on `resize` event; provide "reset layout" button |
| Mobile UX | Collapse to single-panel mode below `xl` breakpoint; floating toolbar becomes bottom sheet |
| State sync across panels | Zustand handles it; each panel instance is independent |
| Editor panel vs content panels | Editor is a special panel type — always centered, can't be closed, only maximized |

## Estimated Effort

- Store rewrite: ~150 lines
- FloatingPanel: ~200 lines
- Workspace: ~150 lines
- View/CommandBar updates: ~50 lines
- Tests: ~100 lines
- **Total: ~650 lines of new/changed code**
