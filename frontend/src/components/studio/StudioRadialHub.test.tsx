import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, act } from '../../__tests__/test-utils';
import { useStudioStore } from '../../stores/studioStore';
import { StudioRadialHub } from './StudioRadialHub';

vi.stubGlobal('ResizeObserver', class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
});

describe('StudioRadialHub', () => {
  beforeEach(() => {
    useStudioStore.setState({
      currentProjectId: null,
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
  });

  afterEach(() => {
    const panels = Object.keys(useStudioStore.getState().layout.panels);
    panels.forEach((id) => useStudioStore.getState().removePanel(id));
    useStudioStore.setState({ currentProjectId: null });
  });

  it('renders workspace container', () => {
    render(<StudioRadialHub projectId="proj-1" />);
    const container = document.querySelector('[data-radial-hub]');
    expect(container).toBeInTheDocument();
  });

  it('renders visible panels after store update', () => {
    render(<StudioRadialHub projectId="proj-1" />);
    act(() => {
      useStudioStore.getState().addPanel('characters');
    });
    expect(document.querySelector('[data-panel-container]')).toBeInTheDocument();
  });

  it('does not render hidden panels', () => {
    render(<StudioRadialHub projectId="proj-1" />);
    let panelId = '';
    act(() => {
      panelId = useStudioStore.getState().addPanel('ideas');
      useStudioStore.getState().togglePanel(panelId);
    });
    expect(screen.queryByText('Ideas')).not.toBeInTheDocument();
  });
});
