import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { DndContext, DragEndEvent, DragOverEvent, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { useStudioStore, type PanelLayoutState } from '../../stores/studioStore';
import { StudioFloatingPanel } from './StudioFloatingPanel';
import { StudioFloatingWindow } from './StudioFloatingWindow';
import { StudioPanelContent } from './StudioPanelContent';
import { StudioSnapIndicator, detectSnapZone, detectPanelSnap, type SnapZone, type PanelRect } from './StudioSnapIndicator';
import { usePanelKeyboard } from '../../hooks/usePanelKeyboard';
import { useMediaQuery } from '../../hooks/useMediaQuery';

interface StudioRadialHubProps {
  projectId: string;
}

function StudioRadialHubImpl({ projectId }: StudioRadialHubProps) {
  const layout = useStudioStore((s) => s.layout);
  const movePanel = useStudioStore((s) => s.movePanel);
  const bringToFront = useStudioStore((s) => s.bringToFront);

  const isMobile = useMediaQuery('(max-width: 1279px)');

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const workspaceRef = useRef<HTMLDivElement>(null);
  const [workspaceRect, setWorkspaceRect] = useState({ width: 0, height: 0 });
  const [dragState, setDragState] = useState<{ panelId: string; snapZone: SnapZone | null } | null>(null);

  usePanelKeyboard();

  useEffect(() => {
    const el = workspaceRef.current;
    if (!el) return;

    const measure = () => {
      const rect = el.getBoundingClientRect();
      setWorkspaceRect({ width: rect.width, height: rect.height });
    };
    measure();

    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const handleResize = () => {
      const panels = useStudioStore.getState().layout.panels;
      const w = workspaceRect.width;
      const h = workspaceRect.height;
      if (!w || !h) return;

      let changed = false;
      const updated: Record<string, PanelLayoutState> = { ...panels };
      for (const [id, panel] of Object.entries(updated)) {
        if (panel.floating) continue;
        const newX = Math.max(0, Math.min(panel.position.x, w - panel.size.width));
        const newY = Math.max(0, Math.min(panel.position.y, h - panel.size.height));
        if (newX !== panel.position.x || newY !== panel.position.y) {
          updated[id] = { ...panel, position: { x: newX, y: newY } };
          changed = true;
        }
      }
      if (changed) {
        useStudioStore.setState((state) => ({
          layout: { ...state.layout, panels: updated },
        }));
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [workspaceRect]);

  const allPanels = useMemo(
    () => Object.values(layout.panels).filter((p: PanelLayoutState) => p.visible),
    [layout.panels],
  );

  const visiblePanels = useMemo(
    () => Object.values(layout.panels).filter((p: PanelLayoutState) => p.visible && !p.floating),
    [layout.panels],
  );

  const floatingPanels = useMemo(
    () => Object.values(layout.panels).filter((p: PanelLayoutState) => p.visible && p.floating),
    [layout.panels],
  );

  const otherPanels: PanelRect[] = useMemo(
    () =>
      allPanels.map((p: PanelLayoutState) => ({
        id: p.id,
        x: p.position.x,
        y: p.position.y,
        width: p.size.width,
        height: p.size.height,
      })),
    [allPanels],
  );

  const handleDragStart = useCallback(
    (event: DragOverEvent) => {
      bringToFront(String(event.active.id));
    },
    [bringToFront],
  );

  const handleDragOver = useCallback(
    (event: DragOverEvent) => {
      const currentPanels = useStudioStore.getState().layout.panels;
      const panel = currentPanels[String(event.active.id)];
      if (!panel) return;

      const rawX = panel.position.x + event.delta.x;
      const rawY = panel.position.y + event.delta.y;

      const panelSnap = detectPanelSnap(
        String(event.active.id),
        rawX,
        rawY,
        panel.size.width,
        panel.size.height,
        otherPanels,
      );

      if (panelSnap) {
        setDragState({ panelId: String(event.active.id), snapZone: panelSnap });
        return;
      }

      const snapZone = detectSnapZone(
        String(event.active.id),
        rawX,
        rawY,
        panel.size.width,
        panel.size.height,
        workspaceRect.width,
        workspaceRect.height,
      );

      setDragState({ panelId: String(event.active.id), snapZone });
    },
    [workspaceRect, otherPanels],
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      setDragState(null);

      const currentPanels = useStudioStore.getState().layout.panels;
      const panel = currentPanels[String(event.active.id)];
      if (!panel) return;

      const rawX = panel.position.x + event.delta.x;
      const rawY = panel.position.y + event.delta.y;

      const panelSnap = detectPanelSnap(
        String(event.active.id),
        rawX,
        rawY,
        panel.size.width,
        panel.size.height,
        otherPanels,
      );

      if (panelSnap) {
        movePanel(String(event.active.id), panelSnap.position);
        return;
      }

      const snapZone = detectSnapZone(
        String(event.active.id),
        rawX,
        rawY,
        panel.size.width,
        panel.size.height,
        workspaceRect.width,
        workspaceRect.height,
      );

      if (snapZone) {
        movePanel(String(event.active.id), snapZone.position);
      } else {
        movePanel(String(event.active.id), {
          x: panel.position.x + event.delta.x,
          y: panel.position.y + event.delta.y,
        });
      }
    },
    [movePanel, workspaceRect, otherPanels],
  );

  if (isMobile) {
    return (
      <div
        data-radial-hub
        className="flex h-full w-full flex-col overflow-hidden bg-[var(--bg-tertiary)]"
        role="main"
        aria-label="Workspace"
      >
        {visiblePanels.map((panel: PanelLayoutState) => (
          <div
            key={panel.id}
            className="flex-shrink-0 border-b border-[var(--border-primary)]"
            style={{ height: '50vh', minHeight: '200px' }}
          >
            <StudioFloatingPanel
              panelId={panel.id}
              panelKey={panel.key}
              projectId={projectId}
              position={{ x: 0, y: 0 }}
              size={{ width: 9999, height: 9999 }}
              pinned={true}
              floating={false}
              zIndex={panel.zIndex}
            >
              <StudioPanelContent panelKey={panel.key} projectId={projectId} />
            </StudioFloatingPanel>
          </div>
        ))}
        {visiblePanels.length === 0 && (
          <div className="flex h-full items-center justify-center text-sm text-[var(--text-secondary)]">
            No panels open. Use the panel menu to add panels.
          </div>
        )}
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div
        ref={workspaceRef}
        data-radial-hub
        className="relative h-full w-full overflow-hidden bg-[var(--bg-tertiary)]"
        role="main"
        aria-label="Workspace"
      >
        <div
          className="pointer-events-none absolute inset-0"
          aria-hidden="true"
          style={{
            backgroundImage: 'radial-gradient(circle, var(--border-primary) 1px, transparent 1px)',
            backgroundSize: '8px 8px',
            opacity: 0.3,
          }}
        />

        <StudioSnapIndicator
          snapZone={dragState?.snapZone ?? null}
          otherPanels={otherPanels}
        />

        {visiblePanels.map((panel: PanelLayoutState) => (
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

        {floatingPanels.map((panel: PanelLayoutState) => (
          <StudioFloatingWindow
            key={panel.id}
            panelId={panel.id}
            panelKey={panel.key}
            projectId={projectId}
            position={panel.position}
            size={panel.size}
            zIndex={panel.zIndex}
          >
            <StudioPanelContent panelKey={panel.key} projectId={projectId} />
          </StudioFloatingWindow>
        ))}
      </div>
    </DndContext>
  );
}

export const StudioRadialHub = memo(StudioRadialHubImpl);
