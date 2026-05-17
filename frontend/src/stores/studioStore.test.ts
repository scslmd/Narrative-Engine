import { beforeEach, describe, expect, it, afterEach } from 'vitest';
import { useStudioStore, parseStoredStudioLayout, clampStudioWidth } from './studioStore';

describe('studioStore persistence', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('has correct defaults when storage is empty', () => {
    useStudioStore.getState().resetLayout();
    localStorage.clear();
    useStudioStore.getState().resetLayout();
    const state = useStudioStore.getState();
    expect(state.leftRailMode).toBe('collapsed');
    expect(state.contextPanelMode).toBe('docked');
    expect(state.contextPanelPinned).toBe(true);
    expect(state.leftRailWidth).toBe(224);
    expect(state.contextPanelWidth).toBe(416);
  });

  it('parseStoredStudioLayout returns sanitized layout', () => {
    const result = parseStoredStudioLayout(JSON.stringify({
      leftRailMode: 'collapsed',
      contextPanelMode: 'overlay',
      contextPanelPinned: false,
      leftRailWidth: 256,
      contextPanelWidth: 480,
    }));
    expect(result).not.toBeNull();
    expect(result!.leftRailMode).toBe('collapsed');
    expect(result!.contextPanelMode).toBe('overlay');
    expect(result!.contextPanelPinned).toBe(false);
    expect(result!.leftRailWidth).toBe(256);
    expect(result!.contextPanelWidth).toBe(480);
  });

  it('parseStoredStudioLayout returns null for invalid JSON', () => {
    expect(parseStoredStudioLayout('not json')).toBeNull();
  });

  it('parseStoredStudioLayout clamps out-of-bounds widths', () => {
    const result = parseStoredStudioLayout(JSON.stringify({
      leftRailMode: 'collapsed',
      contextPanelMode: 'docked',
      contextPanelPinned: true,
      leftRailWidth: 100,
      contextPanelWidth: 600,
    }));
    expect(result).not.toBeNull();
    expect(result!.leftRailWidth).toBe(192);
    expect(result!.contextPanelWidth).toBe(520);
  });

  it('parseStoredStudioLayout returns null for invalid rail mode', () => {
    expect(parseStoredStudioLayout(JSON.stringify({
      leftRailMode: 'invalid',
      contextPanelMode: 'docked',
      contextPanelPinned: true,
      leftRailWidth: 224,
      contextPanelWidth: 416,
    }))).toBeNull();
  });

  it('parseStoredStudioLayout returns null for invalid context mode', () => {
    expect(parseStoredStudioLayout(JSON.stringify({
      leftRailMode: 'collapsed',
      contextPanelMode: 'invalid',
      contextPanelPinned: true,
      leftRailWidth: 224,
      contextPanelWidth: 416,
    }))).toBeNull();
  });

  it('clampStudioWidth returns fallback for non-finite values', () => {
    expect(clampStudioWidth('abc', 0, 100, 50)).toBe(50);
    expect(clampStudioWidth(NaN, 0, 100, 50)).toBe(50);
    expect(clampStudioWidth(Infinity, 0, 100, 50)).toBe(50);
    expect(clampStudioWidth(null, 0, 100, 50)).toBe(50);
    expect(clampStudioWidth(undefined, 0, 100, 50)).toBe(50);
  });

  it('clampStudioWidth clamps within bounds', () => {
    expect(clampStudioWidth(10, 20, 80, 50)).toBe(20);
    expect(clampStudioWidth(90, 20, 80, 50)).toBe(80);
    expect(clampStudioWidth(50, 20, 80, 50)).toBe(50);
  });

  it('resetLayout restores defaults and persists', () => {
    useStudioStore.getState().setLeftRailMode('collapsed');
    useStudioStore.getState().setContextPanelMode('closed');
    useStudioStore.getState().setLeftRailWidth(300);
    useStudioStore.getState().setContextPanelWidth(500);
    useStudioStore.getState().setActivePanel('ideas');
    useStudioStore.getState().setContextPanelPinned(false);

    useStudioStore.getState().resetLayout();
    const state = useStudioStore.getState();
    expect(state.activePanel).toBe('suggestions');
    expect(state.leftRailMode).toBe('collapsed');
    expect(state.contextPanelMode).toBe('docked');
    expect(state.contextPanelPinned).toBe(true);
    expect(state.leftRailWidth).toBe(224);
    expect(state.contextPanelWidth).toBe(416);

    const stored = localStorage.getItem('studio-layout-v1');
    expect(stored).not.toBeNull();
    const parsed = JSON.parse(stored!);
    expect(parsed.leftRailMode).toBe('collapsed');
    expect(parsed.contextPanelMode).toBe('docked');
    expect(parsed.leftRailWidth).toBe(224);
    expect(parsed.contextPanelWidth).toBe(416);
    expect(parsed.activePanel).toBeUndefined();
  });

  it('openPanel reopens closed context to docked', () => {
    useStudioStore.getState().setContextPanelMode('closed');
    useStudioStore.getState().openPanel('review');
    const state = useStudioStore.getState();
    expect(state.activePanel).toBe('review');
    expect(state.contextPanelMode).toBe('docked');
  });

  it('setter persistence writes only layout fields, never activePanel', () => {
    useStudioStore.getState().setLeftRailMode('collapsed');
    const stored = localStorage.getItem('studio-layout-v1');
    expect(stored).not.toBeNull();
    const parsed = JSON.parse(stored!);
    expect(parsed.activePanel).toBeUndefined();
    expect(parsed.leftRailMode).toBe('collapsed');
  });
});

describe('studioStore adaptive layout', () => {
  beforeEach(() => {
    localStorage.clear();
    useStudioStore.setState({
      activePanel: 'suggestions',
      leftRailMode: 'collapsed',
      contextPanelMode: 'docked',
      contextPanelPinned: true,
      leftRailWidth: 224,
      contextPanelWidth: 416,
    });
  });

  afterEach(() => {
    localStorage.clear();
    useStudioStore.setState({
      activePanel: 'suggestions',
      leftRailMode: 'collapsed',
      contextPanelMode: 'docked',
      contextPanelPinned: true,
      leftRailWidth: 224,
      contextPanelWidth: 416,
    });
  });

  it('has correct default adaptive state', () => {
    const state = useStudioStore.getState();
    expect(state.activePanel).toBe('suggestions');
    expect(state.leftRailMode).toBe('collapsed');
    expect(state.contextPanelMode).toBe('docked');
    expect(state.contextPanelPinned).toBe(true);
    expect(state.leftRailWidth).toBe(224);
    expect(state.contextPanelWidth).toBe(416);
  });

  it('setLeftRailMode changes rail mode', () => {
    useStudioStore.getState().setLeftRailMode('collapsed');
    expect(useStudioStore.getState().leftRailMode).toBe('collapsed');

    useStudioStore.getState().setLeftRailMode('overlay');
    expect(useStudioStore.getState().leftRailMode).toBe('overlay');
  });

  it('setContextPanelMode changes context mode', () => {
    useStudioStore.getState().setContextPanelMode('closed');
    expect(useStudioStore.getState().contextPanelMode).toBe('closed');

    useStudioStore.getState().setContextPanelMode('overlay');
    expect(useStudioStore.getState().contextPanelMode).toBe('overlay');
  });

  it('setContextPanelPinned toggles pin state', () => {
    useStudioStore.getState().setContextPanelPinned(false);
    expect(useStudioStore.getState().contextPanelPinned).toBe(false);

    useStudioStore.getState().setContextPanelPinned(true);
    expect(useStudioStore.getState().contextPanelPinned).toBe(true);
  });

  it('setLeftRailWidth clamps between 192 and 320', () => {
    useStudioStore.getState().setLeftRailWidth(100);
    expect(useStudioStore.getState().leftRailWidth).toBe(192);

    useStudioStore.getState().setLeftRailWidth(500);
    expect(useStudioStore.getState().leftRailWidth).toBe(320);

    useStudioStore.getState().setLeftRailWidth(256);
    expect(useStudioStore.getState().leftRailWidth).toBe(256);
  });

  it('setContextPanelWidth clamps between 320 and 520', () => {
    useStudioStore.getState().setContextPanelWidth(200);
    expect(useStudioStore.getState().contextPanelWidth).toBe(320);

    useStudioStore.getState().setContextPanelWidth(600);
    expect(useStudioStore.getState().contextPanelWidth).toBe(520);

    useStudioStore.getState().setContextPanelWidth(400);
    expect(useStudioStore.getState().contextPanelWidth).toBe(400);
  });

  it('openPanel sets active panel and reopens closed context', () => {
    useStudioStore.getState().setContextPanelMode('closed');
    useStudioStore.getState().openPanel('generation');
    const state = useStudioStore.getState();
    expect(state.activePanel).toBe('generation');
    expect(state.contextPanelMode).toBe('docked');
  });

  it('openPanel keeps context panel mode when not closed', () => {
    useStudioStore.getState().setContextPanelMode('overlay');
    useStudioStore.getState().openPanel('review');
    const state = useStudioStore.getState();
    expect(state.activePanel).toBe('review');
    expect(state.contextPanelMode).toBe('overlay');
  });

  it('resetLayout restores defaults', () => {
    useStudioStore.getState().setLeftRailMode('collapsed');
    useStudioStore.getState().setContextPanelMode('closed');
    useStudioStore.getState().setLeftRailWidth(300);
    useStudioStore.getState().setContextPanelWidth(500);
    useStudioStore.getState().setActivePanel('ideas');
    useStudioStore.getState().setContextPanelPinned(false);

    useStudioStore.getState().resetLayout();
    const state = useStudioStore.getState();
    expect(state.activePanel).toBe('suggestions');
    expect(state.leftRailMode).toBe('collapsed');
    expect(state.contextPanelMode).toBe('docked');
    expect(state.contextPanelPinned).toBe(true);
    expect(state.leftRailWidth).toBe(224);
    expect(state.contextPanelWidth).toBe(416);
  });

  it('toggleLeftRail toggles overlay mode', () => {
    useStudioStore.getState().toggleLeftRail();
    expect(useStudioStore.getState().leftRailMode).toBe('overlay');

    useStudioStore.getState().toggleLeftRail();
    expect(useStudioStore.getState().leftRailMode).toBe('collapsed');
  });

  it('toggleContextPanel toggles overlay mode', () => {
    useStudioStore.getState().toggleContextPanel();
    expect(useStudioStore.getState().contextPanelMode).toBe('overlay');

    useStudioStore.getState().toggleContextPanel();
    expect(useStudioStore.getState().contextPanelMode).toBe('closed');
  });

  it('closeDrawers closes both panels', () => {
    useStudioStore.getState().setLeftRailMode('overlay');
    useStudioStore.getState().setContextPanelMode('overlay');
    useStudioStore.getState().closeDrawers();
    const state = useStudioStore.getState();
    expect(state.leftRailMode).toBe('collapsed');
    expect(state.contextPanelMode).toBe('closed');
  });
});

describe('studioStore adaptive layout', () => {
  afterEach(() => {
    useStudioStore.setState({
      activePanel: 'suggestions',
      leftRailMode: 'collapsed',
      contextPanelMode: 'docked',
      contextPanelPinned: true,
      leftRailWidth: 224,
      contextPanelWidth: 416,
    });
  });

  it('has correct default adaptive state', () => {
    const state = useStudioStore.getState();
    expect(state.activePanel).toBe('suggestions');
    expect(state.leftRailMode).toBe('collapsed');
    expect(state.contextPanelMode).toBe('docked');
    expect(state.contextPanelPinned).toBe(true);
    expect(state.leftRailWidth).toBe(224);
    expect(state.contextPanelWidth).toBe(416);
  });

  it('setLeftRailMode changes rail mode', () => {
    useStudioStore.getState().setLeftRailMode('collapsed');
    expect(useStudioStore.getState().leftRailMode).toBe('collapsed');

    useStudioStore.getState().setLeftRailMode('overlay');
    expect(useStudioStore.getState().leftRailMode).toBe('overlay');
  });

  it('setContextPanelMode changes context mode', () => {
    useStudioStore.getState().setContextPanelMode('closed');
    expect(useStudioStore.getState().contextPanelMode).toBe('closed');

    useStudioStore.getState().setContextPanelMode('overlay');
    expect(useStudioStore.getState().contextPanelMode).toBe('overlay');
  });

  it('setContextPanelPinned toggles pin state', () => {
    useStudioStore.getState().setContextPanelPinned(false);
    expect(useStudioStore.getState().contextPanelPinned).toBe(false);

    useStudioStore.getState().setContextPanelPinned(true);
    expect(useStudioStore.getState().contextPanelPinned).toBe(true);
  });

  it('setLeftRailWidth clamps between 192 and 320', () => {
    useStudioStore.getState().setLeftRailWidth(100);
    expect(useStudioStore.getState().leftRailWidth).toBe(192);

    useStudioStore.getState().setLeftRailWidth(500);
    expect(useStudioStore.getState().leftRailWidth).toBe(320);

    useStudioStore.getState().setLeftRailWidth(256);
    expect(useStudioStore.getState().leftRailWidth).toBe(256);
  });

  it('setContextPanelWidth clamps between 320 and 520', () => {
    useStudioStore.getState().setContextPanelWidth(200);
    expect(useStudioStore.getState().contextPanelWidth).toBe(320);

    useStudioStore.getState().setContextPanelWidth(600);
    expect(useStudioStore.getState().contextPanelWidth).toBe(520);

    useStudioStore.getState().setContextPanelWidth(400);
    expect(useStudioStore.getState().contextPanelWidth).toBe(400);
  });

  it('openPanel sets active panel and reopens closed context', () => {
    useStudioStore.getState().setContextPanelMode('closed');
    useStudioStore.getState().openPanel('generation');
    const state = useStudioStore.getState();
    expect(state.activePanel).toBe('generation');
    expect(state.contextPanelMode).toBe('docked');
  });

  it('openPanel keeps context panel mode when not closed', () => {
    useStudioStore.getState().setContextPanelMode('overlay');
    useStudioStore.getState().openPanel('review');
    const state = useStudioStore.getState();
    expect(state.activePanel).toBe('review');
    expect(state.contextPanelMode).toBe('overlay');
  });

  it('resetLayout restores defaults', () => {
    useStudioStore.getState().setLeftRailMode('collapsed');
    useStudioStore.getState().setContextPanelMode('closed');
    useStudioStore.getState().setLeftRailWidth(300);
    useStudioStore.getState().setContextPanelWidth(500);
    useStudioStore.getState().setActivePanel('ideas');
    useStudioStore.getState().setContextPanelPinned(false);

    useStudioStore.getState().resetLayout();
    const state = useStudioStore.getState();
    expect(state.activePanel).toBe('suggestions');
    expect(state.leftRailMode).toBe('collapsed');
    expect(state.contextPanelMode).toBe('docked');
    expect(state.contextPanelPinned).toBe(true);
    expect(state.leftRailWidth).toBe(224);
    expect(state.contextPanelWidth).toBe(416);
  });

  it('toggleLeftRail toggles overlay mode', () => {
    useStudioStore.getState().toggleLeftRail();
    expect(useStudioStore.getState().leftRailMode).toBe('overlay');

    useStudioStore.getState().toggleLeftRail();
    expect(useStudioStore.getState().leftRailMode).toBe('collapsed');
  });

  it('toggleContextPanel toggles overlay mode', () => {
    useStudioStore.getState().toggleContextPanel();
    expect(useStudioStore.getState().contextPanelMode).toBe('overlay');

    useStudioStore.getState().toggleContextPanel();
    expect(useStudioStore.getState().contextPanelMode).toBe('closed');
  });

  it('closeDrawers closes both panels', () => {
    useStudioStore.getState().setLeftRailMode('overlay');
    useStudioStore.getState().setContextPanelMode('overlay');
    useStudioStore.getState().closeDrawers();
    const state = useStudioStore.getState();
    expect(state.leftRailMode).toBe('collapsed');
    expect(state.contextPanelMode).toBe('closed');
  });
});
