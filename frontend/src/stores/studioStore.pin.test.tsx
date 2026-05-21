import { describe, it, expect, beforeEach } from 'vitest';
import { useStudioStore } from './studioStore';

describe('studioStore pin behavior', () => {
  beforeEach(() => {
    useStudioStore.setState({
      currentProjectId: 'proj-1',
      activePanel: 'suggestions',
      leftRailMode: 'collapsed',
      contextPanelMode: 'docked',
      contextPanelPinned: true,
      leftRailWidth: 224,
      contextPanelWidth: 416,
      panelVisible: false,
      layout: { panels: {}, nextZIndex: 100, layoutPreset: null },
    });
  });

  it('blocks removePanel for pinned panels', () => {
    useStudioStore.getState().addPanel('suggestions');
    const panels = useStudioStore.getState().layout.panels;
    const id = Object.keys(panels)[0];

    useStudioStore.getState().pinPanel(id, true);
    useStudioStore.getState().removePanel(id);

    const after = useStudioStore.getState().layout.panels;
    expect(after[id]).toBeDefined();
  });

  it('allows removePanel for unpinned panels', () => {
    useStudioStore.getState().addPanel('suggestions');
    const panels = useStudioStore.getState().layout.panels;
    const id = Object.keys(panels)[0];

    useStudioStore.getState().removePanel(id);

    const after = useStudioStore.getState().layout.panels;
    expect(after[id]).toBeUndefined();
  });

  it('preserves pinned panels through resetLayout', () => {
    useStudioStore.getState().addPanel('suggestions');
    useStudioStore.getState().addPanel('characters');
    const panels = useStudioStore.getState().layout.panels;
    const ids = Object.keys(panels);
    useStudioStore.getState().pinPanel(ids[0], true);

    useStudioStore.getState().resetLayout();

    const after = useStudioStore.getState().layout.panels;
    expect(after[ids[0]]).toBeDefined();
    expect(after[ids[1]]).toBeUndefined();
  });

  it('preserves pinned panels through applyPreset', () => {
    useStudioStore.getState().addPanel('suggestions');
    const panels = useStudioStore.getState().layout.panels;
    const id = Object.keys(panels)[0];
    useStudioStore.getState().pinPanel(id, true);

    useStudioStore.getState().applyPreset('idea-first');

    const after = useStudioStore.getState().layout.panels;
    expect(after[id]).toBeDefined();
    expect(after[id]!.pinned).toBe(true);
  });
});
