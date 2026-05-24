import { memo, useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useStudioStore } from '../../stores/studioStore';
import type { StudioPanelKey } from '../../stores/studioStore';

const PANEL_LABELS: Record<string, string> = {
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

interface StudioFloatingWindowProps {
  panelId: string;
  panelKey: StudioPanelKey;
  projectId: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  zIndex: number;
  children: React.ReactNode;
}

function StudioFloatingWindowImpl({
  panelId,
  panelKey,
  position,
  size,
  zIndex,
  children,
}: StudioFloatingWindowProps) {
  const resizePanel = useStudioStore((s) => s.resizePanel);
  const removePanel = useStudioStore((s) => s.removePanel);
  const reattachPanel = useStudioStore((s) => s.reattachPanel);
  const movePanel = useStudioStore((s) => s.movePanel);
  const bringToFront = useStudioStore((s) => s.bringToFront);

  const [pos, setPos] = useState(position);
  const [sz, setSz] = useState(size);
  const [dragging, setDragging] = useState(false);
  const [resizing, setResizing] = useState<'none' | 'right' | 'bottom' | 'corner' | 'left' | 'top'>('none');
  const dragRef = useRef<{ mouseStartX: number; mouseStartY: number; panelStartX: number; panelStartY: number } | null>(null);
  const resizeRef = useRef<{ startX: number; startY: number; startW: number; startH: number; startLeft: number; startTop: number } | null>(null);
  const rafRef = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const posRef = useRef(pos);
  posRef.current = pos;
  const szRef = useRef(sz);
  szRef.current = sz;

  useEffect(() => {
    setPos(position);
  }, [position]);

  useEffect(() => {
    setSz(size);
  }, [size]);

  const handleDragStart = useCallback((e: React.PointerEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setDragging(true);
    dragRef.current = {
      mouseStartX: e.clientX,
      mouseStartY: e.clientY,
      panelStartX: posRef.current.x,
      panelStartY: posRef.current.y,
    };
  }, []);

  useEffect(() => {
    if (!dragging || !dragRef.current) return;
    const handleMove = (e: PointerEvent) => {
      if (rafRef.current != null) return;
      rafRef.current = requestAnimationFrame(() => {
        const newX = dragRef.current!.panelStartX + (e.clientX - dragRef.current!.mouseStartX);
        const newY = dragRef.current!.panelStartY + (e.clientY - dragRef.current!.mouseStartY);
        setPos({ x: newX, y: newY });
        rafRef.current = null;
      });
    };
    const handleUp = () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      setDragging(false);
      dragRef.current = null;
      movePanel(panelId, posRef.current);
    };
    document.addEventListener('pointermove', handleMove);
    document.addEventListener('pointerup', handleUp);
    return () => {
      document.removeEventListener('pointermove', handleMove);
      document.removeEventListener('pointerup', handleUp);
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    };
  }, [dragging, panelId, movePanel]);

  const handleResizeStart = useCallback(
    (edge: 'right' | 'bottom' | 'corner' | 'left' | 'top', e: React.PointerEvent) => {
      e.stopPropagation();
      e.preventDefault();
      setResizing(edge);
      resizeRef.current = {
        startX: e.clientX,
        startY: e.clientY,
        startW: szRef.current.width,
        startH: szRef.current.height,
        startLeft: posRef.current.x,
        startTop: posRef.current.y,
      };
    },
    []
  );

  useEffect(() => {
    if (resizing === 'none' || !resizeRef.current) return;
    const handleMove = (e: PointerEvent) => {
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

        setSz({ width: newW, height: newH });
        setPos({ x: newLeft, y: newTop });
        rafRef.current = null;
      });
    };
    const handleUp = () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      setResizing('none');
      resizeRef.current = null;
      resizePanel(panelId, szRef.current);
      movePanel(panelId, posRef.current);
    };
    document.addEventListener('pointermove', handleMove);
    document.addEventListener('pointerup', handleUp);
    return () => {
      document.removeEventListener('pointermove', handleMove);
      document.removeEventListener('pointerup', handleUp);
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    };
  }, [resizing, panelId, resizePanel, movePanel]);

  const label = PANEL_LABELS[panelKey] || panelKey;

  const portalContent = (
    <div
      ref={containerRef}
      data-floating-window
      onClick={() => bringToFront(panelId)}
      className="flex flex-col overflow-hidden rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-2xl"
      style={{
        position: 'fixed',
        left: `${pos.x}px`,
        top: `${pos.y}px`,
        width: `${sz.width}px`,
        height: `${sz.height}px`,
        zIndex,
        transform: dragging ? 'scale(1.02)' : undefined,
        transition: dragging ? 'none' : 'box-shadow 0.15s, transform 0.1s',
      }}
    >
     <div
         className="flex shrink-0 items-center justify-between border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] px-2.5 py-1 cursor-grab active:cursor-grabbing select-none"
         onPointerDown={handleDragStart}
       >
         <span className="text-[10px] font-semibold text-[var(--text-primary)]">{label}</span>
         <div className="flex items-center gap-0.5">
           <button
             type="button"
             onClick={(e) => { e.stopPropagation(); reattachPanel(panelId); }}
             className="rounded px-1 py-0.5 text-[9px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
             title="Reattach"
           >
             &#x2281;
           </button>
           <button
             type="button"
             aria-label="Close panel"
             onClick={(e) => { e.stopPropagation(); removePanel(panelId); }}
             className="rounded px-1 py-0.5 text-[9px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
             title="Close"
           >
             &#x2715;
           </button>
         </div>
       </div>

      <div className="relative flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto p-2">{children}</div>

        <div
          className="z-10 absolute right-0 top-0 bottom-0 w-[2px] cursor-ew-resize opacity-0 hover:opacity-100 transition-opacity"
          style={{ background: 'var(--accent-primary)' }}
          onPointerDown={(e) => handleResizeStart('right', e)}
        />
        <div
          className="z-10 absolute left-0 top-0 bottom-0 w-[2px] cursor-ew-resize opacity-0 hover:opacity-100 transition-opacity"
          style={{ background: 'var(--accent-primary)' }}
          onPointerDown={(e) => handleResizeStart('left', e)}
        />
        <div
          className="z-10 absolute left-0 right-0 bottom-0 h-[2px] cursor-ns-resize opacity-0 hover:opacity-100 transition-opacity"
          style={{ background: 'var(--accent-primary)' }}
          onPointerDown={(e) => handleResizeStart('bottom', e)}
        />
        <div
          className="z-10 absolute left-0 right-0 top-0 h-[2px] cursor-ns-resize opacity-0 hover:opacity-100 transition-opacity"
          style={{ background: 'var(--accent-primary)' }}
          onPointerDown={(e) => handleResizeStart('top', e)}
        />
        <div
          className="z-10 absolute right-0 bottom-0 w-3 h-3 cursor-nwse-resize"
          onPointerDown={(e) => handleResizeStart('corner', e)}
        >
          <div className="absolute right-0.5 bottom-0.5 w-2 h-2 rotate-45 bg-[var(--text-secondary)]" />
        </div>
      </div>
    </div>
  );

  return typeof document !== 'undefined' ? createPortal(portalContent, document.body) : null;
}

export const StudioFloatingWindow = memo(StudioFloatingWindowImpl);
