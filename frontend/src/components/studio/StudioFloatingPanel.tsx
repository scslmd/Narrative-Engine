import { memo, useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useDraggable } from '@dnd-kit/core';
import { useStudioStore, type StudioPanelKey } from '../../stores/studioStore';
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

  const [resizing, setResizing] = useState<'none' | 'right' | 'bottom' | 'corner' | 'left' | 'top'>('none');

  const { listeners, setNodeRef, transform } = useDraggable({
    id: panelId,
    disabled: floating || resizing !== 'none',
  });
  const resizeRef = useRef<{ startX: number; startY: number; startW: number; startH: number; startLeft: number; startTop: number; newW?: number; newH?: number; newLeft?: number; newTop?: number } | null>(null);
  const [dragSize, setDragSize] = useState<{ width: number; height: number } | null>(null);
  const [dragPosition, setDragPosition] = useState<{ x: number; y: number } | null>(null);

  const activeSize = dragSize ?? size;
  const activePosition = dragPosition ?? position;

  const style: React.CSSProperties = {
    position: floating ? 'fixed' : 'absolute',
    left: `${activePosition.x}px`,
    top: `${activePosition.y}px`,
    width: `${activeSize.width}px`,
    height: `${activeSize.height}px`,
    zIndex,
    transform: transform ? `translate(${transform.x}px, ${transform.y}px)` : undefined,
    transition: transform || resizing !== 'none'
      ? 'none'
      : 'box-shadow 0.15s, left 0.1s, top 0.1s',
    ...(resizing !== 'none' ? { boxShadow: '0 0 0 2px var(--accent-primary), 0 10px 40px rgba(0,0,0,0.3)' } : {}),
  };
  const rafRef = useRef<number | null>(null);

  const [hoveringHeader, setHoveringHeader] = useState(false);
  const [previewRect, setPreviewRect] = useState<{ left: number; top: number } | null>(null);
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const headerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    return () => {
      if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
    };
  }, []);

  const handleHeaderHover = useCallback(() => {
    if (headerRef.current) {
      const rect = headerRef.current.getBoundingClientRect();
      setPreviewRect({ left: rect.left, top: rect.bottom + 4 });
    }
    hoverTimerRef.current = setTimeout(() => setHoveringHeader(true), 400);
  }, []);

  const handleHeaderLeave = useCallback(() => {
    if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
    setHoveringHeader(false);
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

  // Block pointer events on resize handles so DndKit never sees them.
  // Only stopPropagation — preventDefault() would also cancel the mousedown.
  const handleResizePointerDown = useCallback((e: React.PointerEvent) => {
    e.stopPropagation();
  }, []);

  const MIN_W = 240;
  const MAX_W = 800;
  const MIN_H = 180;
  const MAX_H = 600;

  // Track which resize directions are blocked so we can show not-allowed cursor
  const [blockedEdges, setBlockedEdges] = useState<Set<string>>(new Set());

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

        const blocked = new Set<string>();

        if (resizing === 'right' || resizing === 'corner') {
          const raw = r.startW + dx;
          const clamped = Math.max(MIN_W, Math.min(MAX_W, raw));
          if (clamped !== raw) blocked.add('right');
          newW = clamped;
        }
        if (resizing === 'bottom' || resizing === 'corner') {
          const raw = r.startH + dy;
          const clamped = Math.max(MIN_H, Math.min(MAX_H, raw));
          if (clamped !== raw) blocked.add('bottom');
          newH = clamped;
        }
        if (resizing === 'left') {
          const raw = r.startW - dx;
          const clamped = Math.max(MIN_W, Math.min(MAX_W, raw));
          if (clamped !== raw) blocked.add('left');
          newW = clamped;
          newLeft = r.startLeft + (r.startW - newW);
        }
        if (resizing === 'top') {
          const raw = r.startH - dy;
          const clamped = Math.max(MIN_H, Math.min(MAX_H, raw));
          if (clamped !== raw) blocked.add('top');
          newH = clamped;
          newTop = r.startTop + (r.startH - newH);
        }

        resizeRef.current = { ...r, newW, newH, newLeft, newTop };
        setDragSize({ width: newW, height: newH });
        setDragPosition(newLeft != null || newTop != null
          ? { x: newLeft ?? r.startLeft, y: newTop ?? r.startTop }
          : null);
        setBlockedEdges(blocked);
        rafRef.current = null;
      });
    };
    const handleUp = () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      setBlockedEdges(new Set());
      setResizing('none');
      setDragSize(null);
      setDragPosition(null);
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

  const resizeHandleBase = 'absolute opacity-0 hover:opacity-100 transition-opacity touch-none';
  const resizeHandleVertical = 'absolute opacity-0 hover:opacity-100 transition-opacity touch-none';

  return (
    <div
      ref={assignPanelRef}
      data-panel-container
      role={panelRole}
      aria-label={panelAriaLabel}
      tabIndex={-1}
      {...listeners}
      onClick={() => bringToFront(panelId)}
      className="relative flex flex-col rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-lg"
      style={style}
    >
      {/* Inner wrapper with overflow-hidden for rounded corners */}
      <div className="flex h-full flex-col overflow-hidden">
        <div
          ref={headerRef}
          className="flex shrink-0 items-center justify-between border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-1.5 cursor-grab active:cursor-grabbing relative"
          onMouseEnter={handleHeaderHover}
          onMouseLeave={handleHeaderLeave}
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
        </div>

        {typeof document !== 'undefined' && hoveringHeader && previewRect &&
          createPortal(
            <div
              className="absolute z-50"
              style={{
                left: `${previewRect.left}px`,
                top: `${previewRect.top}px`,
              }}
            >
              <StudioHoverPreview
                panelKey={panelKey}
                isHovering={hoveringHeader}
                projectId={projectId}
              />
            </div>,
            document.body,
          )}

        <div className="relative flex-1 overflow-hidden">
          <div className="h-full overflow-y-auto p-2">{children}</div>
        </div>
      </div>

      {/* Resize handles - outside overflow-hidden wrapper, positioned relative to panel */}
      {/* Right handle */}
      <div
        data-resize-handle="right"
        className={resizeHandleBase}
        style={{
          right: '-6px',
          top: '0',
          width: '12px',
          height: `calc(100% - 20px)`,
          cursor: blockedEdges.has('right') ? 'not-allowed' : 'ew-resize',
          opacity: resizing !== 'none' ? 1 : undefined,
          background: resizing === 'right'
            ? (blockedEdges.has('right') ? '#ef4444' : 'var(--accent-primary)')
            : 'transparent',
        }}
        onPointerDown={(e) => handleResizePointerDown(e)}
        onMouseDown={(e) => handleResizeStart('right', e)}
        aria-hidden="true"
      />
      {/* Left handle */}
      <div
        data-resize-handle="left"
        className={resizeHandleBase}
        style={{
          left: '-6px',
          top: '0',
          width: '12px',
          height: '100%',
          cursor: blockedEdges.has('left') ? 'not-allowed' : 'ew-resize',
          opacity: resizing !== 'none' ? 1 : undefined,
          background: resizing === 'left'
            ? (blockedEdges.has('left') ? '#ef4444' : 'var(--accent-primary)')
            : 'transparent',
        }}
        onPointerDown={(e) => handleResizePointerDown(e)}
        onMouseDown={(e) => handleResizeStart('left', e)}
        aria-hidden="true"
      />
      {/* Bottom handle */}
      <div
        data-resize-handle="bottom"
        className={resizeHandleVertical}
        style={{
          left: '0',
          bottom: '-6px',
          width: 'calc(100% - 20px)',
          height: '12px',
          cursor: blockedEdges.has('bottom') ? 'not-allowed' : 'ns-resize',
          opacity: resizing !== 'none' ? 1 : undefined,
          background: resizing === 'bottom'
            ? (blockedEdges.has('bottom') ? '#ef4444' : 'var(--accent-primary)')
            : 'transparent',
        }}
        onPointerDown={(e) => handleResizePointerDown(e)}
        onMouseDown={(e) => handleResizeStart('bottom', e)}
        aria-hidden="true"
      />
      {/* Top handle */}
      <div
        data-resize-handle="top"
        className={resizeHandleVertical}
        style={{
          left: '0',
          top: '-6px',
          width: '100%',
          height: '12px',
          cursor: blockedEdges.has('top') ? 'not-allowed' : 'ns-resize',
          opacity: resizing !== 'none' ? 1 : undefined,
          background: resizing === 'top'
            ? (blockedEdges.has('top') ? '#ef4444' : 'var(--accent-primary)')
            : 'transparent',
        }}
        onPointerDown={(e) => handleResizePointerDown(e)}
        onMouseDown={(e) => handleResizeStart('top', e)}
        aria-hidden="true"
      />
          {/* Corner handle */}
      <div
        data-resize-handle="corner"
        className="absolute cursor-nwse-resize touch-none"
        style={{
          right: '-10px',
          bottom: '-10px',
          width: '20px',
          height: '20px',
          cursor: blockedEdges.has('right') && blockedEdges.has('bottom') ? 'not-allowed' : 'nwse-resize',
        }}
        onPointerDown={(e) => handleResizePointerDown(e)}
        onMouseDown={(e) => handleResizeStart('corner', e)}
        aria-hidden="true"
      >
        <div
          className="absolute right-1 bottom-1 w-2 h-2 rotate-45"
          style={{
            backgroundColor:
              resizing !== 'none' && blockedEdges.has('right') && blockedEdges.has('bottom')
                ? '#ef4444'
                : 'var(--text-secondary)',
          }}
        />
      </div>
    </div>
  );
}

export const StudioFloatingPanel = memo(StudioFloatingPanelImpl);
