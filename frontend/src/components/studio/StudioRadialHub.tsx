import { memo, useCallback, useEffect, useMemo } from 'react';
import { DndContext, DragEndEvent, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { useStudioStore } from '../../stores/studioStore';
import { StudioFloatingPanel } from './StudioFloatingPanel';
import { StudioPanelContent } from './StudioPanelContent';

interface StudioRadialHubProps {
  projectId: string;
}

function StudioRadialHubImpl({ projectId }: StudioRadialHubProps) {
  const layout = useStudioStore((s) => s.layout);
  const movePanel = useStudioStore((s) => s.movePanel);
  const loadLayout = useStudioStore((s) => s.loadLayout);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  useEffect(() => {
    loadLayout(projectId);
  }, [projectId, loadLayout]);

  const visiblePanels = useMemo(
    () => Object.values(layout.panels).filter((p) => p.visible && !p.floating),
    [layout.panels]
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const currentPanels = useStudioStore.getState().layout.panels;
      const panelId = String(event.active.id);
      const panel = currentPanels[panelId];
      if (panel) {
        movePanel(panelId, {
          x: panel.position.x + event.delta.x,
          y: panel.position.y + event.delta.y,
        });
      }
    },
    [movePanel]
  );

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div
        data-radial-hub
        className="relative h-full w-full overflow-hidden bg-[var(--bg-tertiary)]"
      >
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage: 'radial-gradient(circle, var(--border-primary) 1px, transparent 1px)',
            backgroundSize: '8px 8px',
            opacity: 0.3,
          }}
        />
        {visiblePanels.map((panel) => (
          <StudioFloatingPanel
            key={panel.id}
            panelId={panel.id}
            panelKey={panel.key}
            projectId={projectId}
            position={panel.position}
            size={panel.size}
            pinned={panel.pinned}
            floating={panel.floating}
            zIndex={panel.zIndex}
          >
            <StudioPanelContent panelKey={panel.key} projectId={projectId} />
          </StudioFloatingPanel>
        ))}
      </div>
    </DndContext>
  );
}

export const StudioRadialHub = memo(StudioRadialHubImpl);
