import { memo } from 'react';

export type SnapZoneId =
  | 'left-edge'
  | 'right-edge'
  | 'top'
  | 'bottom'
  | 'center'
  | 'panel-right'
  | 'panel-left'
  | 'panel-above'
  | 'panel-below';

export interface SnapZone {
  id: SnapZoneId;
  position: { x: number; y: number };
  targetPanelId?: string;
}

export interface PanelRect {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

const SNAP_THRESHOLD = 64;
const GRID_SIZE = 8;

function snapToGrid(value: number): number {
  return Math.round(value / GRID_SIZE) * GRID_SIZE;
}

export function detectPanelSnap(
  panelId: string,
  rawX: number,
  rawY: number,
  panelWidth: number,
  panelHeight: number,
  otherPanels: PanelRect[],
): SnapZone | null {
  const right = rawX + panelWidth;
  const bottom = rawY + panelHeight;

  let bestSnap: SnapZone | null = null;
  let bestGap = Infinity;

  for (const other of otherPanels) {
    if (other.id === panelId) continue;

    const otherRight = other.x + other.width;
    const otherBottom = other.y + other.height;

    // Snap to right of another panel
    const verticalOverlap = rawY < otherBottom && bottom > other.y;
    if (verticalOverlap) {
      const gapRight = Math.abs(rawX - otherRight);
      if (gapRight <= SNAP_THRESHOLD && gapRight < bestGap) {
        bestGap = gapRight;
        bestSnap = {
          id: 'panel-right',
          position: { x: snapToGrid(otherRight), y: snapToGrid(other.y) },
          targetPanelId: other.id,
        };
      }
      const gapLeft = Math.abs(right - other.x);
      if (gapLeft <= SNAP_THRESHOLD && gapLeft < bestGap) {
        bestGap = gapLeft;
        bestSnap = {
          id: 'panel-left',
          position: { x: snapToGrid(other.x - panelWidth), y: snapToGrid(other.y) },
          targetPanelId: other.id,
        };
      }
    }

    // Snap above another panel
    const horizontalOverlap = rawX < otherRight && right > other.x;
    if (horizontalOverlap) {
      const gapAbove = Math.abs(rawY - other.y);
      if (gapAbove <= SNAP_THRESHOLD && gapAbove < bestGap) {
        bestGap = gapAbove;
        bestSnap = {
          id: 'panel-above',
          position: { x: snapToGrid(other.x), y: snapToGrid(other.y - panelHeight) },
          targetPanelId: other.id,
        };
      }
      const gapBelow = Math.abs(bottom - other.y);
      if (gapBelow <= SNAP_THRESHOLD && gapBelow < bestGap) {
        bestGap = gapBelow;
        bestSnap = {
          id: 'panel-below',
          position: { x: snapToGrid(other.x), y: snapToGrid(otherBottom) },
          targetPanelId: other.id,
        };
      }
    }
  }

  return bestSnap;
}

export function detectSnapZone(
  _panelId: string,
  rawX: number,
  rawY: number,
  panelWidth: number,
  panelHeight: number,
  workspaceWidth: number,
  workspaceHeight: number,
): SnapZone | null {
  const cx = workspaceWidth / 2;
  const cy = workspaceHeight / 2;
  const panelCx = rawX + panelWidth / 2;
  const panelCy = rawY + panelHeight / 2;

  if (Math.abs(panelCx - cx) < 80 && Math.abs(panelCy - cy) < 80) {
    return {
      id: 'center',
      position: {
        x: snapToGrid(cx - panelWidth / 2),
        y: snapToGrid(cy - panelHeight / 2),
      },
    };
  }

  if (rawX < SNAP_THRESHOLD) {
    return {
      id: 'left-edge',
      position: { x: snapToGrid(16), y: snapToGrid(Math.max(40, Math.min(rawY, workspaceHeight - panelHeight - 16))) },
    };
  }

  if (rawX > workspaceWidth - SNAP_THRESHOLD - panelWidth) {
    return {
      id: 'right-edge',
      position: { x: snapToGrid(workspaceWidth - panelWidth - 16), y: snapToGrid(Math.max(40, Math.min(rawY, workspaceHeight - panelHeight - 16))) },
    };
  }

  if (rawY < SNAP_THRESHOLD) {
    return {
      id: 'top',
      position: { x: snapToGrid(Math.max(16, Math.min(rawX, workspaceWidth - panelWidth - 16))), y: snapToGrid(40) },
    };
  }

  if (rawY > workspaceHeight - SNAP_THRESHOLD - panelHeight) {
    return {
      id: 'bottom',
      position: {
        x: snapToGrid(Math.max(16, Math.min(rawX, workspaceWidth - panelWidth - 16))),
        y: snapToGrid(workspaceHeight - panelHeight - 16),
      },
    };
  }

  return null;
}

interface StudioSnapIndicatorProps {
  snapZone: SnapZone | null;
  otherPanels?: PanelRect[];
}

function StudioSnapIndicatorImpl({ snapZone, otherPanels = [] }: StudioSnapIndicatorProps) {
  if (!snapZone) return null;

  if (snapZone.id === 'center') {
    return (
      <div
        className="pointer-events-none absolute border-2 border-dashed border-blue-400/60 bg-blue-400/10 rounded-full"
        style={{
          left: '50%',
          top: '50%',
          width: 64,
          height: 64,
          transform: 'translate(-50%, -50%)',
        }}
      />
    );
  }

  const isPanelSnap = snapZone.id.startsWith('panel-');

  if (isPanelSnap && snapZone.targetPanelId) {
    const target = otherPanels.find((p) => p.id === snapZone.targetPanelId);
    if (!target) return null;

    const lineClass = 'pointer-events-none absolute bg-blue-400/60 transition-opacity duration-100';

    if (snapZone.id === 'panel-right') {
      return (
        <div
          className={lineClass}
          style={{ left: target.x + target.width, top: Math.min(target.y, snapZone.position.y), width: 2, height: Math.max(2, Math.min(target.y + target.height, snapZone.position.y) - Math.min(target.y, snapZone.position.y)) }}
        />
      );
    }

    if (snapZone.id === 'panel-left') {
      return (
        <div
          className={lineClass}
          style={{ left: target.x - 2, top: Math.min(target.y, snapZone.position.y), width: 2, height: Math.max(2, Math.min(target.y + target.height, snapZone.position.y) - Math.min(target.y, snapZone.position.y)) }}
        />
      );
    }

    if (snapZone.id === 'panel-above') {
      return (
        <div
          className={lineClass}
          style={{ top: target.y - 2, left: Math.min(target.x, snapZone.position.x), height: 2, width: Math.max(2, Math.min(target.x + target.width, snapZone.position.x) - Math.min(target.x, snapZone.position.x)) }}
        />
      );
    }

    if (snapZone.id === 'panel-below') {
      return (
        <div
          className={lineClass}
          style={{ top: target.y + target.height, left: Math.min(target.x, snapZone.position.x), height: 2, width: Math.max(2, Math.min(target.x + target.width, snapZone.position.x) - Math.min(target.x, snapZone.position.x)) }}
        />
      );
    }
  }

  return (
    <div
      className="pointer-events-none absolute bg-blue-400/60 transition-opacity duration-100"
      style={
        snapZone.id === 'left-edge'
          ? { left: 0, top: 0, bottom: 0, width: 2 }
          : snapZone.id === 'right-edge'
            ? { right: 0, top: 0, bottom: 0, width: 2 }
            : snapZone.id === 'top'
              ? { left: 0, right: 0, top: 0, height: 2 }
              : { left: 0, right: 0, bottom: 0, height: 2 }
      }
    />
  );
}

export const StudioSnapIndicator = memo(StudioSnapIndicatorImpl);
