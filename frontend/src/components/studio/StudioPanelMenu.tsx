import { memo, useRef, useEffect, useState } from 'react';
import { useStudioStore } from '../../stores/studioStore';
import type { StudioPanelKey } from '../../stores/studioStore';
import { useMediaQuery } from '../../hooks/useMediaQuery';

const PANEL_OPTIONS: { key: StudioPanelKey; label: string }[] = [
  { key: 'characters', label: 'Characters' },
  { key: 'relationships', label: 'Relationships' },
  { key: 'worldBible', label: 'World Bible' },
  { key: 'arcs', label: 'Arcs' },
  { key: 'structure', label: 'Structure' },
  { key: 'chapters', label: 'Chapters' },
  { key: 'ideas', label: 'Ideas' },
  { key: 'manuscripts', label: 'Manuscripts' },
  { key: 'generation', label: 'Generation' },
  { key: 'review', label: 'Review' },
  { key: 'inspect', label: 'Inspect' },
  { key: 'canon', label: 'Canon' },
];

interface StudioPanelMenuProps {
  projectId: string;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function StudioPanelMenuImpl({ projectId: _projectId }: StudioPanelMenuProps) {
  const addPanel = useStudioStore((s) => s.addPanel);
  const layout = useStudioStore((s) => s.layout);
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const isMobile = useMediaQuery('(max-width: 1279px)');

  const visibleKeys = new Set(Object.values(layout.panels).map((p) => p.key));

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  const handleAddPanel = (key: StudioPanelKey) => {
    addPanel(key);
    setOpen(false);
  };

  if (isMobile) {
    return (
      <div ref={menuRef} className="relative">
        <button
          type="button"
          aria-label="Panel menu"
          aria-expanded={open}
          aria-haspopup="menu"
          onClick={() => setOpen(!open)}
          className="rounded-md px-3 py-2 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
        >
          Panels
        </button>
        {open && (
          <div
            role="menu"
            className="fixed bottom-4 left-4 right-4 z-50 max-h-[60vh] overflow-y-auto rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-1 shadow-xl"
          >
            {PANEL_OPTIONS.map((option) => {
              const isActive = visibleKeys.has(option.key);
              return (
                <button
                  key={option.key}
                  role="menuitem"
                  type="button"
                  onClick={() => handleAddPanel(option.key)}
                  className={`flex w-full items-center justify-between rounded-md px-3 py-2.5 text-sm transition-colors ${
                    isActive
                      ? 'bg-[var(--bg-secondary)] text-[var(--text-primary)]'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]'
                  }`}
                >
                  <span>{option.label}</span>
                  {isActive && <span className="text-xs text-emerald-400">&#10003;</span>}
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  return (
    <div ref={menuRef} className="relative">
      <button
        type="button"
        aria-label="Panel menu"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen(!open)}
        className="rounded-md px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
      >
        Panels &#x25BE;
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 z-50 mt-1 min-w-[180px] rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-1 shadow-xl"
        >
          {PANEL_OPTIONS.map((option) => {
            const isActive = visibleKeys.has(option.key);
            return (
              <button
                key={option.key}
                role="menuitem"
                type="button"
                onClick={() => handleAddPanel(option.key)}
                className={`flex w-full items-center justify-between rounded-md px-3 py-1.5 text-xs transition-colors ${
                  isActive
                    ? 'bg-[var(--bg-secondary)] text-[var(--text-primary)]'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                <span>{option.label}</span>
                {isActive && <span className="text-[10px] text-emerald-400">&#10003;</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export const StudioPanelMenu = memo(StudioPanelMenuImpl);
