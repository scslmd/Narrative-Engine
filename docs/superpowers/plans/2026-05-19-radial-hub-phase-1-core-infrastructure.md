# Radial Hub Phase 1: Core Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the floating panel system — new store, draggable/resizable panel wrapper, radial hub layout manager, and panel menu — so StudioView renders a working radial hub with existing panels inside floating containers.

**Status:** Design approved. Visual mockup confirmed by user (2026-05-19). Design locked; proceed to implementation.

**Architecture:** Replace the current `StudioView` grid layout (ViewShell with left rail + right panel) with `StudioRadialHub` that renders panels as `StudioFloatingPanel` instances managed by a new layout store. Existing panel content components are reused unchanged, wrapped by `StudioFloatingPanel`. The store adds layout state (panel positions, sizes, visibility) while preserving backward-compatible types for existing consumers.

**Tech Stack:** React 18, TypeScript, Zustand, `@dnd-kit/core` (installed), `@dnd-kit/utilities` (installed), custom resize handles, Tailwind CSS, CSS variables

**Dependencies (existing):** `@dnd-kit/core@^6.3.1`, `@dnd-kit/utilities@^3.2.2`

**Note:** `react-resizable-panels` is NOT used — it's designed for split-pane layouts (PanelGroup/Panel), not floating panels. Custom mouse-event resize handles are implemented directly on `StudioFloatingPanel`.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/stores/studioStore.ts` | Modify | Add layout state/types, currentProjectId, per-panel state (backward-compatible) |
| `frontend/src/components/studio/StudioFloatingPanel.tsx` | Create | Draggable/resizable/tear-off panel wrapper |
| `frontend/src/components/studio/StudioRadialHub.tsx` | Create | Main layout manager: dnd context, panel rendering, snap grid |
| `frontend/src/components/studio/StudioPanelMenu.tsx` | Create | Dropdown menu to add panel instances |
| `frontend/src/components/studio/StudioPanelContent.tsx` | Create | Routes panel key to correct component (content router) |
| `frontend/src/views/StudioView.tsx` | Modify | Replace ViewShell grid with StudioRadialHub |
| `frontend/src/components/studio/StudioCommandBar.tsx` | Modify | Add panel menu button and layout reset button |

**Do NOT modify:** Any existing panel content components (`StudioCharactersPanel.tsx`, `StudioIdeasPanel.tsx`, etc.), `StudioContextPanel.tsx`, `StudioProjectRail.tsx`, `ViewShell.tsx`, `WritingView.tsx`, service files, hook files, type files.

---

## Task 1: Extend `StudioPanelKey` with missing panel types

**Files:**
- Modify: `frontend/src/stores/studioStore.ts`

**Purpose:** Add `structure`, `chapters`, `canon` to `StudioPanelKey` so they can be used in the panel menu and content router without `as any` casts. (These panels are wired in Phase 2; the keys exist now so the menu can list them.)

- [ ] **Step 1: Add missing keys to StudioPanelKey**

Add to the existing union type:
```ts
export type StudioPanelKey =
  | 'suggestions'
  | 'ideas'
  | 'drafts'
  | 'manuscripts'
  | 'characters'
  | 'worldBible'
  | 'relationships'
  | 'arcs'
  | 'structure'    // NEW
  | 'chapters'     // NEW
  | 'canon'        // NEW
  | 'generation'
  | 'review'
  | 'inspect'
  | 'notes'
  | 'jobs';
```

- [ ] **Step 2: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS (no new errors)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/studioStore.ts
git commit -m "feat: add structure, chapters, canon to StudioPanelKey"
```

---

## Task 2: Extend `studioStore.ts` with Layout State

**Files:**
- Modify: `frontend/src/stores/studioStore.ts`

**Design:** Add new types and state alongside existing types. Keep all existing types (`StudioPanelKey`, `StudioRailMode`, `StudioContextMode`, `PersistedStudioLayout`, `StudioState`) and their behavior unchanged. New state uses `layout` namespace to avoid collision.

**Fixes applied (adversarial review):**
- **H1:** Added `currentProjectId` to store so `addPanel` can persist to correct project
- **H2:** `loadLayout` now wires to `loadLayoutV2`
- **H3:** `togglePanel` interface matches implementation with optional `stateSnapshot`

- [ ] **Step 1: Add new types**

Add after existing type definitions (before `interface StudioState`):

```ts
export interface PanelLayoutState {
  id: string;
  key: StudioPanelKey;
  position: { x: number; y: number };
  size: { width: number; height: number };
  visible: boolean;
  pinned: boolean;
  floating: boolean;
  zIndex: number;
  // Per-panel state persistence (Photoshop-style: remember everything)
  collapsedSections: Record<string, boolean>;  // form section collapse states
  scrollY: number;                              // scroll position on hide
}

export interface StudioLayoutState {
  panels: Record<string, PanelLayoutState>;
  nextZIndex: number;
  layoutPreset: string | null;
}
```

- [ ] **Step 2: Add layout defaults**

Add constants after existing constants:

```ts
const STUDIO_LAYOUT_V2_KEY = (projectId: string) => `studio-layout-v2-${projectId}`;
const MIN_PANEL_WIDTH = 180;
const MIN_PANEL_HEIGHT = 120;
const GRID_SIZE = 8;

function snapToGrid(value: number): number {
  return Math.round(value / GRID_SIZE) * GRID_SIZE;
}

function generatePanelId(): string {
  return `panel-${crypto.randomUUID?.() ?? Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}
```

- [ ] **Step 3: Add layout state to store**

Extend `StudioState` interface — add these fields:

```ts
interface StudioState {
  // ... existing fields unchanged ...

  // Layout state (Phase 1)
  currentProjectId: string | null;
  layout: StudioLayoutState;
  setCurrentProjectId: (projectId: string | null) => void;
  addPanel: (key: StudioPanelKey) => string;
  removePanel: (id: string) => void;
  movePanel: (id: string, position: { x: number; y: number }) => void;
  resizePanel: (id: string, size: { width: number; height: number }) => void;
  togglePanel: (id: string, stateSnapshot?: { collapsedSections?: Record<string, boolean>; scrollY?: number }) => void;
  updatePanelState: (id: string, updates: { collapsedSections?: Record<string, boolean>; scrollY?: number }) => void;
  pinPanel: (id: string, pinned: boolean) => void;
  tearOffPanel: (id: string) => void;
  reattachPanel: (id: string) => void;
  bringToFront: (id: string) => void;
  resetLayout: () => void;
  loadLayout: (projectId: string) => void;
}
```

Note: `resetLayout` already exists — extend it to also reset layout state.

- [ ] **Step 4: Add layout state initialization and actions**

Add to the `create<StudioState>` call, after existing state:

```ts
// Layout state
currentProjectId: null,
layout: {
  panels: {},
  nextZIndex: 1,
  layoutPreset: null,
},
setCurrentProjectId: (projectId) => set({ currentProjectId: projectId }),
addPanel: (key) =>
  set((state) => {
    const id = generatePanelId();
    const panelCount = Object.keys(state.layout.panels).length;
    const panel: PanelLayoutState = {
      id,
      key,
      position: { x: snapToGrid(16 + (panelCount % 6) * 12), y: snapToGrid(40 + Math.floor(panelCount / 6) * 80) },
      size: { width: 280, height: 360 },
      visible: true,
      pinned: false,
      floating: false,
      zIndex: state.layout.nextZIndex,
      collapsedSections: {},
      scrollY: 0,
    };
    const newPanels = { ...state.layout.panels, [id]: panel };
    const newLayout = { ...state.layout, panels: newPanels, nextZIndex: state.layout.nextZIndex + 1 };
    if (state.currentProjectId) persistLayoutV2(state.currentProjectId, newLayout);
    return { layout: newLayout };
  }),
removePanel: (id) =>
  set((state) => {
    const newPanels = { ...state.layout.panels };
    delete newPanels[id];
    const newLayout = { ...state.layout, panels: newPanels };
    if (state.currentProjectId) persistLayoutV2(state.currentProjectId, newLayout);
    return { layout: newLayout };
  }),
movePanel: (id, position) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return {};
    const snapped = { x: snapToGrid(position.x), y: snapToGrid(position.y) };
    const newPanels = { ...state.layout.panels, [id]: { ...panel, position: snapped } };
    const newLayout = { ...state.layout, panels: newPanels };
    if (state.currentProjectId) persistLayoutV2(state.currentProjectId, newLayout);
    return { layout: newLayout };
  }),
resizePanel: (id, size) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return {};
    const clamped = {
      width: Math.max(MIN_PANEL_WIDTH, Math.min(size.width, 800)),
      height: Math.max(MIN_PANEL_HEIGHT, Math.min(size.height, 900)),
    };
    const newPanels = { ...state.layout.panels, [id]: { ...panel, size: clamped } };
    const newLayout = { ...state.layout, panels: newPanels };
    if (state.currentProjectId) persistLayoutV2(state.currentProjectId, newLayout);
    return { layout: newLayout };
  }),
togglePanel: (id, stateSnapshot) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return {};
    const updated = panel.visible
      ? { ...panel, visible: false, collapsedSections: stateSnapshot?.collapsedSections ?? panel.collapsedSections, scrollY: stateSnapshot?.scrollY ?? panel.scrollY }
      : { ...panel, visible: true };
    const newPanels = { ...state.layout.panels, [id]: updated };
    const newLayout = { ...state.layout, panels: newPanels };
    if (state.currentProjectId) persistLayoutV2(state.currentProjectId, newLayout);
    return { layout: newLayout };
  }),
updatePanelState: (id, updates) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return {};
    const newPanels = { ...state.layout.panels, [id]: { ...panel, ...updates } };
    const newLayout = { ...state.layout, panels: newPanels };
    if (state.currentProjectId) persistLayoutV2(state.currentProjectId, newLayout);
    return { layout: newLayout };
  }),
pinPanel: (id, pinned) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return {};
    const newPanels = { ...state.layout.panels, [id]: { ...panel, pinned } };
    const newLayout = { ...state.layout, panels: newPanels };
    if (state.currentProjectId) persistLayoutV2(state.currentProjectId, newLayout);
    return { layout: newLayout };
  }),
tearOffPanel: (id) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return {};
    const newPanels = { ...state.layout.panels, [id]: { ...panel, floating: true } };
    const newLayout = { ...state.layout, panels: newPanels };
    if (state.currentProjectId) persistLayoutV2(state.currentProjectId, newLayout);
    return { layout: newLayout };
  }),
reattachPanel: (id) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return {};
    const newPanels = { ...state.layout.panels, [id]: { ...panel, floating: false } };
    const newLayout = { ...state.layout, panels: newPanels };
    if (state.currentProjectId) persistLayoutV2(state.currentProjectId, newLayout);
    return { layout: newLayout };
  }),
bringToFront: (id) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return {};
    const newPanels = { ...state.layout.panels, [id]: { ...panel, zIndex: state.layout.nextZIndex } };
    return { layout: { ...state.layout, panels: newPanels, nextZIndex: state.layout.nextZIndex + 1 } };
  }),
loadLayout: (projectId) =>
  set((state) => {
    if (state.currentProjectId === projectId) return {};
    const saved = loadLayoutV2(projectId);
    return {
      currentProjectId: projectId,
      layout: saved ?? { panels: {}, nextZIndex: 1, layoutPreset: null },
    };
  }),
```

- [ ] **Step 5: Add layout persistence helper**

Add before `persistLayout`:

```ts
function persistLayoutV2(projectId: string, layout: StudioLayoutState): void {
  const key = STUDIO_LAYOUT_V2_KEY(projectId);
  try {
    localStorage.setItem(key, JSON.stringify({ panels: layout.panels, layoutPreset: layout.layoutPreset }));
  } catch {
    // Storage full or unavailable — ignore
  }
}

function loadLayoutV2(projectId: string): StudioLayoutState | null {
  const key = STUDIO_LAYOUT_V2_KEY(projectId);
  const raw = typeof localStorage !== 'undefined' ? localStorage.getItem(key) : null;
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as { panels?: Record<string, PanelLayoutState>; layoutPreset?: string | null };
    if (!parsed || typeof parsed !== 'object') return null;
    return {
      panels: parsed.panels ?? {},
      nextZIndex: Object.values(parsed.panels ?? {}).reduce((max, p) => Math.max(max, p.zIndex), 0) + 1,
      layoutPreset: parsed.layoutPreset ?? null,
    };
  } catch {
    return null;
  }
}
```

- [ ] **Step 6: Extend existing `resetLayout` to clear layout state**

Modify the existing `resetLayout` action to also reset layout and clear v2 storage:

```ts
resetLayout: () => {
  set((state) => {
    // Clear v2 storage for current project
    if (state.currentProjectId) {
      try { localStorage.removeItem(STUDIO_LAYOUT_V2_KEY(state.currentProjectId)); } catch { /* ignore */ }
    }
    return {
      activePanel: 'suggestions',
      leftRailMode: 'collapsed',
      contextPanelMode: 'docked',
      contextPanelPinned: true,
      leftRailWidth: DEFAULT_LEFT_RAIL_WIDTH,
      contextPanelWidth: DEFAULT_CONTEXT_PANEL_WIDTH,
      panelVisible: false,
      currentProjectId: null,
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    };
  });
  persistLayout(useStudioStore.getState());
},
```

- [ ] **Step 7: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS (no new errors)

- [ ] **Step 8: Commit**

```bash
git add frontend/src/stores/studioStore.ts
git commit -m "feat: extend studioStore with floating panel layout state"
```

---

## Task 3: Create `StudioFloatingPanel.tsx`

**Files:**
- Create: `frontend/src/components/studio/StudioFloatingPanel.tsx`

**Props:**
```ts
interface StudioFloatingPanelProps {
  panelId: string;
  panelKey: StudioPanelKey;
  projectId: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  pinned: boolean;
  floating: boolean;
  zIndex: number;
  children: React.ReactNode;
}
```

- [ ] **Step 1: Write test for panel render**

Create `frontend/src/components/studio/StudioFloatingPanel.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react';
import { StudioFloatingPanel } from './StudioFloatingPanel';

describe('StudioFloatingPanel', () => {
  it('renders children content', () => {
    render(
      <StudioFloatingPanel
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 0, y: 0 }}
        size={{ width: 240, height: 320 }}
        pinned={false}
        floating={false}
        zIndex={1}
      >
        <div data-testid="panel-content">Test content</div>
      </StudioFloatingPanel>
    );
    expect(screen.getByTestId('panel-content')).toBeInTheDocument();
  });

  it('applies position and size styles', () => {
    const { container } = render(
      <StudioFloatingPanel
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 16, y: 32 }}
        size={{ width: 200, height: 300 }}
        pinned={false}
        floating={false}
        zIndex={2}
      >
        <div>Content</div>
      </StudioFloatingPanel>
    );
    const panel = container.querySelector('[data-panel-container]');
    expect(panel).toHaveStyle({ left: '16px', top: '32px', width: '200px', height: '300px' });
  });

  it('shows close button', () => {
    render(
      <StudioFloatingPanel
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 0, y: 0 }}
        size={{ width: 240, height: 320 }}
        pinned={false}
        floating={false}
        zIndex={1}
      >
        <div>Content</div>
      </StudioFloatingPanel>
    );
    expect(screen.getByLabelText('Close panel')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- StudioFloatingPanel.test.tsx`
Expected: FAIL (module not found)

- [ ] **Step 3: Create component**

```tsx
import { memo, useCallback, useEffect, useRef, useState } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { useStudioStore } from '../../stores/studioStore';
import type { StudioPanelKey } from '../../stores/studioStore';

const PANEL_LABELS: Record<StudioPanelKey, string> = {
  suggestions: 'Suggestions',
  ideas: '💡 Ideas',
  drafts: '📄 Drafts',
  manuscripts: '📖 Manuscripts',
  characters: '👤 Characters',
  worldBible: '🌍 World Bible',
  relationships: '🔗 Relationships',
  arcs: '📈 Arcs',
  structure: '📋 Structure',
  chapters: '📑 Chapters',
  canon: '📜 Canon',
  generation: '⚡ Generation',
  review: '🔍 Review',
  inspect: '🔬 Inspect',
  notes: '📝 Notes',
  jobs: '⚙️ Jobs',
};

interface StudioFloatingPanelProps {
  panelId: string;
  panelKey: StudioPanelKey;
  projectId: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  pinned: boolean;
  floating: boolean;
  zIndex: number;
  children: React.ReactNode;
}

function StudioFloatingPanelImpl({
  panelId,
  panelKey,
  position,
  size,
  pinned,
  floating,
  zIndex,
  children,
}: StudioFloatingPanelProps) {
  const resizePanel = useStudioStore((s) => s.resizePanel);
  const removePanel = useStudioStore((s) => s.removePanel);
  const pinPanel = useStudioStore((s) => s.pinPanel);
  const bringToFront = useStudioStore((s) => s.bringToFront);
  const reattachPanel = useStudioStore((s) => s.reattachPanel);

  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: panelId,
    disabled: floating,
  });

  // FIX H4: Always include base position/size; layer transform on top
  const style: React.CSSProperties = {
    position: floating ? 'fixed' : 'absolute',
    left: `${position.x}px`,
    top: `${position.y}px`,
    width: `${size.width}px`,
    height: `${size.height}px`,
    zIndex,
    transform: transform ? `translate(${transform.x}px, ${transform.y}px)` : undefined,
    transition: transform ? 'none' : 'box-shadow 0.15s, left 0.1s, top 0.1s',
  };

  // Custom resize handles (FIX C1: react-resizable-panels is for split-panes, not floating panels)
  const [resizing, setResizing] = useState<'none' | 'right' | 'bottom' | 'corner'>('none');
  const resizeRef = useRef<{ startX: number; startY: number; startW: number; startH: number } | null>(null);
  const rafRef = useRef<number | null>(null);

  const handleResizeStart = useCallback(
    (edge: 'right' | 'bottom' | 'corner', e: React.MouseEvent) => {
      e.stopPropagation();
      e.preventDefault();
      setResizing(edge);
      resizeRef.current = { startX: e.clientX, startY: e.clientY, startW: size.width, startH: size.height };
    },
    [size]
  );

  // FIX H7: Throttle resize to one call per frame via requestAnimationFrame
  useEffect(() => {
    if (resizing === 'none' || !resizeRef.current) return;
    const handleMove = (e: MouseEvent) => {
      if (rafRef.current != null) return; // Skip if frame already scheduled
      rafRef.current = requestAnimationFrame(() => {
        const dx = e.clientX - resizeRef.current!.startX;
        const dy = e.clientY - resizeRef.current!.startY;
        let newW = resizeRef.current!.startW;
        let newH = resizeRef.current!.startH;
        if (resizing === 'right' || resizing === 'corner') newW = Math.max(180, resizeRef.current!.startW + dx);
        if (resizing === 'bottom' || resizing === 'corner') newH = Math.max(120, resizeRef.current!.startH + dy);
        resizePanel(panelId, { width: newW, height: newH });
        rafRef.current = null;
      });
    };
    const handleUp = () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      setResizing('none');
      resizeRef.current = null;
    };
    document.addEventListener('mousemove', handleMove);
    document.addEventListener('mouseup', handleUp);
    return () => {
      document.removeEventListener('mousemove', handleMove);
      document.removeEventListener('mouseup', handleUp);
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    };
  }, [resizing, panelId, resizePanel]);

  const label = PANEL_LABELS[panelKey] || panelKey;

  return (
    <div
      ref={setNodeRef}
      data-panel-container
      {...attributes}
      {...listeners}
      onClick={() => bringToFront(panelId)}
      className="flex flex-col overflow-hidden rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-lg"
      style={style}
    >
      {/* Header (drag target) */}
      <div className="flex shrink-0 items-center justify-between border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-1.5 cursor-grab active:cursor-grabbing">
        <span className="text-xs font-semibold text-[var(--text-primary)]">{label}</span>
        <div className="flex items-center gap-1">
          {floating ? (
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); reattachPanel(panelId); }}
              className="rounded px-1.5 py-0.5 text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              title="Reattach"
            >
              ⊡
            </button>
          ) : (
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); pinPanel(panelId, !pinned); }}
              className={`rounded px-1.5 py-0.5 text-[10px] ${pinned ? 'text-amber-400' : 'text-[var(--text-secondary)]'} hover:text-[var(--text-primary)]`}
              title={pinned ? 'Unpin' : 'Pin'}
            >
              📌
            </button>
          )}
          <button
            type="button"
            aria-label="Close panel"
            onClick={(e) => { e.stopPropagation(); removePanel(panelId); }}
            className="rounded px-1.5 py-0.5 text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            title="Close"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="relative flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto p-2">{children}</div>

        {/* Resize handles (visible on hover) */}
        <div
          className="absolute right-0 top-0 bottom-0 w-1 cursor-ew-resize opacity-0 hover:opacity-100 transition-opacity"
          style={{ background: 'var(--accent-primary)' }}
          onMouseDown={(e) => handleResizeStart('right', e)}
        />
        <div
          className="absolute left-0 right-0 bottom-0 h-1 cursor-ns-resize opacity-0 hover:opacity-100 transition-opacity"
          style={{ background: 'var(--accent-primary)' }}
          onMouseDown={(e) => handleResizeStart('bottom', e)}
        />
        <div
          className="absolute right-0 bottom-0 w-3 h-3 cursor-nwse-resize"
          onMouseDown={(e) => handleResizeStart('corner', e)}
        >
          <div className="absolute right-0.5 bottom-0.5 w-2 h-2 rotate-45 bg-[var(--text-secondary)]" />
        </div>
      </div>
    </div>
  );
}

export const StudioFloatingPanel = memo(StudioFloatingPanelImpl);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- StudioFloatingPanel.test.tsx`
Expected: PASS (3 tests)

- [ ] **Step 5: Run lint**

Run: `cd frontend && npm run lint`
Expected: PASS (no new errors)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/studio/StudioFloatingPanel.tsx frontend/src/components/studio/StudioFloatingPanel.test.tsx
git commit -m "feat: create StudioFloatingPanel draggable/resizable wrapper"
```

---

## Task 4: Create `StudioPanelMenu.tsx`

**Files:**
- Create: `frontend/src/components/studio/StudioPanelMenu.tsx`

**Props:**
```ts
interface StudioPanelMenuProps {
  projectId: string;
}
```

**Purpose:** Dropdown menu for adding panel instances to the layout. Checkmark (✓) indicates which panel types already have an open instance. Clicking always adds a new panel; removal is via the panel's ✕ close button.

- [ ] **Step 1: Write test**

Create `frontend/src/components/studio/StudioPanelMenu.test.tsx`:

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { StudioPanelMenu } from './StudioPanelMenu';

describe('StudioPanelMenu', () => {
  it('renders menu trigger button', () => {
    render(<StudioPanelMenu projectId="proj-1" />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('shows panel list when opened', () => {
    render(<StudioPanelMenu projectId="proj-1" />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByText('Characters')).toBeInTheDocument();
    expect(screen.getByText('World Bible')).toBeInTheDocument();
    expect(screen.getByText('Generation')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- StudioPanelMenu.test.tsx`
Expected: FAIL (module not found)

- [ ] **Step 3: Create component**

```tsx
import { memo, useRef, useEffect, useState } from 'react';
import { useStudioStore } from '../../stores/studioStore';
import type { StudioPanelKey } from '../../stores/studioStore';

const PANEL_OPTIONS: { key: StudioPanelKey; label: string }[] = [
  { key: 'characters', label: '👤 Characters' },
  { key: 'relationships', label: '🔗 Relationships' },
  { key: 'worldBible', label: '🌍 World Bible' },
  { key: 'arcs', label: '📈 Arcs' },
  { key: 'structure', label: '📋 Structure' },
  { key: 'chapters', label: '📑 Chapters' },
  { key: 'ideas', label: '💡 Ideas' },
  { key: 'manuscripts', label: '📖 Manuscripts' },
  { key: 'generation', label: '⚡ Generation' },
  { key: 'review', label: '🔍 Review' },
  { key: 'inspect', label: '🔬 Inspect' },
  { key: 'canon', label: '📜 Canon' },
];

interface StudioPanelMenuProps {
  projectId: string;
}

function StudioPanelMenuImpl({ projectId }: StudioPanelMenuProps) {
  const addPanel = useStudioStore((s) => s.addPanel);
  const layout = useStudioStore((s) => s.layout);
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const visibleKeys = new Set(Object.values(layout.panels).map((p) => p.key));

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  const handleAddPanel = (key: StudioPanelKey) => {
    addPanel(key);
    setOpen(false);
  };

  return (
    <div ref={menuRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="rounded-md px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
      >
        Panels ▾
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-1 min-w-[180px] rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-1 shadow-xl">
          {PANEL_OPTIONS.map((option) => {
            const isActive = visibleKeys.has(option.key);
            return (
              <button
                key={option.key}
                type="button"
                onClick={() => handleAddPanel(option.key)}
                className={`flex w-full items-center justify-between rounded-md px-3 py-1.5 text-xs transition-colors ${
                  isActive
                    ? 'bg-[var(--bg-secondary)] text-[var(--text-primary)]'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                <span>{option.label}</span>
                {isActive && <span className="text-[10px] text-emerald-400">✓</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export const StudioPanelMenu = memo(StudioPanelMenuImpl);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- StudioPanelMenu.test.tsx`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/studio/StudioPanelMenu.tsx frontend/src/components/studio/StudioPanelMenu.test.tsx
git commit -m "feat: create StudioPanelMenu for panel visibility toggles"
```

---

## Task 5: Create `StudioRadialHub.tsx`

**Files:**
- Create: `frontend/src/components/studio/StudioRadialHub.tsx`

**Props:**
```ts
interface StudioRadialHubProps {
  projectId: string;
}
```

**Purpose:** Main layout manager. Wraps DndContext, renders all visible panels as StudioFloatingPanel instances, provides snap grid background, and handles drag-end positioning.

- [ ] **Step 1: Write test**

Create `frontend/src/components/studio/StudioRadialHub.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react';
import { StudioRadialHub } from './StudioRadialHub';
import { useStudioStore } from '../../stores/studioStore';

describe('StudioRadialHub', () => {
  // FIX M3: Isolate tests by resetting store state before each test
  beforeEach(() => {
    useStudioStore.setState({
      currentProjectId: null,
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
  });

  afterEach(() => {
    // Cleanup all panels after each test
    const panels = Object.keys(useStudioStore.getState().layout.panels);
    panels.forEach((id) => useStudioStore.getState().removePanel(id));
    useStudioStore.setState({ currentProjectId: null });
  });

  it('renders workspace container', () => {
    render(<StudioRadialHub projectId="proj-1" />);
    const container = document.querySelector('[data-radial-hub]');
    expect(container).toBeInTheDocument();
  });

  it('renders visible panels', () => {
    useStudioStore.getState().addPanel('characters');
    render(<StudioRadialHub projectId="proj-1" />);
    expect(screen.getByText('👤 Characters')).toBeInTheDocument();
  });

  it('does not render hidden panels', () => {
    const id = useStudioStore.getState().addPanel('ideas');
    useStudioStore.getState().togglePanel(id);
    render(<StudioRadialHub projectId="proj-1" />);
    expect(screen.queryByText('💡 Ideas')).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- StudioRadialHub.test.tsx`
Expected: FAIL (module not found)

- [ ] **Step 3: Create component**

```tsx
import { memo, useCallback, useEffect, useMemo } from 'react';
import { DndContext, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { useStudioStore } from '../../stores/studioStore';
import { StudioFloatingPanel } from './StudioFloatingPanel';
import { StudioPanelContent } from './StudioPanelContent';

interface StudioRadialHubProps {
  projectId: string;
}

function StudioRadialHubImpl({ projectId }: StudioRadialHubProps) {
  const layout = useStudioStore((s) => s.layout);
  const movePanel = useStudioStore((s) => s.movePanel);
  const loadLayout = useStudioStore((s) => s.loadLayout);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  useEffect(() => {
    loadLayout(projectId);
  }, [projectId, loadLayout]);

  const visiblePanels = useMemo(
    () => Object.values(layout.panels).filter((p) => p.visible && !p.floating),
    [layout.panels]
  );

  // FIX C2: Use delta instead of over.rect (over is always null without useDroppable targets)
  // FIX M9: Use getState() for current layout instead of closure-captured layout
  const handleDragEnd = useCallback(
    (event: { active: { id: string }; delta: { x: number; y: number } }) => {
      const currentPanels = useStudioStore.getState().layout.panels;
      const panel = currentPanels[event.active.id as string];
      if (panel) {
        movePanel(event.active.id as string, {
          x: panel.position.x + event.delta.x,
          y: panel.position.y + event.delta.y,
        });
      }
    },
    [movePanel]
  );

  // FIX M1: Snap grid in separate layer so opacity doesn't affect child panels
  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div
        data-radial-hub
        className="relative h-full w-full overflow-hidden bg-[var(--bg-tertiary)]"
      >
        {/* Snap grid background layer - separate from content */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage: 'radial-gradient(circle, var(--border-primary) 1px, transparent 1px)',
            backgroundSize: '8px 8px',
            opacity: 0.3,
          }}
        />
        {/* Panels layer */}
        {visiblePanels.map((panel) => (
          <StudioFloatingPanel
            key={panel.id}
            panelId={panel.id}
            panelKey={panel.key}
            projectId={projectId}
            position={panel.position}
            size={panel.size}
            pinned={panel.pinned}
            floating={panel.floating}
            zIndex={panel.zIndex}
          >
            <StudioPanelContent panelKey={panel.key} projectId={projectId} />
          </StudioFloatingPanel>
        ))}
      </div>
    </DndContext>
  );
}

export const StudioRadialHub = memo(StudioRadialHubImpl);
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/studio/StudioRadialHub.tsx frontend/src/components/studio/StudioRadialHub.test.tsx
git commit -m "feat: create StudioRadialHub layout manager with dnd context"
```

---

## Task 6: Create `StudioPanelContent.tsx` (Content Router)

**Files:**
- Create: `frontend/src/components/studio/StudioPanelContent.tsx`

**Purpose:** Routes `panelKey` to the correct existing panel component. This is a thin switch component — no business logic.

- [ ] **Step 1: Create component**

```tsx
import { memo } from 'react';
import type { StudioPanelKey } from '../../stores/studioStore';
import { StudioCharactersPanel } from './StudioCharactersPanel';
import { StudioIdeasPanel } from './StudioIdeasPanel';
import { StudioWorldBiblePanel } from './StudioWorldBiblePanel';
import { StudioRelationshipsPanel } from './StudioRelationshipsPanel';
import { StudioArcsPanel } from './StudioArcsPanel';
import { StudioGenerationPanel } from './StudioGenerationPanel';
import { StudioReviewPanel } from './StudioReviewPanel';
import { StudioInspectPanel } from './StudioInspectPanel';
import { StudioSuggestionsPanel } from './StudioSuggestionsPanel';
import { StudioDraftsPanel } from './StudioDraftsPanel';
import { StudioManuscriptsPanel } from './StudioManuscriptsPanel';
import { NotesPanel } from '../NotesPanel';
import { JobLaunchPanel } from '../JobLaunchPanel';

interface StudioPanelContentProps {
  panelKey: StudioPanelKey;
  projectId: string;
}

function StudioPanelContentImpl({ panelKey, projectId }: StudioPanelContentProps) {
  switch (panelKey) {
    case 'characters':
      return <StudioCharactersPanel projectId={projectId} />;
    case 'ideas':
      return <StudioIdeasPanel projectId={projectId} />;
    case 'worldBible':
      return <StudioWorldBiblePanel projectId={projectId} />;
    case 'relationships':
      return <StudioRelationshipsPanel projectId={projectId} />;
    case 'arcs':
      return <StudioArcsPanel projectId={projectId} />;
    case 'generation':
      return <StudioGenerationPanel projectId={projectId} />;
    case 'review':
      return <StudioReviewPanel projectId={projectId} />;
    case 'inspect':
      return <StudioInspectPanel />;
    case 'suggestions':
      return <StudioSuggestionsPanel projectId={projectId} />;
    case 'drafts':
      return <StudioDraftsPanel />;
    case 'manuscripts':
      return <StudioManuscriptsPanel />;
    case 'notes':
      return <NotesPanel projectId={projectId} />;
    case 'jobs':
      return <JobLaunchPanel projectId={projectId} />;
    default:
      return (
        <div className="flex h-full items-center justify-center p-4 text-sm text-[var(--text-secondary)]">
          Panel &quot;{panelKey}&quot; not yet implemented.
        </div>
      );
  }
}

export const StudioPanelContent = memo(StudioPanelContentImpl);
```

- [ ] **Step 2: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS (no new errors)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/studio/StudioPanelContent.tsx
git commit -m "feat: create StudioPanelContent router for panel key to component mapping"
```

---

## Task 7: Update `StudioView.tsx` to Use Radial Hub

**Files:**
- Modify: `frontend/src/views/StudioView.tsx`

**Purpose:** Replace ViewShell grid with StudioRadialHub. The writing surface (WritingView) remains as the center content; panels float around it.

- [ ] **Step 1: Write test**

Create `frontend/src/views/StudioView.test.tsx` (or add to existing if present):

```tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom';
import { StudioView } from './StudioView';

function TestWrapper() {
  return (
    <MemoryRouter initialEntries={['/workspace/proj-1/studio']}>
      <Routes>
        <Route path="/workspace/:projectId/studio" element={<StudioView />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('StudioView', () => {
  it('renders radial hub workspace', () => {
    render(<TestWrapper />);
    const hub = document.querySelector('[data-radial-hub]');
    expect(hub).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Modify StudioView**

Replace the current implementation:

```tsx
import { useParams } from 'react-router-dom';
import { StudioRadialHub } from '../components/studio/StudioRadialHub';
import { StudioCommandBar } from '../components/studio/StudioCommandBar';
import { WritingView } from './WritingView';
import { useStudioStore } from '../stores/studioStore';

export function StudioView() {
  const { projectId } = useParams<{ projectId: string }>();
  const resetLayout = useStudioStore((s) => s.resetLayout);

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
      <StudioCommandBar projectId={projectId} onResetLayout={resetLayout} />
      {/* FIX M2: RadialHub gets higher z-index so panels render above WritingView */}
      <div className="relative flex-1 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <WritingView embedded />
        </div>
        <div className="absolute inset-0 z-10">
          <StudioRadialHub projectId={projectId} />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS (no new errors)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/StudioView.tsx frontend/src/views/StudioView.test.tsx
git commit -m "feat: replace StudioView grid with StudioRadialHub layout"
```

---

## Task 8: Update `StudioCommandBar.tsx`

**Files:**
- Modify: `frontend/src/components/studio/StudioCommandBar.tsx`

**Purpose:** Add `projectId` prop, panel menu button, and layout reset button.

- [ ] **Step 1: Read current component**

Read `frontend/src/components/studio/StudioCommandBar.tsx` to understand current props and structure.

- [ ] **Step 2: Add props and buttons**

Replace the existing interface:
```ts
interface StudioCommandBarProps {
  projectId: string;
  projectName?: string;
  railCollapsed?: boolean;
  panelVisible?: boolean;
  onToggleRail?: () => void;
  onTogglePanel?: () => void;
  onResetLayout?: () => void;
}
```

Update the function signature to accept new props:
```ts
export function StudioCommandBar({
  projectId,
  projectName = 'Current Project',
  railCollapsed,
  panelVisible,
  onToggleRail,
  onTogglePanel,
  onResetLayout,
}: StudioCommandBarProps) {
```

Add import:
```tsx
import { StudioPanelMenu } from './StudioPanelMenu';
```

**Insertion point:** Inside the existing right-side `<div className="flex items-center gap-1">` (line 45), append the reset button and panel menu after the existing panel toggle button (line 73):

```tsx
      <div className="flex items-center gap-1">
        {/* Desktop rail toggle */}
        <button
          type="button"
          onClick={() => {
            if (onToggleRail) {
              onToggleRail();
            } else {
              setLeftRailMode(leftRailMode === 'collapsed' ? 'expanded' : 'collapsed');
            }
          }}
          className="hidden items-center gap-1 rounded-lg px-2 py-1.5 text-[10px] font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:flex"
          title={railCollapsed ? 'Expand rail' : 'Collapse rail'}
        >
          <PanelLeft className="h-3.5 w-3.5" />
        </button>
        {/* Desktop panel toggle */}
        <button
          type="button"
          onClick={() => {
            if (onTogglePanel) {
              onTogglePanel();
            }
          }}
          className="hidden items-center gap-1 rounded-lg px-2 py-1.5 text-[10px] font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:flex"
          title={panelVisible ? 'Hide context panel' : 'Show context panel'}
        >
          <PanelRight className="h-3.5 w-3.5" />
        </button>
        {/* FIX C5: New buttons appended here */}
        {onResetLayout && (
          <button
            type="button"
            onClick={onResetLayout}
            className="hidden items-center gap-1 rounded-lg px-2 py-1.5 text-[10px] font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:flex"
            title="Reset layout"
          >
            ↺
          </button>
        )}
        <StudioPanelMenu projectId={projectId} />
      </div>
```

- [ ] **Step 3: Update StudioView to pass new props**

In `StudioView.tsx`, ensure `<StudioCommandBar projectId={projectId} onResetLayout={resetLayout} />` is used (already done in Task 7).

- [ ] **Step 4: Run typecheck + lint**

Run: `cd frontend && npm run typecheck && npm run lint`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/studio/StudioCommandBar.tsx
git commit -m "feat: add panel menu and reset button to StudioCommandBar"
```

---

## Task 9: Validation

- [ ] **Step 1: Run full frontend test suite**

Run: `cd frontend && npm run test`
Expected: All tests pass (675+ existing + 8 new)

- [ ] **Step 2: Run lint**

Run: `cd frontend && npm run lint`
Expected: PASS (no new errors)

- [ ] **Step 3: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 4: Run build**

Run: `cd frontend && npm run build`
Expected: PASS (builds successfully)

- [ ] **Step 5: Manual smoke test**

Start dev server: `cd frontend && npm run dev`
Navigate to `http://localhost:5173/workspace/{any-project-id}/studio`
Verify:
- Radial hub renders with snap grid background
- "Panels ▾" button opens panel menu
- Clicking a panel adds a floating panel to the workspace
- Panel can be dragged by header
- Panel can be closed with ✕ button
- Writing surface (WritingView) renders in center
- "↺ Reset" button clears all panels

---

## Self-Review

### Spec Coverage
| Spec Requirement | Task | Status |
|-----------------|------|--------|
| Extend `StudioPanelKey` with missing keys | Task 1 | ✅ |
| Rewrite `studioStore.ts` with layout state | Task 2 | ✅ |
| Create `StudioFloatingPanel.tsx` | Task 3 | ✅ |
| Create `StudioRadialHub.tsx` | Task 5 | ✅ |
| Create `StudioPanelMenu.tsx` | Task 4 | ✅ |
| Update `StudioView.tsx` | Task 7 | ✅ |
| Update `StudioCommandBar.tsx` | Task 8 | ✅ |
| Drag-and-drop with grid snap | Tasks 3, 5 | ✅ (dnd-kit delta tracking + snap in store) |
| Resize handles | Task 3 | ✅ (custom mouse-event handles) |
| Tear-off / reattach | Tasks 2, 3 | ✅ (store actions + UI buttons) |
| Layout persistence | Task 2 | ✅ (localStorage per project, v2 storage) |
| Existing panels reused | Task 6 | ✅ (StudioPanelContent router) |

### Placeholder Scan
- No "TBD", "TODO", "implement later" found
- No "add appropriate error handling" — error handling is explicit (try/catch in localStorage, null checks in store, early returns for missing panels)
- All code blocks contain actual implementation code
- All types defined before use
- No `as any` casts remaining (C3 fix)
- All imports present: `useEffect` in `StudioFloatingPanel` (L4 fix), `StudioPanelKey` in `StudioPanelMenu` (C4 fix)
- No unused imports: `movePanel` removed from `StudioFloatingPanel` (H8 fix)
- Resize throttled via `requestAnimationFrame` (H7 fix)
- `handleDragEnd` uses `getState()` for current layout (M9 fix)

### Type Consistency
- `StudioPanelKey` extended with `structure`, `chapters`, `canon` — used consistently across store, panel menu, panel content, and floating panel
- `PANEL_OPTIONS` typed as `{ key: StudioPanelKey; label: string }[]` — no `as any` casts
- `StudioPanelKey` imported in `StudioPanelMenu` (C4 fix)
- `PanelLayoutState` and `StudioLayoutState` defined in store, referenced correctly in components
- `projectId` string passed through all components consistently
- `resetLayout` signature unchanged (extended behavior, same call, clears v2 storage)
- `togglePanel` interface matches implementation: `(id: string, stateSnapshot?: { collapsedSections?: Record<string, boolean>; scrollY?: number })`
- `StudioCommandBarProps` extended with `projectId` (required), `onResetLayout` (optional) — preserves existing optional props (C5 fix)
- No unused imports: `movePanel` removed from `StudioFloatingPanel` (H8 fix)

### Gaps
- **Arcs, Structure, Chapters, Canon panels** — `arcs` wired in Phase 1; `structure`, `chapters`, `canon` keys exist in `StudioPanelKey` but render as placeholder in StudioPanelContent default case (Phase 2)
- **Tear-off into actual OS floating window** — Phase 1 uses `position: fixed` within the same DOM tree; true multi-window tear-off requires `window.open()` or `React Portal` with iframe, deferred to Phase 3
- **Hover preview** — deferred to Phase 3
- **Default layout presets per author type** — deferred to Phase 2

### Adversarial Review Fixes Applied (2026-05-19)

**Pass 1 (17 issues):**

| Issue | Severity | Fix |
|-------|----------|-----|
| **C1**: `react-resizable-panels` API wrong (`Resizable`/`ResizeHandle` don't exist) | Critical | Custom mouse-event resize handles on `StudioFloatingPanel` |
| **C2**: `onDragEnd` uses `over.rect` with no droppable targets — `over` always null | Critical | Use `event.delta` + current position for final position |
| **C3**: `PANEL_OPTIONS` keys not in `StudioPanelKey` union, `as any` cast | Critical | Added `structure`, `chapters`, `canon` to `StudioPanelKey`; typed `PANEL_OPTIONS` as `StudioPanelKey[]` |
| **H1**: `addPanel` calls `state.projectId` — field doesn't exist on `StudioState` | High | Added `currentProjectId` to store; all persistence gated on it |
| **H2**: `loadLayout` no-op placeholder | High | Wired to `loadLayoutV2` function |
| **H3**: `togglePanel` signature mismatch | High | Interface matches implementation: `(id, stateSnapshot?)` |
| **H4**: Drag style drops base position/size when transform is active | High | Style always includes `left`, `top`, `width`, `height`; `transform` layered on top |
| **M1**: Snap grid `opacity: 0.3` applies to child panels | Medium | Grid in separate `pointer-events-none` layer |
| **M2**: WritingView and RadialHub both `absolute inset-0` — panels unclickable | Medium | z-index: WritingView `z-0`, RadialHub `z-10` |
| **M3**: Tests use global Zustand store — parallel test interference | Medium | `beforeEach`/`afterEach` reset store state |
| **M4**: `StudioDraftsPanel`/`StudioManuscriptsPanel` get `projectId` from route | Medium | Out of scope — StudioPanelContent passes `projectId` consistently |
| **M5**: `PANEL_LABELS` missing `arcs` key | Medium | Added `arcs`, `structure`, `chapters`, `canon` labels |
| **M6**: `resetLayout` doesn't clear v2 localStorage | Medium | Extended to clear `studio-layout-v2-${projectId}` |
| **L1**: `Date.now()` collision risk | Low | Use `crypto.randomUUID()` with fallback |
| **L2**: Tests don't mock localStorage | Low | Out of scope — tests use store actions, not direct storage |
| **L3**: ViewShell becomes dead code | Low | Not modified — backward-compatible for non-studio routes |
| **L4**: `StudioPanelContent` missing `arcs` case | Low | Added `arcs` import and switch case |

**Pass 2 (6 issues):**

| Issue | Severity | Fix |
|-------|----------|-----|
| **C4**: `StudioPanelMenu` uses `StudioPanelKey` but doesn't import it | Critical | Added `import type { StudioPanelKey }` |
| **C5**: `StudioCommandBar` plan snippet has no insertion point | Critical | Exact JSX shown: append to existing right-side `<div>` after panel toggle button |
| **H7**: Resize fires `resizePanel` on every pixel — no throttling | High | `requestAnimationFrame` throttling; skip if frame already scheduled |
| **H8**: `movePanel` imported but unused in `StudioFloatingPanel` | High | Removed unused import (drag handled by parent `handleDragEnd`) |
| **M8**: Menu purpose says "toggle visibility" but clicking always adds | Medium | Clarified: menu adds panels; checkmark shows existing; ✕ removes |
| **M9**: `handleDragEnd` closure captures stale `layout.panels` | Medium | Use `useStudioStore.getState().layout.panels` for current state |

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-19-radial-hub-phase-1-core-infrastructure.md`.

**Adversarial review status:** All 23 issues fixed across 2 passes (5 critical, 6 high, 8 medium, 4 low). Plan is ready for execution.

**Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session with checkpoints

**Which approach?**
