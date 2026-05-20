import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { useStudioStore } from '../../stores/studioStore';
import { StudioFloatingPanel } from './StudioFloatingPanel';

describe('StudioFloatingPanel', () => {
  beforeEach(() => {
    useStudioStore.setState({
      currentProjectId: null,
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
  });

  it('renders children content', () => {
    render(
      <StudioFloatingPanel
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 0, y: 0 }}
        size={{ width: 240, height: 320 }}
        pinned={false}
        floating={false}
        zIndex={1}
      >
        <div data-testid="panel-content">Test content</div>
      </StudioFloatingPanel>
    );
    expect(screen.getByTestId('panel-content')).toBeInTheDocument();
  });

  it('applies position and size styles', () => {
    const { container } = render(
      <StudioFloatingPanel
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 16, y: 32 }}
        size={{ width: 200, height: 300 }}
        pinned={false}
        floating={false}
        zIndex={2}
      >
        <div>Content</div>
      </StudioFloatingPanel>
    );
    const panel = container.querySelector('[data-panel-container]');
    expect(panel).toHaveStyle({ left: '16px', top: '32px', width: '200px', height: '300px' });
  });

  it('shows close button', () => {
    render(
      <StudioFloatingPanel
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 0, y: 0 }}
        size={{ width: 240, height: 320 }}
        pinned={false}
        floating={false}
        zIndex={1}
      >
        <div>Content</div>
      </StudioFloatingPanel>
    );
    expect(screen.getByLabelText('Close panel')).toBeInTheDocument();
  });
});
