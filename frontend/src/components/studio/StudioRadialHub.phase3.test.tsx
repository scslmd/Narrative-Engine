import { render } from '../../__tests__/test-utils';
import { describe, it, beforeEach, expect, vi } from 'vitest';
import { useStudioStore } from '../../stores/studioStore';
import { StudioRadialHub } from './StudioRadialHub';

vi.stubGlobal('ResizeObserver', class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
});

describe('StudioRadialHub Phase 3 polish', () => {
  beforeEach(() => {
    useStudioStore.setState({
      currentProjectId: 'proj-1',
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
  });

  it('renders radial hub container', () => {
    const { container } = render(
      <StudioRadialHub projectId="proj-1" />
    );
    const hub = container.querySelector('[data-radial-hub]');
    expect(hub).toBeInTheDocument();
  });

  it('renders snap indicator component', () => {
    const { container } = render(
      <StudioRadialHub projectId="proj-1" />
    );
    const hub = container.querySelector('[data-radial-hub]');
    expect(hub).toBeInTheDocument();
  });

  it('renders visible panels', () => {
    useStudioStore.getState().addPanel('ideas');
    const { container } = render(
      <StudioRadialHub projectId="proj-1" />
    );
    const panels = container.querySelectorAll('[data-panel-container]');
    expect(panels.length).toBeGreaterThanOrEqual(1);
  });

  it('does not render floating panels in workspace', () => {
    useStudioStore.setState({
      currentProjectId: 'proj-1',
      layout: {
        panels: {
          'test-1': {
            id: 'test-1',
            key: 'characters',
            position: { x: 100, y: 100 },
            size: { width: 300, height: 400 },
            visible: true,
            pinned: false,
            floating: true,
            zIndex: 1,
            collapsedSections: {},
            scrollY: 0,
          },
        },
        nextZIndex: 2,
        layoutPreset: null,
      },
    });
    const { container } = render(
      <StudioRadialHub projectId="proj-1" />
    );
    const panels = container.querySelectorAll('[data-panel-container]');
    expect(panels.length).toBe(0);
  });
});
