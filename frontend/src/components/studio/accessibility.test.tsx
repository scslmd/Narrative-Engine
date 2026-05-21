import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent } from '../../__tests__/test-utils';
import { DndContext, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { useStudioStore } from '../../stores/studioStore';
import { StudioFloatingPanel } from './StudioFloatingPanel';
import { StudioPanelMenu } from './StudioPanelMenu';

function DndContextWrapper({ children }: { children: React.ReactNode }) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));
  return (
    <DndContext sensors={sensors}>
      {children}
    </DndContext>
  );
}

describe('Radial Hub Accessibility', () => {
  it('floating panel has ARIA role and label', () => {
    useStudioStore.setState({
      currentProjectId: null,
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
    const { container } = render(
      <DndContextWrapper>
        <StudioFloatingPanel
          panelId="test-1"
          panelKey="characters"
          projectId="proj-1"
          position={{ x: 0, y: 0 }}
          size={{ width: 280, height: 360 }}
          pinned={false}
          floating={false}
          zIndex={1}
        >
          <div>Content</div>
        </StudioFloatingPanel>
      </DndContextWrapper>
    );
    const panel = container.querySelector('[data-panel-container]');
    expect(panel).toHaveAttribute('role');
    expect(panel).toHaveAttribute('aria-label');
  });

  it('panel close button has aria-label', () => {
    useStudioStore.setState({
      currentProjectId: null,
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
    render(
      <DndContextWrapper>
        <StudioFloatingPanel
          panelId="test-1"
          panelKey="characters"
          projectId="proj-1"
          position={{ x: 0, y: 0 }}
          size={{ width: 280, height: 360 }}
          pinned={false}
          floating={false}
          zIndex={1}
        >
          <div>Content</div>
        </StudioFloatingPanel>
      </DndContextWrapper>
    );
    expect(screen.getByRole('button', { name: 'Close panel' })).toBeInTheDocument();
  });

  it('panel menu trigger has aria-haspopup', () => {
    useStudioStore.setState({
      currentProjectId: null,
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
    const { container } = render(<StudioPanelMenu projectId="proj-1" />);
    const trigger = container.querySelector('[aria-haspopup="menu"]');
    expect(trigger).toBeInTheDocument();
  });

  it('panel menu options have role menuitem', () => {
    useStudioStore.setState({
      currentProjectId: null,
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
    const { container } = render(<StudioPanelMenu projectId="proj-1" />);
    const trigger = container.querySelector('[aria-haspopup="menu"]');
    fireEvent.click(trigger as Element);
    const menuItems = container.querySelectorAll('[role="menuitem"]');
    expect(menuItems.length).toBeGreaterThan(0);
  });

  it('pinned panel hides close button', () => {
    useStudioStore.setState({
      currentProjectId: null,
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
    render(
      <DndContextWrapper>
        <StudioFloatingPanel
          panelId="test-1"
          panelKey="characters"
          projectId="proj-1"
          position={{ x: 0, y: 0 }}
          size={{ width: 280, height: 360 }}
          pinned={true}
          floating={false}
          zIndex={1}
        >
          <div>Content</div>
        </StudioFloatingPanel>
      </DndContextWrapper>
    );
    expect(screen.queryByRole('button', { name: 'Close panel' })).not.toBeInTheDocument();
  });

  it('pinned panel shows pin button', () => {
    useStudioStore.setState({
      currentProjectId: null,
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
    render(
      <DndContextWrapper>
        <StudioFloatingPanel
          panelId="test-1"
          panelKey="characters"
          projectId="proj-1"
          position={{ x: 0, y: 0 }}
          size={{ width: 280, height: 360 }}
          pinned={true}
          floating={false}
          zIndex={1}
        >
          <div>Content</div>
        </StudioFloatingPanel>
      </DndContextWrapper>
    );
    expect(screen.getByRole('button', { name: 'Unpin panel' })).toBeInTheDocument();
  });
});
