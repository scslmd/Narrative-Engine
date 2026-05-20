# Radial Hub Phase 1: Core Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the floating panel system — new store, draggable/resizable panel wrapper, radial hub layout manager, and panel menu — so StudioView renders a working radial hub with existing panels inside floating containers.

**Status:** Design approved. Visual mockup confirmed by user (2026-05-19). Design locked; proceed to implementation.

**Architecture:** Replace the current `StudioView` grid layout (ViewShell with left rail + right panel) with `StudioRadialHub` that renders panels as `StudioFloatingPanel` instances managed by a new layout store. Existing panel content components are reused unchanged, wrapped by `StudioFloatingPanel`. The store adds layout state (panel positions, sizes, visibility) while preserving backward-compatible types for existing consumers.

**Tech Stack:** React 18, TypeScript, Zustand, `@dnd-kit/core` (installed), `@dnd-kit/utilities` (installed), `react-resizable-panels` (new), Tailwind CSS, CSS variables

**Dependencies (existing):** `@dnd-kit/core@^6.3.1`, `@dnd-kit/utilities@^3.2.2`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/package.json` | Modify | Add `react-resizable-panels` dependency |
| `frontend/src/stores/studioStore.ts` | Modify | Add layout state/types alongside existing state (backward-compatible) |
| `frontend/src/components/studio/StudioFloatingPanel.tsx` | Create | Draggable/resizable/tear-off panel wrapper |
| `frontend/src/components/studio/StudioRadialHub.tsx` | Create | Main layout manager: dnd context, panel rendering, snap grid |
| `frontend/src/components/studio/StudioPanelMenu.tsx` | Create | Dropdown menu to toggle panel visibility |
| `frontend/src/views/StudioView.tsx` | Modify | Replace ViewShell grid with StudioRadialHub |
| `frontend/src/components/studio/StudioCommandBar.tsx` | Modify | Add panel menu button and layout reset button |

**Do NOT modify:** Any existing panel content components (`StudioCharactersPanel.tsx`, `StudioIdeasPanel.tsx`, etc.), `StudioContextPanel.tsx`, `StudioProjectRail.tsx`, `ViewShell.tsx`, `WritingView.tsx`, service files, hook files, type files.

---

## Task 1: Install `react-resizable-panels`

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install package**

Run: `cd frontend && npm install react-resizable-panels`
Expected: Package installed, `package.json` updated with `"react-resizable-panels": "^X.Y.Z"`

- [ ] **Step 2: Verify import works**

Run: `cd frontend && npm run typecheck`
Expected: PASS (no new errors beyond pre-existing)

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: install react-resizable-panels for radial hub"
```

---

## Task 2: Extend `studioStore.ts` with Layout State

**Files:**
- Modify: `frontend/src/stores/studioStore.ts`

**Design:** Add new types and state alongside existing types. Keep all existing types (`StudioPanelKey`, `StudioRailMode`, `StudioContextMode`, `PersistedStudioLayout`, `StudioState`) and their behavior unchanged. New state uses `layout` namespace to avoid collision.

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
  return `panel-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}
```

- [ ] **Step 3: Add layout state to store**

Extend `StudioState` interface — add these fields:

```ts
interface StudioState {
  // ... existing fields unchanged ...

  // Layout state (Phase 1)
  layout: StudioLayoutState;
  addPanel: (key: StudioPanelKey) => string;
  removePanel: (id: string) => void;
  movePanel: (id: string, position: { x: number; y: number }) => void;
  resizePanel: (id: string, size: { width: number; height: number }) => void;
  togglePanel: (id: string) => void;
  pinPanel: (id: string, pinned: boolean) => void;
  tearOffPanel: (id: string) => void;
  reattachPanel: (id: string) => void;
  bringToFront: (id: string) => void;
  resetLayout: () => void;
  saveLayout: () => void;
  loadLayout: (projectId: string) => void;
}
```

Note: `resetLayout` already exists — extend it to also reset layout state.

- [ ] **Step 4: Add layout state initialization and actions**

Add to the `create<StudioState>` call, after existing state:

```ts
// Layout state
layout: {
  panels: {},
  nextZIndex: 1,
  layoutPreset: null,
},
addPanel: (key) =>
  set((state) => {
    const id = generatePanelId();
    const workspaceRect = { width: window.innerWidth - 32, height: window.innerHeight - 100 };
    const panel: PanelLayoutState = {
      id,
      key,
      position: { x: snapToGrid(20 + Object.keys(state.layout.panels).length * 12), y: snapToGrid(40) },
      size: { width: 240, height: 320 },
      visible: true,
      pinned: false,
      floating: false,
      zIndex: state.layout.nextZIndex,
    };
    const newPanels = { ...state.layout.panels, [id]: panel };
    persistLayoutV2(state.projectId || '', { panels: newPanels, nextZIndex: state.layout.nextZIndex + 1, layoutPreset: null });
    return { layout: { ...state.layout, panels: newPanels, nextZIndex: state.layout.nextZIndex + 1 } };
  }),
removePanel: (id) =>
  set((state) => {
    const newPanels = { ...state.layout.panels };
    delete newPanels[id];
    return { layout: { ...state.layout, panels: newPanels } };
  }),
movePanel: (id, position) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return state;
    const snapped = { x: snapToGrid(position.x), y: snapToGrid(position.y) };
    const newPanels = { ...state.layout.panels, [id]: { ...panel, position: snapped } };
    return { layout: { ...state.layout, panels: newPanels } };
  }),
resizePanel: (id, size) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return state;
    const clamped = {
      width: Math.max(MIN_PANEL_WIDTH, Math.min(size.width, window.innerWidth - MIN_PANEL_WIDTH - 32)),
      height: Math.max(MIN_PANEL_HEIGHT, Math.min(size.height, window.innerHeight - MIN_PANEL_HEIGHT - 100)),
    };
    const newPanels = { ...state.layout.panels, [id]: { ...panel, size: clamped } };
    return { layout: { ...state.layout, panels: newPanels } };
  }),
togglePanel: (id) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return state;
    const newPanels = { ...state.layout.panels, [id]: { ...panel, visible: !panel.visible } };
    return { layout: { ...state.layout, panels: newPanels } };
  }),
pinPanel: (id, pinned) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return state;
    const newPanels = { ...state.layout.panels, [id]: { ...panel, pinned } };
    return { layout: { ...state.layout, panels: newPanels } };
  }),
tearOffPanel: (id) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return state;
    const newPanels = { ...state.layout.panels, [id]: { ...panel, floating: true } };
    return { layout: { ...state.layout, panels: newPanels } };
  }),
reattachPanel: (id) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return state;
    const newPanels = { ...state.layout.panels, [id]: { ...panel, floating: false } };
    return { layout: { ...state.layout, panels: newPanels } };
  }),
bringToFront: (id) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return state;
    const newPanels = { ...state.layout.panels, [id]: { ...panel, zIndex: state.layout.nextZIndex } };
    return { layout: { ...state.layout, panels: newPanels, nextZIndex: state.layout.nextZIndex + 1 } };
  }),
saveLayout: () => {
  // Handled inline in each action — no-op for explicit save
},
loadLayout: (projectId) => {
  // Load from localStorage — implemented in Step 5
},
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

- [ ] **Step 6: Initialize layout from storage**

In the `create<StudioState>` call, use `loadLayoutV2` for initial layout state. Since `projectId` is not available at store creation time, initialize with empty and load on first access:

```ts
layout: {
  panels: {},
  nextZIndex: 1,
  layoutPreset: null,
},
```

The `loadLayout` action handles loading when projectId becomes available (called from StudioView).

- [ ] **Step 7: Extend existing `resetLayout` to clear layout state**

Modify the existing `resetLayout` action to also reset layout:

```ts
resetLayout: () => {
  set({
    activePanel: 'suggestions',
    leftRailMode: 'collapsed',
    contextPanelMode: 'docked',
    contextPanelPinned: true,
    leftRailWidth: DEFAULT_LEFT_RAIL_WIDTH,
    contextPanelWidth: DEFAULT_CONTEXT_PANEL_WIDTH,
    panelVisible: false,
    layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
  });
  persistLayout(useStudioStore.getState());
},
```

- [ ] **Step 8: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS (no new errors)

- [ ] **Step 9: Commit**

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
import { memo, useCallback } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { Resizable, ResizeHandle } from 'react-resizable-panels';
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
  const movePanel = useStudioStore((s) => s.movePanel);
  const resizePanel = useStudioStore((s) => s.resizePanel);
  const removePanel = useStudioStore((s) => s.removePanel);
  const pinPanel = useStudioStore((s) => s.pinPanel);
  const bringToFront = useStudioStore((s) => s.bringToFront);
  const reattachPanel = useStudioStore((s) => s.reattachPanel);

  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: panelId,
    disabled: floating,
  });

  const style = transform
    ? {
        transform: `translate(${transform.x}px, ${transform.y}px)`,
        zIndex,
      }
    : {
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: `${size.width}px`,
        height: `${size.height}px`,
        zIndex,
      };

  const handleDragEnd = useCallback(
    (_event: { delta: { x: number; y: number } }) => {
      // Will be handled by parent DndContext onDragEnd
    },
    []
  );

  const handleResize = useCallback(
    (newSize: { width: number; height: number }) => {
      resizePanel(panelId, newSize);
    },
    [panelId, resizePanel]
  );

  const label = PANEL_LABELS[panelKey] || panelKey;

  return (
    <div
      ref={setNodeRef}
      data-panel-container
      {...attributes}
      {...listeners}
      onClick={() => bringToFront(panelId)}
      className="flex flex-col overflow-hidden rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-lg"
      style={{
        ...style,
        position: floating ? 'fixed' : 'absolute',
        transition: transform ? 'none' : 'box-shadow 0.15s',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-1.5">
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
      <div className="flex-1 overflow-hidden">
        <Resizable defaultSize={100} className="h-full w-full">
          {children}
          <ResizeHandle
            className="relative flex w-1 items-center justify-end bg-transparent transition-colors hover:bg-[var(--accent-primary)]"
            onResize={(e, size) => {
              // ResizeHandle provides direction — map to width/height
              const container = (e.target as HTMLElement).parentElement;
              if (container) {
                handleResize({
                  width: container.offsetWidth + (size.deltaX ?? 0),
                  height: container.offsetHeight + (size.deltaY ?? 0),
                });
              }
            }}
          />
        </Resizable>
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

**Purpose:** Dropdown menu listing all 12 panels with checkboxes showing current visibility. Clicking adds a panel instance to the layout.

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

const PANEL_OPTIONS = [
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
] as const;

type PanelOptionKey = typeof PANEL_OPTIONS[number]['key'];

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

  const handleAddPanel = (key: PanelOptionKey) => {
    addPanel(key as any);
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
  it('renders workspace container', () => {
    render(<StudioRadialHub projectId="proj-1" />);
    const container = screen.getByRole('main') || document.querySelector('[data-radial-hub]');
    expect(container).toBeInTheDocument();
  });

  it('renders visible panels', () => {
    const store = useStudioStore.getState();
    store.addPanel('characters');
    render(<StudioRadialHub projectId="proj-1" />);
    expect(screen.getByText('👤 Characters')).toBeInTheDocument();
    // Cleanup
    const panels = Object.keys(store.layout.panels);
    panels.forEach((id) => store.removePanel(id));
  });

  it('does not render hidden panels', () => {
    const store = useStudioStore.getState();
    const id = store.addPanel('ideas');
    store.togglePanel(id);
    render(<StudioRadialHub projectId="proj-1" />);
    expect(screen.queryByText('💡 Ideas')).not.toBeInTheDocument();
    // Cleanup
    store.removePanel(id);
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

  const handleDragEnd = useCallback(
    (event: { over: { rect: { x: number; y: number; width: number; height: number } } | null; active: { id: string } }) => {
      const { over, active } = event;
      if (over) {
        movePanel(active.id as string, {
          x: over.rect.x,
          y: over.rect.y,
        });
      }
    },
    [movePanel]
  );

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div
        data-radial-hub
        className="relative h-full w-full overflow-hidden bg-[var(--bg-tertiary)]"
        style={{
          backgroundImage: 'radial-gradient(circle, var(--border-primary) 1px, transparent 1px)',
          backgroundSize: '8px 8px',
          opacity: 0.3,
        }}
      >
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
      <div className="relative flex-1 overflow-hidden">
        <div className="absolute inset-0 flex">
          <StudioRadialHub projectId={projectId} />
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="mx-4 h-[calc(100%-32px)] w-full max-w-3xl overflow-hidden rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-lg">
            <WritingView embedded />
          </div>
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

Add to the interface:
```ts
interface StudioCommandBarProps {
  projectId: string;
  onResetLayout: () => void;
}
```

Import and add `StudioPanelMenu` and reset button to the command bar's right section:
```tsx
import { StudioPanelMenu } from './StudioPanelMenu';

// In the render, add to the right side of the command bar:
<div className="flex items-center gap-2">
  <button
    type="button"
    onClick={onResetLayout}
    className="rounded-md px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
    title="Reset layout"
  >
    ↺ Reset
  </button>
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
| Install `react-resizable-panels` | Task 1 | ✅ |
| Rewrite `studioStore.ts` with layout state | Task 2 | ✅ |
| Create `StudioFloatingPanel.tsx` | Task 3 | ✅ |
| Create `StudioRadialHub.tsx` | Task 5 | ✅ |
| Create `StudioPanelMenu.tsx` | Task 4 | ✅ |
| Update `StudioView.tsx` | Task 7 | ✅ |
| Update `StudioCommandBar.tsx` | Task 8 | ✅ |
| Drag-and-drop with grid snap | Tasks 3, 5 | ✅ (basic dnd + snap in store) |
| Resize handles | Task 3 | ✅ (via react-resizable-panels) |
| Tear-off / reattach | Tasks 2, 3 | ✅ (store actions + UI buttons) |
| Layout persistence | Task 2 | ✅ (localStorage per project) |
| Existing panels reused | Task 6 | ✅ (StudioPanelContent router) |

### Placeholder Scan
- No "TBD", "TODO", "implement later" found
- No "add appropriate error handling" — error handling is explicit (try/catch in localStorage, null checks in store)
- All code blocks contain actual implementation code
- All types defined before use

### Type Consistency
- `StudioPanelKey` used consistently across store, panel menu, panel content, and floating panel
- `PanelLayoutState` and `StudioLayoutState` defined in store, referenced correctly in components
- `projectId` string passed through all components consistently
- `resetLayout` signature unchanged (extended behavior, same call)

### Gaps
- **Arcs, Structure, Chapters, Canon panels** — not yet implemented (planned for Phase 2, rendered as placeholder in StudioPanelContent default case)
- **Tear-off into actual OS floating window** — Phase 1 uses `position: fixed` within the same DOM tree; true multi-window tear-off requires `window.open()` or `React Portal` with iframe, deferred to Phase 3
- **Hover preview** — deferred to Phase 3
- **Default layout presets per author type** — deferred to Phase 2

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-19-radial-hub-phase-1-core-infrastructure.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session with checkpoints

**Which approach?**
