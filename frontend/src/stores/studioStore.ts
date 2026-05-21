import { create } from 'zustand';

export type StudioPanelKey =
  | 'suggestions'
  | 'ideas'
  | 'drafts'
  | 'manuscripts'
  | 'characters'
  | 'worldBible'
  | 'relationships'
  | 'arcs'
  | 'structure'
  | 'chapters'
  | 'canon'
  | 'generation'
  | 'review'
  | 'inspect'
  | 'notes'
  | 'jobs';

export type StudioRailMode = 'expanded' | 'collapsed' | 'overlay';
export type StudioContextMode = 'docked' | 'overlay' | 'closed';
export type AuthorPreset = 'idea-first' | 'character-first' | 'outline-first' | 'world-first';

const STUDIO_LAYOUT_STORAGE_KEY = 'studio-layout-v1';
const DEFAULT_LEFT_RAIL_WIDTH = 224;
const DEFAULT_CONTEXT_PANEL_WIDTH = 416;
const MIN_LEFT_RAIL_WIDTH = 192;
const MAX_LEFT_RAIL_WIDTH = 320;
const MIN_CONTEXT_PANEL_WIDTH = 320;
const MAX_CONTEXT_PANEL_WIDTH = 520;

export interface PersistedStudioLayout {
  leftRailMode: StudioRailMode;
  contextPanelMode: StudioContextMode;
  contextPanelPinned: boolean;
  leftRailWidth: number;
  contextPanelWidth: number;
}

export function clampStudioWidth(value: unknown, min: number, max: number, fallback: number): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) return fallback;
  return Math.max(min, Math.min(max, value));
}

export function parseStoredStudioLayout(raw: string | null): PersistedStudioLayout | null {
  if (raw === null) return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (typeof parsed !== 'object' || parsed === null) return null;
  const obj = parsed as Record<string, unknown>;
  const validRailModes = ['expanded', 'collapsed', 'overlay'] as const;
  const validContextModes = ['docked', 'overlay', 'closed'] as const;
  if (!validRailModes.includes(obj.leftRailMode as StudioRailMode)) return null;
  if (!validContextModes.includes(obj.contextPanelMode as StudioContextMode)) return null;
  return {
    leftRailMode: obj.leftRailMode as StudioRailMode,
    contextPanelMode: obj.contextPanelMode as StudioContextMode,
    contextPanelPinned: !!obj.contextPanelPinned,
    leftRailWidth: clampStudioWidth(obj.leftRailWidth, MIN_LEFT_RAIL_WIDTH, MAX_LEFT_RAIL_WIDTH, DEFAULT_LEFT_RAIL_WIDTH),
    contextPanelWidth: clampStudioWidth(obj.contextPanelWidth, MIN_CONTEXT_PANEL_WIDTH, MAX_CONTEXT_PANEL_WIDTH, DEFAULT_CONTEXT_PANEL_WIDTH),
  };
}

export interface PanelLayoutState {
  id: string;
  key: StudioPanelKey;
  position: { x: number; y: number };
  size: { width: number; height: number };
  visible: boolean;
  pinned: boolean;
  floating: boolean;
  zIndex: number;
  collapsedSections: Record<string, boolean>;
  scrollY: number;
}

export interface StudioLayoutState {
  panels: Record<string, PanelLayoutState>;
  nextZIndex: number;
  layoutPreset: string | null;
}

const STUDIO_LAYOUT_V2_KEY = (projectId: string) => `studio-layout-v2-${projectId}`;
  const MIN_PANEL_WIDTH = 240;
  const MIN_PANEL_HEIGHT = 180;
  const GRID_SIZE = 8;
  const MIN_PANEL_ZINDEX = 100;

interface PanelPreset {
  key: StudioPanelKey;
}

const LAYOUT_PRESETS: Record<AuthorPreset, PanelPreset[]> = {
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
};

function snapToGrid(value: number): number {
  return Math.round(value / GRID_SIZE) * GRID_SIZE;
}

function generatePanelId(): string {
  return `panel-${crypto.randomUUID?.() ?? Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

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
      nextZIndex: Object.values(parsed.panels ?? {}).reduce((max, p) => Math.max(max, p.zIndex), MIN_PANEL_ZINDEX) + 1,
      layoutPreset: parsed.layoutPreset ?? null,
    };
  } catch {
    return null;
  }
}

const LAYOUT_DEBOUNCE_MS = 500;

interface LayoutDebounceState {
  timer: ReturnType<typeof setTimeout> | null;
  pendingLayout: StudioLayoutState | null;
  pendingProjectId: string | null;
}

const _debounce: LayoutDebounceState = { timer: null, pendingLayout: null, pendingProjectId: null };

export function scheduleLayoutPersist(projectId: string, layout: StudioLayoutState): void {
  _debounce.pendingProjectId = projectId;
  _debounce.pendingLayout = layout;
  if (_debounce.timer != null) {
    clearTimeout(_debounce.timer);
  }
  _debounce.timer = setTimeout(() => {
    if (_debounce.pendingProjectId && _debounce.pendingLayout) {
      persistLayoutV2(_debounce.pendingProjectId, _debounce.pendingLayout);
    }
    _debounce.timer = null;
    _debounce.pendingLayout = null;
    _debounce.pendingProjectId = null;
  }, LAYOUT_DEBOUNCE_MS);
}

export function flushLayoutDebounce(): void {
  if (_debounce.timer != null) {
    clearTimeout(_debounce.timer);
    _debounce.timer = null;
  }
  if (_debounce.pendingProjectId && _debounce.pendingLayout) {
    persistLayoutV2(_debounce.pendingProjectId, _debounce.pendingLayout);
  }
  _debounce.pendingLayout = null;
  _debounce.pendingProjectId = null;
}

function persistLayout(state: StudioState): void {
  const layout: PersistedStudioLayout = {
    leftRailMode: state.leftRailMode,
    contextPanelMode: state.contextPanelMode,
    contextPanelPinned: state.contextPanelPinned,
    leftRailWidth: state.leftRailWidth,
    contextPanelWidth: state.contextPanelWidth,
  };
  try {
    localStorage.setItem(STUDIO_LAYOUT_STORAGE_KEY, JSON.stringify(layout));
  } catch {
    // Storage full or unavailable — ignore
  }
}

interface StudioState {
  activePanel: StudioPanelKey;
  leftRailMode: StudioRailMode;
  contextPanelMode: StudioContextMode;
  contextPanelPinned: boolean;
  leftRailWidth: number;
  contextPanelWidth: number;
  panelVisible: boolean;
  setActivePanel: (panel: StudioPanelKey) => void;
  setLeftRailMode: (mode: StudioRailMode) => void;
  setContextPanelMode: (mode: StudioContextMode) => void;
  setContextPanelPinned: (pinned: boolean) => void;
  setLeftRailWidth: (width: number) => void;
  setContextPanelWidth: (width: number) => void;
  setPanelVisible: (visible: boolean) => void;
  openPanel: (panel: StudioPanelKey) => void;
  resetLayout: () => void;
  toggleLeftRail: () => void;
  toggleContextPanel: () => void;
  closeDrawers: () => void;
  // Layout state (radial hub)
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
  loadLayout: (projectId: string) => void;
  applyPreset: (preset: AuthorPreset) => void;
  exportLayout: () => string;
  importLayout: (json: string) => boolean;
}

const stored = parseStoredStudioLayout(typeof localStorage !== 'undefined' ? localStorage.getItem(STUDIO_LAYOUT_STORAGE_KEY) : null);

export const useStudioStore = create<StudioState>((set) => ({
  activePanel: 'suggestions',
  leftRailMode: stored?.leftRailMode ?? 'expanded',
  contextPanelMode: stored?.contextPanelMode ?? 'docked',
  contextPanelPinned: stored?.contextPanelPinned ?? true,
  leftRailWidth: stored?.leftRailWidth ?? DEFAULT_LEFT_RAIL_WIDTH,
  contextPanelWidth: stored?.contextPanelWidth ?? DEFAULT_CONTEXT_PANEL_WIDTH,
  panelVisible: false,
  setActivePanel: (activePanel) => set({ activePanel }),
  setLeftRailMode: (leftRailMode) => {
    set((state) => {
      persistLayout({ ...state, leftRailMode });
      return { leftRailMode };
    });
  },
  setContextPanelMode: (contextPanelMode) => {
    set((state) => {
      persistLayout({ ...state, contextPanelMode });
      return { contextPanelMode };
    });
  },
  setContextPanelPinned: (contextPanelPinned) => {
    set((state) => {
      persistLayout({ ...state, contextPanelPinned });
      return { contextPanelPinned };
    });
  },
  setLeftRailWidth: (width) => {
    set((state) => {
      const clamped = Math.max(MIN_LEFT_RAIL_WIDTH, Math.min(MAX_LEFT_RAIL_WIDTH, width));
      persistLayout({ ...state, leftRailWidth: clamped });
      return { leftRailWidth: clamped };
    });
  },
  setContextPanelWidth: (width) => {
    set((state) => {
      const clamped = Math.max(MIN_CONTEXT_PANEL_WIDTH, Math.min(MAX_CONTEXT_PANEL_WIDTH, width));
      persistLayout({ ...state, contextPanelWidth: clamped });
      return { contextPanelWidth: clamped };
    });
  },
  setPanelVisible: (panelVisible) => set({ panelVisible }),
  openPanel: (activePanel) =>
    set((state) => ({
      activePanel,
      panelVisible: true,
      leftRailMode: state.leftRailMode === 'collapsed' ? 'expanded' : state.leftRailMode,
      contextPanelMode: state.contextPanelMode === 'closed' ? 'docked' : state.contextPanelMode,
    })),
  resetLayout: () => {
    set((state) => {
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
        layout: { panels: {}, nextZIndex: MIN_PANEL_ZINDEX, layoutPreset: null },
      };
    });
    persistLayout(useStudioStore.getState());
  },
  toggleLeftRail: () =>
    set((state) => {
      const next = state.leftRailMode === 'collapsed' ? 'expanded' : 'collapsed';
      persistLayout({ ...state, leftRailMode: next });
      return { leftRailMode: next };
    }),
  toggleContextPanel: () =>
    set((state) => ({
      contextPanelMode: state.contextPanelMode === 'overlay' ? 'closed' : 'overlay',
    })),
  closeDrawers: () =>
    set({
      leftRailMode: 'collapsed',
      contextPanelMode: 'closed',
      panelVisible: false,
    }),
  // Layout state initialization
  currentProjectId: null,
  layout: {
    panels: {},
    nextZIndex: MIN_PANEL_ZINDEX,
    layoutPreset: null,
  },
  setCurrentProjectId: (projectId) => set({ currentProjectId: projectId }),
  addPanel: (key) => {
    const id = generatePanelId();
    set((state) => {
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
      if (state.currentProjectId) scheduleLayoutPersist(state.currentProjectId, newLayout);
      return { layout: newLayout, currentProjectId: state.currentProjectId };
    });
    return id;
  },
  removePanel: (id) =>
    set((state) => {
      const newPanels = { ...state.layout.panels };
      delete newPanels[id];
      const newLayout = { ...state.layout, panels: newPanels };
      if (state.currentProjectId) scheduleLayoutPersist(state.currentProjectId, newLayout);
      return { layout: newLayout };
    }),
  movePanel: (id, position) =>
    set((state) => {
      const panel = state.layout.panels[id];
      if (!panel) return {};
      const snapped = { x: snapToGrid(position.x), y: snapToGrid(position.y) };
      const newPanels = { ...state.layout.panels, [id]: { ...panel, position: snapped } };
      const newLayout = { ...state.layout, panels: newPanels };
      if (state.currentProjectId) scheduleLayoutPersist(state.currentProjectId, newLayout);
      return { layout: newLayout };
    }),
  resizePanel: (id, size) =>
    set((state) => {
      const panel = state.layout.panels[id];
      if (!panel) return {};
      const clamped = {
        width: Math.max(MIN_PANEL_WIDTH, Math.min(size.width, 800)),
        height: Math.max(MIN_PANEL_HEIGHT, Math.min(size.height, 600)),
      };
      const newPanels = { ...state.layout.panels, [id]: { ...panel, size: clamped } };
      const newLayout = { ...state.layout, panels: newPanels };
      if (state.currentProjectId) scheduleLayoutPersist(state.currentProjectId, newLayout);
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
      if (state.currentProjectId) scheduleLayoutPersist(state.currentProjectId, newLayout);
      return { layout: newLayout };
    }),
  updatePanelState: (id, updates) =>
    set((state) => {
      const panel = state.layout.panels[id];
      if (!panel) return {};
      const newPanels = { ...state.layout.panels, [id]: { ...panel, ...updates } };
      const newLayout = { ...state.layout, panels: newPanels };
      if (state.currentProjectId) scheduleLayoutPersist(state.currentProjectId, newLayout);
      return { layout: newLayout };
    }),
  pinPanel: (id, pinned) =>
    set((state) => {
      const panel = state.layout.panels[id];
      if (!panel) return {};
      const newPanels = { ...state.layout.panels, [id]: { ...panel, pinned } };
      const newLayout = { ...state.layout, panels: newPanels };
      if (state.currentProjectId) scheduleLayoutPersist(state.currentProjectId, newLayout);
      return { layout: newLayout };
    }),
  tearOffPanel: (id) =>
    set((state) => {
      const panel = state.layout.panels[id];
      if (!panel) return {};
      const newPanels = { ...state.layout.panels, [id]: { ...panel, floating: true } };
      const newLayout = { ...state.layout, panels: newPanels };
      if (state.currentProjectId) scheduleLayoutPersist(state.currentProjectId, newLayout);
      return { layout: newLayout };
    }),
  reattachPanel: (id) =>
    set((state) => {
      const panel = state.layout.panels[id];
      if (!panel) return {};
      const newPanels = { ...state.layout.panels, [id]: { ...panel, floating: false } };
      const newLayout = { ...state.layout, panels: newPanels };
      if (state.currentProjectId) scheduleLayoutPersist(state.currentProjectId, newLayout);
      return { layout: newLayout };
    }),
  bringToFront: (id) =>
    set((state) => {
      const panel = state.layout.panels[id];
      if (!panel) return {};
      const newPanels = { ...state.layout.panels, [id]: { ...panel, zIndex: state.layout.nextZIndex } };
      return {
        activePanel: panel.key,
        layout: { ...state.layout, panels: newPanels, nextZIndex: state.layout.nextZIndex + 1 },
      };
    }),
  loadLayout: (projectId) =>
    set((state) => {
      if (state.currentProjectId === projectId) return {};
      const saved = loadLayoutV2(projectId);
      if (saved && Object.keys(saved.panels).length > 0) {
        // Ensure z-indexes are above minimum threshold
        let maxZ = MIN_PANEL_ZINDEX;
        const fixedPanels: Record<string, PanelLayoutState> = {};
        for (const [id, panel] of Object.entries(saved.panels)) {
          fixedPanels[id] = panel.zIndex < MIN_PANEL_ZINDEX
            ? { ...panel, zIndex: MIN_PANEL_ZINDEX + parseInt(id, 36) % 100 }
            : panel;
          maxZ = Math.max(maxZ, fixedPanels[id].zIndex);
        }
        return {
          currentProjectId: projectId,
          layout: { ...saved, panels: fixedPanels, nextZIndex: maxZ + 1 },
        };
      }
      // No saved layout — keep existing panels if usePanelUrlSync already created one
      const hasExisting = Object.keys(state.layout.panels).length > 0;
      return {
        currentProjectId: projectId,
        layout: hasExisting
          ? state.layout
          : { panels: {}, nextZIndex: MIN_PANEL_ZINDEX, layoutPreset: null },
      };
    }),
  applyPreset: (preset) =>
    set((state) => {
      const panels = LAYOUT_PRESETS[preset];
      if (!panels) return {};

      const newPanels: Record<string, PanelLayoutState> = {};
      let nextZ = state.layout.nextZIndex;

      for (let i = 0; i < panels.length; i++) {
        const panelDef = panels[i];
        const id = `preset-${preset}-${panelDef.key}`;
        const col = i % 4;
        const row = Math.floor(i / 4);
        newPanels[id] = {
          id,
          key: panelDef.key,
          position: {
            x: snapToGrid(16 + col * 296),
            y: snapToGrid(40 + row * 380),
          },
          size: { width: 280, height: 360 },
          visible: true,
          pinned: false,
          floating: false,
          zIndex: nextZ++,
          collapsedSections: {},
          scrollY: 0,
        };
      }

      const newLayout: StudioLayoutState = {
        panels: newPanels,
        nextZIndex: nextZ,
        layoutPreset: preset,
      };

      if (state.currentProjectId) {
        persistLayoutV2(state.currentProjectId, newLayout);
      }

      return { layout: newLayout };
    }),
  exportLayout: (): string => {
    const state = useStudioStore.getState();
    return JSON.stringify({ panels: state.layout.panels, layoutPreset: state.layout.layoutPreset }, null, 2);
  },
  importLayout: (json: string): boolean => {
    try {
      const parsed = JSON.parse(json) as { panels?: Record<string, PanelLayoutState>; layoutPreset?: string | null };
      if (!parsed || typeof parsed !== 'object' || !parsed.panels) return false;
      const zIdx = Object.values(parsed.panels).reduce((max, p) => Math.max(max, p.zIndex), 0) + 1;
      const newLayout: StudioLayoutState = {
        panels: parsed.panels,
        nextZIndex: zIdx,
        layoutPreset: parsed.layoutPreset ?? null,
      };
      const state = useStudioStore.getState();
      useStudioStore.setState({ layout: newLayout });
      if (state.currentProjectId) persistLayoutV2(state.currentProjectId, newLayout);
      return true;
    } catch {
      return false;
    }
  },
}));
