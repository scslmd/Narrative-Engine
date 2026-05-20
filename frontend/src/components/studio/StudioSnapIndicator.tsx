import { memo } from 'react';

export interface SnapZone {
  id: 'left-edge' | 'right-edge' | 'top' | 'bottom' | 'center';
  position: { x: number; y: number };
}

const SNAP_THRESHOLD = 100;
const GRID_SIZE = 8;

function snapToGrid(value: number): number {
  return Math.round(value / GRID_SIZE) * GRID_SIZE;
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
}

function StudioSnapIndicatorImpl({ snapZone }: StudioSnapIndicatorProps) {
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
