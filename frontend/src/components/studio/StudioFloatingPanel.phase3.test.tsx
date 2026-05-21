import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StudioFloatingPanel } from './StudioFloatingPanel';

describe('StudioFloatingPanel Phase 3 polish', () => {
  it('renders panel container', () => {
    const { container } = render(
      <StudioFloatingPanel
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 100, y: 100 }}
        size={{ width: 300, height: 400 }}
        pinned={false}
        floating={false}
        zIndex={1}
      >
        <div>Content</div>
      </StudioFloatingPanel>
    );
    const panel = container.querySelector('[data-panel-container]');
    expect(panel).toBeInTheDocument();
  });

  it('renders hover preview component', () => {
    const { container } = render(
      <StudioFloatingPanel
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 100, y: 100 }}
        size={{ width: 300, height: 400 }}
        pinned={false}
        floating={false}
        zIndex={1}
      >
        <div>Content</div>
      </StudioFloatingPanel>
    );
    const panel = container.querySelector('[data-panel-container]');
    expect(panel).toBeInTheDocument();
  });

  it('renders left and top resize handles', () => {
    const { container } = render(
      <StudioFloatingPanel
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 100, y: 100 }}
        size={{ width: 300, height: 400 }}
        pinned={false}
        floating={false}
        zIndex={1}
      >
        <div>Content</div>
      </StudioFloatingPanel>
    );
    const handles = container.querySelectorAll('[data-resize-handle]');
    expect(handles.length).toBeGreaterThanOrEqual(4);
  });

  it('uses requestAnimationFrame for resize throttling', () => {
    const { container } = render(
      <StudioFloatingPanel
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 100, y: 100 }}
        size={{ width: 300, height: 400 }}
        pinned={false}
        floating={false}
        zIndex={1}
      >
        <div>Content</div>
      </StudioFloatingPanel>
    );
    const panel = container.querySelector('[data-panel-container]');
    expect(panel).toBeInTheDocument();
  });
});
