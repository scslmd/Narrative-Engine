import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useStudioStore, scheduleLayoutPersist, flushLayoutDebounce } from './studioStore';

describe('studioStore debounced persistence', () => {
  beforeEach(() => {
    localStorage.clear();
    useStudioStore.setState({
      currentProjectId: 'proj-1',
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
  });

  afterEach(() => {
    flushLayoutDebounce();
    localStorage.clear();
  });

  it('schedules layout persistence', () => {
    vi.useFakeTimers();
    scheduleLayoutPersist('proj-1', { panels: {}, nextZIndex: 1, layoutPreset: null });
    expect(localStorage.getItem('studio-layout-v2-proj-1')).toBeNull();
    vi.advanceTimersByTime(600);
    expect(localStorage.getItem('studio-layout-v2-proj-1')).not.toBeNull();
    vi.useRealTimers();
  });

  it('debounces multiple rapid calls', () => {
    vi.useFakeTimers();
    scheduleLayoutPersist('proj-1', { panels: { 'a': { id: 'a', key: 'ideas', position: { x: 0, y: 0 }, size: { width: 280, height: 360 }, visible: true, pinned: false, floating: false, zIndex: 1, collapsedSections: {}, scrollY: 0 } }, nextZIndex: 1, layoutPreset: null });
    scheduleLayoutPersist('proj-1', { panels: { 'b': { id: 'b', key: 'characters', position: { x: 0, y: 0 }, size: { width: 280, height: 360 }, visible: true, pinned: false, floating: false, zIndex: 2, collapsedSections: {}, scrollY: 0 } }, nextZIndex: 2, layoutPreset: null });
    scheduleLayoutPersist('proj-1', { panels: { 'c': { id: 'c', key: 'drafts', position: { x: 0, y: 0 }, size: { width: 280, height: 360 }, visible: true, pinned: false, floating: false, zIndex: 3, collapsedSections: {}, scrollY: 0 } }, nextZIndex: 3, layoutPreset: 'outline-first' });
    vi.advanceTimersByTime(600);
    const stored = JSON.parse(localStorage.getItem('studio-layout-v2-proj-1')!);
    expect(stored.layoutPreset).toBe('outline-first');
    expect(Object.keys(stored.panels)).toEqual(['c']);
    vi.useRealTimers();
  });

  it('flushes pending persistence', () => {
    scheduleLayoutPersist('proj-1', { panels: {}, nextZIndex: 1, layoutPreset: null });
    expect(localStorage.getItem('studio-layout-v2-proj-1')).toBeNull();
    flushLayoutDebounce();
    expect(localStorage.getItem('studio-layout-v2-proj-1')).not.toBeNull();
  });

  it('exportLayout returns JSON string', () => {
    const id = useStudioStore.getState().addPanel('characters');
    const json = useStudioStore.getState().exportLayout();
    const parsed = JSON.parse(json);
    expect(parsed.panels[id]).toBeDefined();
    expect(parsed.layoutPreset).toBeNull();
  });

  it('importLayout accepts valid JSON', () => {
    const json = JSON.stringify({
      panels: {
        'test-panel': {
          id: 'test-panel',
          key: 'characters',
          position: { x: 0, y: 0 },
          size: { width: 280, height: 360 },
          visible: true,
          pinned: false,
          floating: false,
          zIndex: 1,
          collapsedSections: {},
          scrollY: 0,
        },
      },
      layoutPreset: null,
    });
    const result = useStudioStore.getState().importLayout(json);
    expect(result).toBe(true);
    const panels = useStudioStore.getState().layout.panels;
    expect(panels['test-panel']).toBeDefined();
  });

  it('importLayout rejects invalid JSON', () => {
    const result = useStudioStore.getState().importLayout('not json');
    expect(result).toBe(false);
  });

  it('importLayout rejects missing panels', () => {
    const result = useStudioStore.getState().importLayout(JSON.stringify({ layoutPreset: null }));
    expect(result).toBe(false);
  });
});
