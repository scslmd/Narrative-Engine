import { useEffect, useCallback, useRef } from 'react';
import { useStudioStore, type PanelLayoutState } from '../stores/studioStore';
import type { StudioPanelKey } from '../stores/studioStore';

export const PANEL_KEY_ORDER: StudioPanelKey[] = [
  'characters',
  'relationships',
  'worldBible',
  'arcs',
  'structure',
  'chapters',
  'ideas',
  'generation',
  'review',
];

interface UsePanelKeyboardOptions {
  onTogglePanel?: (panelKey: StudioPanelKey) => void;
  onClosePanel?: (panelId: string) => void;
}

export function usePanelKeyboard(options?: UsePanelKeyboardOptions) {
  const addPanel = useStudioStore((s) => s.addPanel);
  const layout = useStudioStore((s) => s.layout);
  const removePanel = useStudioStore((s) => s.removePanel);
  const bringToFront = useStudioStore((s) => s.bringToFront);

  const layoutRef = useRef(layout);
  layoutRef.current = layout;

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!e.ctrlKey && !e.metaKey) return;

      if (e.key >= '1' && e.key <= '9' && e.shiftKey && !e.altKey) {
        const index = parseInt(e.key, 10) - 1;
        if (index < PANEL_KEY_ORDER.length) {
          e.preventDefault();
          const key = PANEL_KEY_ORDER[index];
          const panels = layoutRef.current.panels;

          const existing = Object.values(panels).find((p: PanelLayoutState) => p.key === key && p.visible);
          if (existing) {
            bringToFront(existing.id);
            options?.onTogglePanel?.(key);
          } else {
            addPanel(key);
            options?.onTogglePanel?.(key);
          }
          return;
        }
      }

      if (e.key.toLowerCase() === 'w' && e.shiftKey && !e.altKey) {
        const panels = layoutRef.current.panels;
        const visiblePanels = Object.values(panels).filter((p: PanelLayoutState) => p.visible && !p.floating) as PanelLayoutState[];
        if (visiblePanels.length > 0) {
          e.preventDefault();
          const topPanel = visiblePanels.sort((a, b) => b.zIndex - a.zIndex)[0];
          removePanel(topPanel.id);
          options?.onClosePanel?.(topPanel.id);
        }
        return;
      }

      if (e.key.toLowerCase() === 'w' && e.altKey) {
        e.preventDefault();
        const panels = layoutRef.current.panels;
        Object.keys(panels).forEach((id) => removePanel(id));
        return;
      }

      if (e.key === 'Escape') {
        return;
      }
    },
    [addPanel, removePanel, bringToFront, options]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return { panelKeyOrder: PANEL_KEY_ORDER };
}
