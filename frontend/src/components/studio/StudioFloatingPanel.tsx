import { memo, useCallback, useEffect, useRef, useState } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { useStudioStore } from '../../stores/studioStore';
import type { StudioPanelKey } from '../../stores/studioStore';
import { StudioHoverPreview } from './StudioHoverPreview';

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
  projectId,
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
  const movePanel = useStudioStore((s) => s.movePanel);

  const { listeners, setNodeRef, transform } = useDraggable({
    id: panelId,
    disabled: floating,
  });

  const [resizing, setResizing] = useState<'none' | 'right' | 'bottom' | 'corner' | 'left' | 'top'>('none');
  const resizeRef = useRef<{ startX: number; startY: number; startW: number; startH: number; startLeft: number; startTop: number; newW?: number; newH?: number; newLeft?: number; newTop?: number } | null>(null);

  const style: React.CSSProperties = {
    position: floating ? 'fixed' : 'absolute',
    left: `${position.x}px`,
    top: `${position.y}px`,
    width: `${size.width}px`,
    height: `${size.height}px`,
    zIndex,
    transform: transform ? `translate(${transform.x}px, ${transform.y}px)` : undefined,
    transition: transform ? 'none' : 'box-shadow 0.15s, left 0.1s, top 0.1s',
    ...(resizing !== 'none' ? { boxShadow: '0 0 0 2px var(--accent-primary), 0 10px 40px rgba(0,0,0,0.3)' } : {}),
  };
  const rafRef = useRef<number | null>(null);

  const [hoveringHeader, setHoveringHeader] = useState(false);
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
    };
  }, []);

  const handleResizeStart = useCallback(
    (edge: 'right' | 'bottom' | 'corner' | 'left' | 'top', e: React.MouseEvent) => {
      e.stopPropagation();
      e.preventDefault();
      setResizing(edge);
      resizeRef.current = {
        startX: e.clientX,
        startY: e.clientY,
        startW: size.width,
        startH: size.height,
        startLeft: position.x,
        startTop: position.y,
      };
    },
    [size, position]
  );

  useEffect(() => {
    if (resizing === 'none' || !resizeRef.current) return;
    const handleMove = (e: MouseEvent) => {
      if (rafRef.current != null) return;
      rafRef.current = requestAnimationFrame(() => {
        const r = resizeRef.current!;
        const dx = e.clientX - r.startX;
        const dy = e.clientY - r.startY;
        let newW = r.startW;
        let newH = r.startH;
        let newLeft = r.startLeft;
        let newTop = r.startTop;

        if (resizing === 'right' || resizing === 'corner') newW = Math.max(180, r.startW + dx);
        if (resizing === 'bottom' || resizing === 'corner') newH = Math.max(120, r.startH + dy);
        if (resizing === 'left') {
          newW = Math.max(180, r.startW - dx);
          newLeft = r.startLeft + (r.startW - newW);
        }
        if (resizing === 'top') {
          newH = Math.max(120, r.startH - dy);
          newTop = r.startTop + (r.startH - newH);
        }

        resizeRef.current = { ...r, newW, newH, newLeft, newTop };
        rafRef.current = null;
      });
    };
    const handleUp = () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      setResizing('none');
      if (resizeRef.current) {
        resizePanel(panelId, { width: resizeRef.current.newW ?? resizeRef.current.startW, height: resizeRef.current.newH ?? resizeRef.current.startH });
        movePanel(panelId, { x: resizeRef.current.newLeft ?? resizeRef.current.startLeft, y: resizeRef.current.newTop ?? resizeRef.current.startTop });
      }
      resizeRef.current = null;
    };
    document.addEventListener('mousemove', handleMove);
    document.addEventListener('mouseup', handleUp);
    return () => {
      document.removeEventListener('mousemove', handleMove);
      document.removeEventListener('mouseup', handleUp);
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    };
  }, [resizing, panelId, resizePanel, movePanel, size, position]);

  const label = PANEL_LABELS[panelKey] || panelKey;
  const panelRole = floating ? 'dialog' : 'region';
  const panelAriaLabel = `${label} panel`;

  const panelRef = useRef<HTMLDivElement | null>(null);
  const assignPanelRef = useCallback((node: HTMLDivElement | null) => {
    setNodeRef(node);
    panelRef.current = node;
  }, [setNodeRef]);

  useEffect(() => {
    panelRef.current?.focus();
  }, [panelId]);

  return (
    <div
      ref={assignPanelRef}
      data-panel-container
      role={panelRole}
      aria-label={panelAriaLabel}
      tabIndex={-1}
      {...listeners}
      onClick={() => bringToFront(panelId)}
      className="flex flex-col overflow-hidden rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-lg"
      style={style}
    >
      <div
        className="flex shrink-0 items-center justify-between border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-1.5 cursor-grab active:cursor-grabbing relative"
        onMouseEnter={() => {
          hoverTimerRef.current = setTimeout(() => setHoveringHeader(true), 400);
        }}
        onMouseLeave={() => {
          if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
          setHoveringHeader(false);
        }}
      >
        <span className="text-xs font-semibold text-[var(--text-primary)]">{label}</span>
        <div className="flex items-center gap-1">
          {floating ? (
            <button
              type="button"
              aria-label="Reattach panel"
              onClick={(e) => { e.stopPropagation(); reattachPanel(panelId); }}
              className="rounded px-1.5 py-0.5 text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              title="Reattach"
            >
              &#x2281;
            </button>
          ) : (
            <button
              type="button"
              aria-label={pinned ? 'Unpin panel' : 'Pin panel'}
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
        <StudioHoverPreview
          panelKey={panelKey}
          isHovering={hoveringHeader}
          projectId={projectId}
        />
      </div>

      <div className="relative flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto p-2">{children}</div>

        <div
          data-resize-handle="right"
          className="z-10 absolute right-0 top-0 bottom-0 w-[2px] cursor-ew-resize opacity-0 hover:opacity-100 transition-opacity touch-none"
          style={{ background: 'var(--accent-primary)' }}
          onMouseDown={(e) => handleResizeStart('right', e)}
          aria-hidden="true"
        />
        <div
          data-resize-handle="left"
          className="z-10 absolute left-0 top-0 bottom-0 w-[2px] cursor-ew-resize opacity-0 hover:opacity-100 transition-opacity touch-none"
          style={{ background: 'var(--accent-primary)' }}
          onMouseDown={(e) => handleResizeStart('left', e)}
          aria-hidden="true"
        />
        <div
          data-resize-handle="bottom"
          className="z-10 absolute left-0 right-0 bottom-0 h-[2px] cursor-ns-resize opacity-0 hover:opacity-100 transition-opacity touch-none"
          style={{ background: 'var(--accent-primary)' }}
          onMouseDown={(e) => handleResizeStart('bottom', e)}
          aria-hidden="true"
        />
        <div
          data-resize-handle="top"
          className="z-10 absolute left-0 right-0 top-0 h-[2px] cursor-ns-resize opacity-0 hover:opacity-100 transition-opacity touch-none"
          style={{ background: 'var(--accent-primary)' }}
          onMouseDown={(e) => handleResizeStart('top', e)}
          aria-hidden="true"
        />
        <div
          data-resize-handle="corner"
          className="z-10 absolute right-0 bottom-0 w-3 h-3 cursor-nwse-resize touch-none"
          onMouseDown={(e) => handleResizeStart('corner', e)}
          aria-hidden="true"
        >
          <div className="absolute right-0.5 bottom-0.5 w-2 h-2 rotate-45 bg-[var(--text-secondary)]" />
        </div>
      </div>
    </div>
  );
}

export const StudioFloatingPanel = memo(StudioFloatingPanelImpl);
