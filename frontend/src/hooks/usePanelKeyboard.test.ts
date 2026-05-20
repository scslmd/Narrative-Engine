import { renderHook } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { usePanelKeyboard, PANEL_KEY_ORDER } from './usePanelKeyboard';
import { useStudioStore } from '../stores/studioStore';

describe('usePanelKeyboard', () => {
  beforeEach(() => {
    useStudioStore.setState({
      currentProjectId: 'proj-1',
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
  });

  it('registers keyboard event listener on document', () => {
    const originalAdd = document.addEventListener;
    const mockAdd = vi.fn();
    document.addEventListener = mockAdd as unknown as typeof document.addEventListener;

    renderHook(() => usePanelKeyboard());

    expect(mockAdd).toHaveBeenCalledWith('keydown', expect.any(Function));

    document.addEventListener = originalAdd;
  });

  it('handles Ctrl+Shift+W to close focused panel', () => {
    const panelId = useStudioStore.getState().addPanel('characters');

    renderHook(() => usePanelKeyboard());

    document.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'w',
      ctrlKey: true,
      shiftKey: true,
      altKey: false,
    }));

    const panels = useStudioStore.getState().layout.panels;
    expect(panels[panelId]).toBeUndefined();
  });
});

describe('PANEL_KEY_ORDER', () => {
  it('exports panel key order', () => {
    expect(PANEL_KEY_ORDER).toBeDefined();
    expect(PANEL_KEY_ORDER.length).toBeGreaterThan(0);
    expect(PANEL_KEY_ORDER[0]).toBe('characters');
  });
});
