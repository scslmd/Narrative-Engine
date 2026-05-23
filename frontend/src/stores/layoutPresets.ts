import type {
  PanelLayoutState,
  PersistedStudioLayout,
  StudioPanelKey,
} from './studioStore';

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

export interface SaveResult {
  success: boolean;
  error?: 'duplicate' | 'empty' | 'too_long' | 'quota' | null;
}

export interface RenameResult {
  success: boolean;
  error?: 'duplicate' | 'empty' | 'too_long' | 'not_found' | 'quota' | null;
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

// Built-in presets

interface PanelPresetDef {
  key: StudioPanelKey;
}

const BUILTIN_PRESETS: Record<AuthorPresetKey, PanelPresetDef[]> = {
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

// User layout CRUD

function readUserLayouts(): UserLayout[] {
  try {
    const raw = typeof localStorage !== 'undefined' ? localStorage.getItem(USER_LAYOUTS_KEY) : null;
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
  const current = readUserLayouts();
  const layouts = current.filter((l) => l.id !== id);
  if (layouts.length === current.length) return false;
  writeUserLayouts(layouts);
  return true;
}
