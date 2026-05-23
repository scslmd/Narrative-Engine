# Layout Management System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable users to create, save, rename, delete, and load named workspace layouts with 9 built-in presets and a locked factory default.

**Architecture:** 2-layer split — pure config module (`layoutPresets.ts`) + UI component (`StudioLayoutManager.tsx`). No hook layer. Store actions added to `studioStore.ts` for `factoryReset()` and `applyUserLayout()`.

**Tech Stack:** TypeScript, React, Zustand, Vitest, Testing Library

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `stores/layoutPresets.ts` | CREATE | Types, factory default, built-in presets, user CRUD, localStorage |
| `stores/studioStore.ts` | MODIFY | Import presets, add `factoryReset()` + `applyUserLayout()`, expand `AuthorPreset` |
| `components/studio/StudioLayoutManager.tsx` | CREATE | Dropdown UI, save/load/rename/delete/reset/export/import |
| `components/studio/StudioCommandBar.tsx` | MODIFY | Swap `StudioLayoutPreset` for `StudioLayoutManager` |
| `components/studio/StudioLayoutPreset.tsx` | DELETE | Replaced by `StudioLayoutManager` |
| `stores/layoutPresets.test.ts` | CREATE | 13 unit tests for pure functions |
| `components/studio/StudioLayoutManager.test.tsx` | CREATE | 10 component tests |

---

### Task 1: Create `layoutPresets.ts` — Types and Factory Default

**Files:**
- Create: `frontend/src/stores/layoutPresets.ts`

- [ ] **Step 1: Define types and factory default**

```ts
// frontend/src/stores/layoutPresets.ts

import type {
  StudioPanelKey,
  PanelLayoutState,
  PersistedStudioLayout,
  AuthorPreset,
} from './studioStore';

// Expand AuthorPreset type (will be re-exported from studioStore for compat)
export type AuthorPresetKey =
  | 'idea-first'
  | 'character-first'
  | 'outline-first'
  | 'world-first'
  | 'beat-sheet'
  | 'theme-driven'
  | 'showrunner'
  | 'revision-lab'
  | 'world-builder-plus';

export interface UserLayout {
  id: string;
  name: string;
  panels: Record<string, PanelLayoutState>;
  v1State: PersistedStudioLayout;
  createdAt: number;
  updatedAt: number;
}

export interface FactoryLayout {
  v1State: PersistedStudioLayout;
  panels: Record<string, PanelLayoutState>;
}

const USER_LAYOUTS_KEY = 'studio-user-layouts';
const MAX_LAYOUT_NAME = 50;

export function getFactoryDefault(): FactoryLayout {
  return {
    v1State: {
      leftRailMode: 'expanded',
      contextPanelMode: 'closed',
      contextPanelPinned: true,
      leftRailWidth: 224,
      contextPanelWidth: 416,
    },
    panels: {
      'factory-manuscripts': {
        id: 'factory-manuscripts',
        key: 'manuscripts',
        position: { x: 80, y: 0 },
        size: { width: 320, height: 400 },
        visible: true,
        pinned: false,
        floating: false,
        zIndex: 100,
        collapsedSections: {},
        scrollY: 0,
      },
      'factory-suggestions': {
        id: 'factory-suggestions',
        key: 'suggestions',
        position: { x: 0, y: 420 },
        size: { width: 320, height: 400 },
        visible: true,
        pinned: false,
        floating: false,
        zIndex: 101,
        collapsedSections: {},
        scrollY: 0,
      },
      'factory-characters': {
        id: 'factory-characters',
        key: 'characters',
        position: { x: 340, y: 420 },
        size: { width: 360, height: 420 },
        visible: true,
        pinned: false,
        floating: false,
        zIndex: 102,
        collapsedSections: {},
        scrollY: 0,
      },
    },
  };
}
```

- [ ] **Step 2: Verify file compiles**

Run: `cd frontend && cmd /c "npm run typecheck"`
Expected: No new errors related to `layoutPresets.ts`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/layoutPresets.ts
git commit -m "feat(layout): add layoutPresets module with types and factory default"
```

---

### Task 2: Add Built-In Presets Map to `layoutPresets.ts`

**Files:**
- Modify: `frontend/src/stores/layoutPresets.ts`

- [ ] **Step 1: Add presets map and menu labels**

```ts
interface PanelPresetDef {
  key: StudioPanelKey;
}

export const BUILTIN_PRESETS: Record<AuthorPresetKey, PanelPresetDef[]> = {
  'idea-first': [
    { key: 'ideas' },
    { key: 'manuscripts' },
    { key: 'characters' },
  ],
  'character-first': [
    { key: 'characters' },
    { key: 'relationships' },
    { key: 'arcs' },
    { key: 'ideas' },
  ],
  'outline-first': [
    { key: 'structure' },
    { key: 'chapters' },
    { key: 'generation' },
  ],
  'world-first': [
    { key: 'worldBible' },
    { key: 'characters' },
    { key: 'arcs' },
    { key: 'structure' },
  ],
  'beat-sheet': [
    { key: 'structure' },
    { key: 'chapters' },
    { key: 'notes' },
    { key: 'generation' },
  ],
  'theme-driven': [
    { key: 'characters' },
    { key: 'arcs' },
    { key: 'worldBible' },
    { key: 'notes' },
    { key: 'review' },
  ],
  'showrunner': [
    { key: 'characters' },
    { key: 'relationships' },
    { key: 'arcs' },
    { key: 'chapters' },
    { key: 'generation' },
  ],
  'revision-lab': [
    { key: 'manuscripts' },
    { key: 'review' },
    { key: 'suggestions' },
    { key: 'notes' },
    { key: 'drafts' },
  ],
  'world-builder-plus': [
    { key: 'worldBible' },
    { key: 'characters' },
    { key: 'relationships' },
    { key: 'canon' },
    { key: 'notes' },
  ],
};

export const PRESET_LABELS: Record<AuthorPresetKey, string> = {
  'idea-first': 'Idea-First (Pantser)',
  'character-first': 'Character-First',
  'outline-first': 'Outline-First (Plotter)',
  'world-first': 'World-First',
  'beat-sheet': 'Beat-Sheet',
  'theme-driven': 'Theme-Driven',
  'showrunner': 'Showrunner',
  'revision-lab': 'Revision Lab',
  'world-builder-plus': 'World-Builder+',
};

export function getBuiltInPresets(): Record<AuthorPresetKey, PanelPresetDef[]> {
  return BUILTIN_PRESETS;
}

export function getPresetLabel(key: AuthorPresetKey): string {
  return PRESET_LABELS[key];
}
```

- [ ] **Step 2: Verify file compiles**

Run: `cd frontend && cmd /c "npm run typecheck"`
Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/layoutPresets.ts
git commit -m "feat(layout): add 9 built-in presets map and labels to layoutPresets"
```

---

### Task 3: Add User Layout CRUD to `layoutPresets.ts`

**Files:**
- Modify: `frontend/src/stores/layoutPresets.ts`

- [ ] **Step 1: Implement CRUD functions**

```ts
interface SaveResult {
  success: boolean;
  error?: 'duplicate' | 'empty' | 'too_long' | 'quota' | null;
}

interface RenameResult {
  success: boolean;
  error?: 'duplicate' | 'empty' | 'too_long' | 'not_found' | 'quota' | null;
}

function readUserLayouts(): UserLayout[] {
  try {
    const raw = localStorage.getItem(USER_LAYOUTS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed;
  } catch {
    console.warn('[layoutPresets] corrupt localStorage data');
    return [];
  }
}

function writeUserLayouts(layouts: UserLayout[]): void {
  try {
    localStorage.setItem(USER_LAYOUTS_KEY, JSON.stringify(layouts));
  } catch (e: unknown) {
    if (e instanceof DOMException && e.name === 'QuotaExceededError') {
      console.warn('[layoutPresets] localStorage quota exceeded');
    }
  }
}

export function listUserLayouts(): UserLayout[] {
  return readUserLayouts().sort((a, b) => a.name.localeCompare(b.name));
}

export function loadUserLayout(id: string): UserLayout | null {
  return readUserLayouts().find((l) => l.id === id) ?? null;
}

export function saveUserLayout(
  name: string,
  data: { panels: Record<string, PanelLayoutState>; v1State: PersistedStudioLayout },
): SaveResult {
  const trimmed = name.trim();
  if (!trimmed) return { success: false, error: 'empty' };
  if (trimmed.length > MAX_LAYOUT_NAME) return { success: false, error: 'too_long' };

  const layouts = readUserLayouts();
  const existing = layouts.findIndex((l) => l.name === trimmed);
  const now = Date.now();

  const layout: UserLayout = {
    id: existing >= 0 ? layouts[existing].id : `ulayout-${crypto.randomUUID?.() ?? now}`,
    name: trimmed,
    panels: data.panels,
    v1State: data.v1State,
    createdAt: existing >= 0 ? layouts[existing].createdAt : now,
    updatedAt: now,
  };

  if (existing >= 0) {
    layouts[existing] = layout;
  } else {
    layouts.push(layout);
  }

  try {
    writeUserLayouts(layouts);
    return { success: true };
  } catch {
    return { success: false, error: 'quota' };
  }
}

export function renameUserLayout(id: string, newName: string): RenameResult {
  const trimmed = newName.trim();
  if (!trimmed) return { success: false, error: 'empty' };
  if (trimmed.length > MAX_LAYOUT_NAME) return { success: false, error: 'too_long' };

  const layouts = readUserLayouts();
  const idx = layouts.findIndex((l) => l.id === id);
  if (idx < 0) return { success: false, error: 'not_found' };

  const duplicate = layouts.find((l, i) => i !== idx && l.name === trimmed);
  if (duplicate) return { success: false, error: 'duplicate' };

  layouts[idx].name = trimmed;
  layouts[idx].updatedAt = Date.now();

  try {
    writeUserLayouts(layouts);
    return { success: true };
  } catch {
    return { success: false, error: 'quota' };
  }
}

export function deleteUserLayout(id: string): boolean {
  const layouts = readUserLayouts().filter((l) => l.id !== id);
  if (layouts.length === readUserLayouts().length) return false;
  writeUserLayouts(layouts);
  return true;
}
```

- [ ] **Step 2: Verify file compiles**

Run: `cd frontend && cmd /c "npm run typecheck"`
Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/layoutPresets.ts
git commit -m "feat(layout): add user layout CRUD with localStorage persistence"
```

---

### Task 4: Write Unit Tests for `layoutPresets.ts`

**Files:**
- Create: `frontend/src/stores/layoutPresets.test.ts`

- [ ] **Step 1: Write tests**

```ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  getFactoryDefault,
  getBuiltInPresets,
  listUserLayouts,
  loadUserLayout,
  saveUserLayout,
  renameUserLayout,
  deleteUserLayout,
  PRESET_LABELS,
} from './layoutPresets';
import type { PanelLayoutState, PersistedStudioLayout } from './studioStore';

const USER_LAYOUTS_KEY = 'studio-user-layouts';

const mockPanels: Record<string, PanelLayoutState> = {};
const mockV1: PersistedStudioLayout = {
  leftRailMode: 'expanded',
  contextPanelMode: 'closed',
  contextPanelPinned: true,
  leftRailWidth: 224,
  contextPanelWidth: 416,
};

beforeEach(() => {
  localStorage.removeItem(USER_LAYOUTS_KEY);
});

describe('getFactoryDefault', () => {
  it('returns correct V1 state', () => {
    const def = getFactoryDefault();
    expect(def.v1State.leftRailMode).toBe('expanded');
    expect(def.v1State.contextPanelMode).toBe('closed');
    expect(def.v1State.leftRailWidth).toBe(224);
  });

  it('returns 3 panels with correct IDs', () => {
    const def = getFactoryDefault();
    const ids = Object.keys(def.panels);
    expect(ids).toHaveLength(3);
    expect(ids).toContain('factory-manuscripts');
    expect(ids).toContain('factory-suggestions');
    expect(ids).toContain('factory-characters');
  });
});

describe('getBuiltInPresets', () => {
  it('returns 9 presets', () => {
    const presets = getBuiltInPresets();
    expect(Object.keys(presets)).toHaveLength(9);
  });

  it('includes new presets', () => {
    const presets = getBuiltInPresets();
    expect(presets['beat-sheet']).toBeDefined();
    expect(presets['showrunner']).toBeDefined();
  });
});

describe('PRESET_LABELS', () => {
  it('has label for each preset', () => {
    const presets = getBuiltInPresets();
    for (const key of Object.keys(presets)) {
      expect(PRESET_LABELS[key as keyof typeof PRESET_LABELS]).toBeDefined();
    }
  });
});

describe('user layout CRUD', () => {
  it('list returns empty initially', () => {
    expect(listUserLayouts()).toHaveLength(0);
  });

  it('save creates layout', () => {
    const result = saveUserLayout('Test Layout', { panels: mockPanels, v1State: mockV1 });
    expect(result.success).toBe(true);
    const layouts = listUserLayouts();
    expect(layouts).toHaveLength(1);
    expect(layouts[0].name).toBe('Test Layout');
  });

  it('save rejects empty name', () => {
    const result = saveUserLayout('', { panels: mockPanels, v1State: mockV1 });
    expect(result.success).toBe(false);
    expect(result.error).toBe('empty');
  });

  it('save rejects name too long', () => {
    const result = saveUserLayout('a'.repeat(51), { panels: mockPanels, v1State: mockV1 });
    expect(result.success).toBe(false);
    expect(result.error).toBe('too_long');
  });

  it('load returns layout by id', () => {
    saveUserLayout('Test', { panels: mockPanels, v1State: mockV1 });
    const id = listUserLayouts()[0].id;
    const loaded = loadUserLayout(id);
    expect(loaded).not.toBeNull();
    expect(loaded!.name).toBe('Test');
  });

  it('load returns null for unknown id', () => {
    expect(loadUserLayout('nonexistent')).toBeNull();
  });

  it('rename updates name', () => {
    saveUserLayout('Old Name', { panels: mockPanels, v1State: mockV1 });
    const id = listUserLayouts()[0].id;
    const result = renameUserLayout(id, 'New Name');
    expect(result.success).toBe(true);
    expect(loadUserLayout(id)?.name).toBe('New Name');
  });

  it('rename rejects duplicate name', () => {
    saveUserLayout('A', { panels: mockPanels, v1State: mockV1 });
    saveUserLayout('B', { panels: mockPanels, v1State: mockV1 });
    const idB = listUserLayouts().find((l) => l.name === 'B')!.id;
    const result = renameUserLayout(idB, 'A');
    expect(result.success).toBe(false);
    expect(result.error).toBe('duplicate');
  });

  it('delete removes layout', () => {
    saveUserLayout('ToDelete', { panels: mockPanels, v1State: mockV1 });
    const id = listUserLayouts()[0].id;
    expect(deleteUserLayout(id)).toBe(true);
    expect(listUserLayouts()).toHaveLength(0);
  });

  it('list returns sorted layouts', () => {
    saveUserLayout('Charlie', { panels: mockPanels, v1State: mockV1 });
    saveUserLayout('Alpha', { panels: mockPanels, v1State: mockV1 });
    saveUserLayout('Beta', { panels: mockPanels, v1State: mockV1 });
    const names = listUserLayouts().map((l) => l.name);
    expect(names).toEqual(['Alpha', 'Beta', 'Charlie']);
  });
});
```

- [ ] **Step 2: Run tests**

Run: `cd frontend && cmd /c "npx vitest run src/stores/layoutPresets.test.ts --reporter=verbose"`
Expected: 13 passing tests

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/layoutPresets.test.ts
git commit -m "test(layout): add 13 unit tests for layoutPresets CRUD"
```

---

### Task 5: Update `studioStore.ts` — Import Presets, Add Actions

**Files:**
- Modify: `frontend/src/stores/studioStore.ts`

- [ ] **Step 1: Move `AuthorPreset` type and `LAYOUT_PRESETS` to imports**

Replace the inline `AuthorPreset` type and `LAYOUT_PRESETS` constant:

```ts
// At top of file, after existing imports:
import {
  getBuiltInPresets,
  getFactoryDefault,
  loadUserLayout,
  type AuthorPresetKey,
  type PanelPresetDef,
} from './layoutPresets';

// Replace AuthorPreset type with re-export:
export type AuthorPreset = AuthorPresetKey;

// Replace LAYOUT_PRESETS constant:
const LAYOUT_PRESETS = getBuiltInPresets();
```

- [ ] **Step 2: Add `factoryReset` and `applyUserLayout` actions to the store interface**

Add to `StudioState` interface:
```ts
factoryReset: () => void;
applyUserLayout: (id: string) => boolean;
```

- [ ] **Step 3: Implement `factoryReset` action**

Add to Zustand create (after `importLayout`):
```ts
factoryReset: () => {
  const def = getFactoryDefault();
  useStudioStore.setState({
    activePanel: 'suggestions',
    leftRailMode: def.v1State.leftRailMode as any,
    contextPanelMode: def.v1State.contextPanelMode as any,
    contextPanelPinned: def.v1State.contextPanelPinned,
    leftRailWidth: def.v1State.leftRailWidth,
    contextPanelWidth: def.v1State.contextPanelWidth,
    panelVisible: false,
    layout: {
      panels: def.panels,
      nextZIndex: 103,
      layoutPreset: null,
    },
  });
  persistLayout(useStudioStore.getState());
  if (useStudioStore.getState().currentProjectId) {
    persistLayoutV2(useStudioStore.getState().currentProjectId!, {
      panels: def.panels,
      nextZIndex: 103,
      layoutPreset: null,
    });
  }
},
applyUserLayout: (id) => {
  const layout = loadUserLayout(id);
  if (!layout) return false;

  useStudioStore.setState({
    leftRailMode: layout.v1State.leftRailMode as any,
    contextPanelMode: layout.v1State.contextPanelMode as any,
    contextPanelPinned: layout.v1State.contextPanelPinned,
    leftRailWidth: layout.v1State.leftRailWidth,
    contextPanelWidth: layout.v1State.contextPanelWidth,
    activePanel: Object.values(layout.panels).find((p) => p.visible)?.key ?? 'suggestions',
    layout: {
      panels: layout.panels,
      nextZIndex: Object.values(layout.panels).reduce((max, p) => Math.max(max, p.zIndex), 100) + 1,
      layoutPreset: layout.name,
    },
  });

  if (useStudioStore.getState().currentProjectId) {
    persistLayoutV2(useStudioStore.getState().currentProjectId!, {
      panels: layout.panels,
      nextZIndex: Object.values(layout.panels).reduce((max, p) => Math.max(max, p.zIndex), 100) + 1,
      layoutPreset: layout.name,
    });
  }

  return true;
},
```

- [ ] **Step 4: Verify compilation**

Run: `cd frontend && cmd /c "npm run typecheck"`
Expected: No new errors (existing LSP errors from star imports are pre-existing)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/stores/studioStore.ts
git commit -m "feat(layout): import presets from layoutPresets, add factoryReset and applyUserLayout"
```

---

### Task 6: Create `StudioLayoutManager.tsx` — Component

**Files:**
- Create: `frontend/src/components/studio/StudioLayoutManager.tsx`

- [ ] **Step 1: Create the component**

```tsx
import { memo, useRef, useEffect, useState } from 'react';
import { Pencil, Trash2, Plus } from 'lucide-react';
import { useStudioStore, type AuthorPreset } from '../../stores/studioStore';
import {
  getBuiltInPresets,
  PRESET_LABELS,
  listUserLayouts,
  saveUserLayout,
  renameUserLayout,
  deleteUserLayout,
  type AuthorPresetKey,
} from '../../stores/layoutPresets';

function StudioLayoutManagerImpl() {
  const applyPreset = useStudioStore((s) => s.applyPreset);
  const applyUserLayout = useStudioStore((s) => s.applyUserLayout);
  const factoryReset = useStudioStore((s) => s.factoryReset);
  const doExportLayout = useStudioStore((s) => s.exportLayout);
  const doImportLayout = useStudioStore((s) => s.importLayout);
  const state = useStudioStore((s) => ({
    panels: s.layout.panels,
    v1State: {
      leftRailMode: s.leftRailMode,
      contextPanelMode: s.contextPanelMode,
      contextPanelPinned: s.contextPanelPinned,
      leftRailWidth: s.leftRailWidth,
      contextPanelWidth: s.contextPanelWidth,
    },
  }));

  const [open, setOpen] = useState(false);
  const [importText, setImportText] = useState('');
  const [showImport, setShowImport] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [showSaveInput, setShowSaveInput] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [renameError, setRenameError] = useState<string | null>(null);
  const [userLayouts, setUserLayouts] = useState(() => listUserLayouts());
  const [toast, setToast] = useState<{ msg: string; action?: string; onConfirm?: () => void } | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [open]);

  const refreshLayouts = () => setUserLayouts(listUserLayouts());

  const handleExport = () => {
    const json = doExportLayout();
    navigator.clipboard.writeText(json).catch(() => {
      setImportText(json);
      setShowImport(true);
    });
    setOpen(false);
  };

  const handleImport = () => {
    setImportError(null);
    if (doImportLayout(importText)) {
      setShowImport(false);
      setImportText('');
      setOpen(false);
    } else {
      setImportError('Invalid layout JSON.');
    }
  };

  const handleSave = () => {
    setSaveError(null);
    const result = saveUserLayout(saveName, { panels: state.panels, v1State: state.v1State });
    if (result.success) {
      setSaveName('');
      setShowSaveInput(false);
      refreshLayouts();
    } else {
      setSaveError(result.error === 'empty' ? 'Name required' : result.error === 'too_long' ? 'Max 50 chars' : 'Storage full');
    }
  };

  const handleRename = (id: string) => {
    setRenameError(null);
    const result = renameUserLayout(id, editName);
    if (result.success) {
      setEditingId(null);
      setEditName('');
      refreshLayouts();
    } else {
      setRenameError(result.error === 'duplicate' ? 'Name exists' : result.error === 'empty' ? 'Name required' : 'Error');
    }
  };

  const handleDelete = (id: string, name: string) => {
    setToast({
      msg: `Delete "${name}"?`,
      action: 'Delete',
      onConfirm: () => {
        deleteUserLayout(id);
        refreshLayouts();
        setToast(null);
      },
    });
  };

  const presets = getBuiltInPresets();

  return (
    <>
      <div ref={menuRef} className="relative">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="rounded-md px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
        >
          Layout &#9662;
        </button>

        {open && (
          <div className="absolute right-0 z-50 mt-1 min-w-[240px] max-h-[80vh] overflow-y-auto rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-1 shadow-xl">
            <div className="mb-1 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
              Presets
            </div>

            {Object.entries(presets).map(([key]) => (
              <button
                key={key}
                type="button"
                onClick={() => { applyPreset(key as AuthorPreset); setOpen(false); }}
                className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
              >
                <span className="text-[var(--text-tertiary)] text-[10px]">&#9658;</span>
                {PRESET_LABELS[key as AuthorPresetKey]}
              </button>
            ))}

            <div className="my-1 border-t border-[var(--border-primary)]" />

            <div className="mb-1 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
              My Layouts
            </div>

            {userLayouts.length === 0 && (
              <div className="px-3 py-2 text-[11px] text-[var(--text-tertiary)]">No saved layouts</div>
            )}

            {userLayouts.map((layout) => (
              <div key={layout.id} className="flex items-center">
                {editingId === layout.id ? (
                  <div className="flex w-full items-center gap-1">
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleRename(layout.id);
                        if (e.key === 'Escape') { setEditingId(null); setRenameError(null); }
                      }}
                      maxLength={50}
                      className="flex-1 rounded border border-[var(--accent-primary)] bg-[var(--bg-secondary)] px-2 py-0.5 text-[11px] text-[var(--text-primary)] outline-none"
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => handleRename(layout.id)}
                      className="text-[10px] font-medium text-[var(--accent-primary)] hover:opacity-80"
                    >
                      Save
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => { applyUserLayout(layout.id); setOpen(false); }}
                      className="flex flex-1 items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
                    >
                      <span className="text-[var(--text-tertiary)] text-[10px]">&#9658;</span>
                      <span className="truncate">{layout.name}</span>
                    </button>
                    <button
                      type="button"
                      title="Rename"
                      onClick={() => { setEditingId(layout.id); setEditName(layout.name); setRenameError(null); }}
                      className="p-1 text-[var(--text-tertiary)] transition-colors hover:text-[var(--text-primary)]"
                    >
                      <Pencil className="h-3 w-3" />
                    </button>
                    <button
                      type="button"
                      title="Delete"
                      onClick={() => handleDelete(layout.id, layout.name)}
                      className="p-1 text-[var(--text-tertiary)] transition-colors hover:text-red-400"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </>
                )}
              </div>
            ))}

            {renameError && <div className="mt-1 px-2 text-[10px] text-red-400">{renameError}</div>}

            <div className="my-1 border-t border-[var(--border-primary)]" />

            {showSaveInput ? (
              <div className="flex items-center gap-1 px-1">
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSave();
                    if (e.key === 'Escape') { setShowSaveInput(false); setSaveError(null); }
                  }}
                  placeholder="Layout name..."
                  maxLength={50}
                  className="flex-1 rounded border border-[var(--accent-primary)] bg-[var(--bg-secondary)] px-2 py-1 text-[11px] text-[var(--text-primary)] outline-none"
                  autoFocus
                />
                <button
                  type="button"
                  onClick={handleSave}
                  className="rounded bg-[var(--accent-primary)] px-2 py-0.5 text-[10px] font-medium text-white hover:opacity-90"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => { setShowSaveInput(false); setSaveError(null); }}
                  className="rounded px-2 py-0.5 text-[10px] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => { setShowSaveInput(true); setSaveName(''); setSaveError(null); }}
                className="flex w-full items-center gap-1.5 rounded-md px-3 py-1.5 text-xs text-[var(--text-tertiary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
              >
                <Plus className="h-3 w-3 text-green-500" />
                Save Current Layout
              </button>
            )}
            {saveError && <div className="mt-1 px-2 text-[10px] text-red-400">{saveError}</div>}

            <div className="my-1 border-t border-[var(--border-primary)]" />

            <button
              type="button"
              onClick={handleExport}
              className="flex w-full items-center rounded-md px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
            >
              Export Layout (clipboard)
            </button>
            <button
              type="button"
              onClick={() => setShowImport(!showImport)}
              className="flex w-full items-center rounded-md px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
            >
              Import Layout (paste JSON)
            </button>
            {showImport && (
              <div className="mt-1 p-2">
                <textarea
                  value={importText}
                  onChange={(e) => setImportText(e.target.value)}
                  placeholder="Paste layout JSON..."
                  className="h-20 w-full resize-none rounded-md border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-2 text-[10px] text-[var(--text-primary)]"
                />
                {importError && <div className="mt-1 text-[10px] text-red-400">{importError}</div>}
                <button
                  type="button"
                  onClick={handleImport}
                  className="mt-1 w-full rounded-md bg-[var(--accent-primary)] px-2 py-1 text-[10px] font-medium text-white hover:opacity-90"
                >
                  Apply Imported Layout
                </button>
              </div>
            )}

            <div className="my-1 border-t border-[var(--border-primary)]" />

            <button
              type="button"
              onClick={() => {
                setToast({
                  msg: 'Reset to Factory Default?',
                  action: 'Reset',
                  onConfirm: () => {
                    factoryReset();
                    setOpen(false);
                    setToast(null);
                  },
                });
              }}
              className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--text-tertiary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-red-400"
            >
              &#8634; Reset to Factory Default
            </button>
          </div>
        )}
      </div>

      {toast && (
        <div className="fixed bottom-6 right-6 z-[100] flex items-center gap-3 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-4 py-2.5 text-xs text-[var(--text-primary)] shadow-xl">
          <span dangerouslySetInnerHTML={{ __html: toast.msg }} />
          {toast.action && (
            <button
              onClick={() => {
                toast.onConfirm?.();
              }}
              className="font-semibold text-[var(--accent-primary)] hover:opacity-80"
            >
              {toast.action}
            </button>
          )}
          <button onClick={() => setToast(null)} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]">
            &#10005;
          </button>
        </div>
      )}
    </>
  );
}

export const StudioLayoutManager = memo(StudioLayoutManagerImpl);
```

- [ ] **Step 2: Verify compilation**

Run: `cd frontend && cmd /c "npm run typecheck"`
Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/studio/StudioLayoutManager.tsx
git commit -m "feat(layout): create StudioLayoutManager component with full dropdown UI"
```

---

### Task 7: Wire `StudioLayoutManager` into `StudioCommandBar`, Delete Old Component

**Files:**
- Modify: `frontend/src/components/studio/StudioCommandBar.tsx`
- Delete: `frontend/src/components/studio/StudioLayoutPreset.tsx`

- [ ] **Step 1: Update `StudioCommandBar.tsx`**

Replace line 4 import and line 91:

```ts
// Line 4: change import
// FROM: import { StudioLayoutPreset } from './StudioLayoutPreset';
// TO:   import { StudioLayoutManager } from './StudioLayoutManager';

// Line 91: change component
// FROM: {projectId && <StudioLayoutPreset />}
// TO:   {projectId && <StudioLayoutManager />}
```

- [ ] **Step 2: Delete `StudioLayoutPreset.tsx`**

```bash
git rm frontend/src/components/studio/StudioLayoutPreset.tsx
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && cmd /c "npm run build"`
Expected: Successful build, no errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/studio/StudioCommandBar.tsx
git rm frontend/src/components/studio/StudioLayoutPreset.tsx
git commit -m "feat(layout): wire StudioLayoutManager, delete StudioLayoutPreset"
```

---

### Task 8: Write Component Tests for `StudioLayoutManager.tsx`

**Files:**
- Create: `frontend/src/components/studio/StudioLayoutManager.test.tsx`

- [ ] **Step 1: Write tests**

```tsx
import { describe, it, expect, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import { render, screen } from '../../__tests__/test-utils';
import { StudioLayoutManager } from './StudioLayoutManager';
import { useStudioStore } from '../../stores/studioStore';
import { listUserLayouts, saveUserLayout, deleteUserLayout } from '../../stores/layoutPresets';

beforeEach(() => {
  act(() => {
    useStudioStore.getState().resetLayout();
  });
  // Clear user layouts
  const layouts = listUserLayouts();
  layouts.forEach((l) => deleteUserLayout(l.id));
});

describe('StudioLayoutManager', () => {
  it('renders Layout button', () => {
    render(<StudioLayoutManager />);
    expect(screen.getByText(/Layout/)).toBeInTheDocument();
  });

  it('shows 9 preset buttons when opened', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await import('@testing-library/user-event').then(({ default: u }) => {
      const user = u.setup();
      return user.click(btn);
    });
    // Presets should be visible
    expect(screen.getByText('Idea-First (Pantser)')).toBeInTheDocument();
    expect(screen.getByText('Beat-Sheet')).toBeInTheDocument();
    expect(screen.getByText('World-Builder+')).toBeInTheDocument();
  });

  it('shows My Layouts section', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await import('@testing-library/user-event').then(({ default: u }) => {
      const user = u.setup();
      return user.click(btn);
    });
    expect(screen.getByText('My Layouts')).toBeInTheDocument();
  });

  it('shows Save Current Layout button', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await import('@testing-library/user-event').then(({ default: u }) => {
      const user = u.setup();
      return user.click(btn);
    });
    expect(screen.getByText('Save Current Layout')).toBeInTheDocument();
  });

  it('shows Reset to Factory Default button', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await import('@testing-library/user-event').then(({ default: u }) => {
      const user = u.setup();
      return user.click(btn);
    });
    expect(screen.getByText('Reset to Factory Default')).toBeInTheDocument();
  });

  it('shows Export and Import buttons', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await import('@testing-library/user-event').then(({ default: u }) => {
      const user = u.setup();
      return user.click(btn);
    });
    expect(screen.getByText('Export Layout (clipboard)')).toBeInTheDocument();
    expect(screen.getByText('Import Layout (paste JSON)')).toBeInTheDocument();
  });

  it('shows "No saved layouts" when empty', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await import('@testing-library/user-event').then(({ default: u }) => {
      const user = u.setup();
      return user.click(btn);
    });
    expect(screen.getByText('No saved layouts')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests**

Run: `cd frontend && cmd /c "npx vitest run src/components/studio/StudioLayoutManager.test.tsx --reporter=verbose"`
Expected: 7 passing tests

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/studio/StudioLayoutManager.test.tsx
git commit -m "test(layout): add 7 component tests for StudioLayoutManager"
```

---

### Task 9: Full Validation and Cleanup

**Files:** All changed files

- [ ] **Step 1: Run lint**

Run: `cd frontend && cmd /c "npm run lint"`
Expected: No new errors

- [ ] **Step 2: Run typecheck**

Run: `cd frontend && cmd /c "npm run typecheck"`
Expected: No new errors

- [ ] **Step 3: Run build**

Run: `cd frontend && cmd /c "npm run build"`
Expected: Successful build

- [ ] **Step 4: Run full test suite**

Run: `cd frontend && cmd /c "npm run test"`
Expected: All tests pass (previous 675 + new tests)

- [ ] **Step 5: Squash and commit**

```bash
git add -A
git commit -m "feat(layout): complete layout management system

- New stores/layoutPresets.ts: factory default, 9 built-in presets, user CRUD
- New StudioLayoutManager.tsx: dropdown with presets, save/load/rename/delete/reset
- Updated studioStore.ts: factoryReset(), applyUserLayout(), expanded AuthorPreset
- Deleted StudioLayoutPreset.tsx: replaced by StudioLayoutManager
- Added 20 tests: 13 unit + 7 component
- Export/import retained from old component"
```

---

## Self-Review

### Spec Coverage

| Spec Requirement | Task | Status |
|-----------------|------|--------|
| Factory default (locked) | Task 1 | Covered |
| 9 built-in presets | Task 2 | Covered |
| User layout CRUD | Task 3 | Covered |
| Unit tests for CRUD | Task 4 | Covered |
| Store actions (factoryReset, applyUserLayout) | Task 5 | Covered |
| UI component with dropdown | Task 6 | Covered |
| Wire into command bar | Task 7 | Covered |
| Component tests | Task 8 | Covered |
| Export/import retained | Task 6 | Covered |
| Full validation | Task 9 | Covered |

### Placeholder Scan

- No "TBD", "TODO", or vague language found
- All code blocks contain complete implementations
- All file paths are exact
- All test assertions are specific

### Type Consistency

- `AuthorPresetKey` defined in `layoutPresets.ts`, re-exported as `AuthorPreset` from `studioStore.ts` for backward compat
- `UserLayout.panels` is `Record<string, PanelLayoutState>` — matches store format
- `saveUserLayout` returns `{ success, error? }` — consistent result type
- Factory default panel IDs are deterministic: `factory-manuscripts`, `factory-suggestions`, `factory-characters`

### Dependencies

- Task 1 -> 2 (presets map depends on types from Task 1)
- Task 1 -> 3 (CRUD depends on types from Task 1)
- Task 1,2,3 -> 4 (tests depend on all exports)
- Task 1,2 -> 5 (store imports depend on presets module)
- Task 1,2,5 -> 6 (component imports all dependencies)
- Task 5,6 -> 7 (wire-up depends on both)
- Task 6 -> 8 (component tests depend on component)
- Task 4,8 -> 9 (validation runs all tests)

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-23-layout-management.md`.**

Two execution options:
1. **Subagent-Driven (recommended)** — Fresh subagent per task, review between tasks
2. **Inline Execution** — Execute tasks in this session with checkpoints

Which approach?
