import { describe, it, expect, beforeEach } from 'vitest';
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

const mockPanels: Record<string, PanelLayoutState> = {
  'test-panel-1': {
    id: 'test-panel-1',
    key: 'manuscripts',
    position: { x: 0, y: 0 },
    size: { width: 320, height: 400 },
    visible: true,
    pinned: false,
    floating: false,
    zIndex: 100,
    collapsedSections: {},
    scrollY: 0,
  },
};

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
    expect(def.v1State.contextPanelPinned).toBe(true);
    expect(def.v1State.leftRailWidth).toBe(224);
    expect(def.v1State.contextPanelWidth).toBe(416);
  });

  it('returns 3 panels with correct IDs', () => {
    const def = getFactoryDefault();
    const ids = Object.keys(def.panels);
    expect(ids).toHaveLength(3);
    expect(ids).toContain('factory-manuscripts');
    expect(ids).toContain('factory-suggestions');
    expect(ids).toContain('factory-characters');
  });

  it('factory panels have correct keys', () => {
    const def = getFactoryDefault();
    expect(def.panels['factory-manuscripts'].key).toBe('manuscripts');
    expect(def.panels['factory-suggestions'].key).toBe('suggestions');
    expect(def.panels['factory-characters'].key).toBe('characters');
  });
});

describe('getBuiltInPresets', () => {
  it('returns 9 presets', () => {
    const presets = getBuiltInPresets();
    expect(Object.keys(presets)).toHaveLength(9);
  });

  it('includes existing 4 presets', () => {
    const presets = getBuiltInPresets();
    expect(presets['idea-first']).toBeDefined();
    expect(presets['character-first']).toBeDefined();
    expect(presets['outline-first']).toBeDefined();
    expect(presets['world-first']).toBeDefined();
  });

  it('includes new 5 presets', () => {
    const presets = getBuiltInPresets();
    expect(presets['beat-sheet']).toBeDefined();
    expect(presets['theme-driven']).toBeDefined();
    expect(presets['showrunner']).toBeDefined();
    expect(presets['revision-lab']).toBeDefined();
    expect(presets['world-builder-plus']).toBeDefined();
  });

  it('preset panels have correct keys', () => {
    const presets = getBuiltInPresets();
    expect(presets['beat-sheet'].map((p) => p.key)).toEqual(['structure', 'chapters', 'notes', 'generation']);
    expect(presets['showrunner'].map((p) => p.key)).toEqual(['characters', 'relationships', 'arcs', 'chapters', 'generation']);
  });
});

describe('PRESET_LABELS', () => {
  it('has label for each preset', () => {
    const presets = getBuiltInPresets();
    for (const key of Object.keys(presets)) {
      expect(PRESET_LABELS[key as keyof typeof PRESET_LABELS]).toBeDefined();
      expect(typeof PRESET_LABELS[key as keyof typeof PRESET_LABELS]).toBe('string');
    }
  });

  it('has correct labels for new presets', () => {
    expect(PRESET_LABELS['beat-sheet']).toBe('Beat-Sheet');
    expect(PRESET_LABELS['showrunner']).toBe('Showrunner');
    expect(PRESET_LABELS['revision-lab']).toBe('Revision Lab');
    expect(PRESET_LABELS['world-builder-plus']).toBe('World-Builder+');
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

  it('save trims whitespace from name', () => {
    const result = saveUserLayout('  Trimmed  ', { panels: mockPanels, v1State: mockV1 });
    expect(result.success).toBe(true);
    expect(listUserLayouts()[0].name).toBe('Trimmed');
  });

  it('save rejects empty name', () => {
    const result = saveUserLayout('', { panels: mockPanels, v1State: mockV1 });
    expect(result.success).toBe(false);
    expect(result.error).toBe('empty');
  });

  it('save rejects whitespace-only name', () => {
    const result = saveUserLayout('   ', { panels: mockPanels, v1State: mockV1 });
    expect(result.success).toBe(false);
    expect(result.error).toBe('empty');
  });

  it('save rejects name too long', () => {
    const result = saveUserLayout('a'.repeat(51), { panels: mockPanels, v1State: mockV1 });
    expect(result.success).toBe(false);
    expect(result.error).toBe('too_long');
  });

  it('save allows name at max length', () => {
    const result = saveUserLayout('a'.repeat(50), { panels: mockPanels, v1State: mockV1 });
    expect(result.success).toBe(true);
  });

  it('save overwrites existing layout with same name', () => {
    saveUserLayout('Test', { panels: { ...mockPanels }, v1State: mockV1 });
    const firstId = listUserLayouts()[0].id;
    saveUserLayout('Test', { panels: { ...mockPanels }, v1State: { ...mockV1, leftRailMode: 'collapsed' } });
    const layouts = listUserLayouts();
    expect(layouts).toHaveLength(1);
    expect(layouts[0].id).toBe(firstId);
    expect(layouts[0].v1State.leftRailMode).toBe('collapsed');
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

  it('rename rejects empty name', () => {
    saveUserLayout('Test', { panels: mockPanels, v1State: mockV1 });
    const id = listUserLayouts()[0].id;
    const result = renameUserLayout(id, '');
    expect(result.success).toBe(false);
    expect(result.error).toBe('empty');
  });

  it('rename returns not_found for unknown id', () => {
    const result = renameUserLayout('nonexistent', 'New');
    expect(result.success).toBe(false);
    expect(result.error).toBe('not_found');
  });

  it('delete removes layout', () => {
    saveUserLayout('ToDelete', { panels: mockPanels, v1State: mockV1 });
    const id = listUserLayouts()[0].id;
    expect(deleteUserLayout(id)).toBe(true);
    expect(listUserLayouts()).toHaveLength(0);
  });

  it('delete returns false for unknown id', () => {
    expect(deleteUserLayout('nonexistent')).toBe(false);
  });

  it('list returns sorted layouts', () => {
    saveUserLayout('Charlie', { panels: mockPanels, v1State: mockV1 });
    saveUserLayout('Alpha', { panels: mockPanels, v1State: mockV1 });
    saveUserLayout('Beta', { panels: mockPanels, v1State: mockV1 });
    const names = listUserLayouts().map((l) => l.name);
    expect(names).toEqual(['Alpha', 'Beta', 'Charlie']);
  });

  it('save preserves createdAt on overwrite', () => {
    saveUserLayout('Test', { panels: mockPanels, v1State: mockV1 });
    const original = listUserLayouts()[0];
    const result = saveUserLayout('Test', { panels: mockPanels, v1State: mockV1 });
    expect(result.success).toBe(true);
    const updated = listUserLayouts()[0];
    expect(updated.createdAt).toBe(original.createdAt);
    expect(updated.updatedAt).toBeGreaterThanOrEqual(original.updatedAt);
  });

  it('corrupt localStorage returns empty array', () => {
    localStorage.setItem(USER_LAYOUTS_KEY, 'not json');
    expect(listUserLayouts()).toHaveLength(0);
  });

  it('non-array localStorage returns empty array', () => {
    localStorage.setItem(USER_LAYOUTS_KEY, JSON.stringify({ bad: true }));
    expect(listUserLayouts()).toHaveLength(0);
  });
});
