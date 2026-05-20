import { memo, useCallback, useEffect, useRef, useState } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { useStudioStore } from '../../stores/studioStore';
import type { StudioPanelKey } from '../../stores/studioStore';

const PANEL_LABELS: Record<StudioPanelKey, string> = {
  suggestions: 'Suggestions',
  ideas: 'Ideas',
  drafts: 'Drafts',
  manuscripts: 'Manuscripts',
  characters: 'Characters',
  worldBible: 'World Bible',
  relationships: 'Relationships',
  arcs: 'Arcs',
  structure: 'Structure',
  chapters: 'Chapters',
  canon: 'Canon',
  generation: 'Generation',
  review: 'Review',
  inspect: 'Inspect',
  notes: 'Notes',
  jobs: 'Jobs',
};

interface StudioFloatingPanelProps {
  panelId: string;
  panelKey: StudioPanelKey;
  projectId: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  pinned: boolean;
  floating: boolean;
  zIndex: number;
  children: React.ReactNode;
}

function StudioFloatingPanelImpl({
  panelId,
  panelKey,
  position,
  size,
  pinned,
  floating,
  zIndex,
  children,
}: StudioFloatingPanelProps) {
  const resizePanel = useStudioStore((s) => s.resizePanel);
  const removePanel = useStudioStore((s) => s.removePanel);
  const pinPanel = useStudioStore((s) => s.pinPanel);
  const bringToFront = useStudioStore((s) => s.bringToFront);
  const reattachPanel = useStudioStore((s) => s.reattachPanel);

  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: panelId,
    disabled: floating,
  });

  const style: React.CSSProperties = {
    position: floating ? 'fixed' : 'absolute',
    left: `${position.x}px`,
    top: `${position.y}px`,
    width: `${size.width}px`,
    height: `${size.height}px`,
    zIndex,
    transform: transform ? `translate(${transform.x}px, ${transform.y}px)` : undefined,
    transition: transform ? 'none' : 'box-shadow 0.15s, left 0.1s, top 0.1s',
  };

  const [resizing, setResizing] = useState<'none' | 'right' | 'bottom' | 'corner'>('none');
  const resizeRef = useRef<{ startX: number; startY: number; startW: number; startH: number } | null>(null);
  const rafRef = useRef<number | null>(null);

  const handleResizeStart = useCallback(
    (edge: 'right' | 'bottom' | 'corner', e: React.MouseEvent) => {
      e.stopPropagation();
      e.preventDefault();
      setResizing(edge);
      resizeRef.current = { startX: e.clientX, startY: e.clientY, startW: size.width, startH: size.height };
    },
    [size]
  );

  useEffect(() => {
    if (resizing === 'none' || !resizeRef.current) return;
    const handleMove = (e: MouseEvent) => {
      if (rafRef.current != null) return;
      rafRef.current = requestAnimationFrame(() => {
        const dx = e.clientX - resizeRef.current!.startX;
        const dy = e.clientY - resizeRef.current!.startY;
        let newW = resizeRef.current!.startW;
        let newH = resizeRef.current!.startH;
        if (resizing === 'right' || resizing === 'corner') newW = Math.max(180, resizeRef.current!.startW + dx);
        if (resizing === 'bottom' || resizing === 'corner') newH = Math.max(120, resizeRef.current!.startH + dy);
        resizePanel(panelId, { width: newW, height: newH });
        rafRef.current = null;
      });
    };
    const handleUp = () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      setResizing('none');
      resizeRef.current = null;
    };
    document.addEventListener('mousemove', handleMove);
    document.addEventListener('mouseup', handleUp);
    return () => {
      document.removeEventListener('mousemove', handleMove);
      document.removeEventListener('mouseup', handleUp);
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    };
  }, [resizing, panelId, resizePanel]);

  const label = PANEL_LABELS[panelKey] || panelKey;

  return (
    <div
      ref={setNodeRef}
      data-panel-container
      {...attributes}
      {...listeners}
      onClick={() => bringToFront(panelId)}
      className="flex flex-col overflow-hidden rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-lg"
      style={style}
    >
      <div className="flex shrink-0 items-center justify-between border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-1.5 cursor-grab active:cursor-grabbing">
        <span className="text-xs font-semibold text-[var(--text-primary)]">{label}</span>
        <div className="flex items-center gap-1">
          {floating ? (
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); reattachPanel(panelId); }}
              className="rounded px-1.5 py-0.5 text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              title="Reattach"
            >
              &#x2281;
            </button>
          ) : (
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); pinPanel(panelId, !pinned); }}
              className={`rounded px-1.5 py-0.5 text-[10px] ${pinned ? 'text-amber-400' : 'text-[var(--text-secondary)]'} hover:text-[var(--text-primary)]`}
              title={pinned ? 'Unpin' : 'Pin'}
            >
              &#x1F4CC;
            </button>
          )}
          <button
            type="button"
            aria-label="Close panel"
            onClick={(e) => { e.stopPropagation(); removePanel(panelId); }}
            className="rounded px-1.5 py-0.5 text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            title="Close"
          >
            &#x2715;
          </button>
        </div>
      </div>

      <div className="relative flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto p-2">{children}</div>

        <div
          className="absolute right-0 top-0 bottom-0 w-1 cursor-ew-resize opacity-0 hover:opacity-100 transition-opacity"
          style={{ background: 'var(--accent-primary)' }}
          onMouseDown={(e) => handleResizeStart('right', e)}
        />
        <div
          className="absolute left-0 right-0 bottom-0 h-1 cursor-ns-resize opacity-0 hover:opacity-100 transition-opacity"
          style={{ background: 'var(--accent-primary)' }}
          onMouseDown={(e) => handleResizeStart('bottom', e)}
        />
        <div
          className="absolute right-0 bottom-0 w-3 h-3 cursor-nwse-resize"
          onMouseDown={(e) => handleResizeStart('corner', e)}
        >
          <div className="absolute right-0.5 bottom-0.5 w-2 h-2 rotate-45 bg-[var(--text-secondary)]" />
        </div>
      </div>
    </div>
  );
}

export const StudioFloatingPanel = memo(StudioFloatingPanelImpl);
