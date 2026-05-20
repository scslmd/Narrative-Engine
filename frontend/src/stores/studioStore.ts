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
  | 'generation'
  | 'review'
  | 'inspect'
  | 'notes'
  | 'jobs';

export type StudioRailMode = 'expanded' | 'collapsed' | 'overlay';
export type StudioContextMode = 'docked' | 'overlay' | 'closed';

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
    set({
      activePanel: 'suggestions',
      leftRailMode: 'collapsed',
      contextPanelMode: 'docked',
      contextPanelPinned: true,
      leftRailWidth: DEFAULT_LEFT_RAIL_WIDTH,
      contextPanelWidth: DEFAULT_CONTEXT_PANEL_WIDTH,
      panelVisible: false,
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
}));
