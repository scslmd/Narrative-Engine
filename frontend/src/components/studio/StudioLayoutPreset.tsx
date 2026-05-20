import { memo, useRef, useEffect, useState } from 'react';
import { useStudioStore, type AuthorPreset } from '../../stores/studioStore';

const LAYOUT_PRESETS_MENU: Record<AuthorPreset, string> = {
  'idea-first': 'Idea-First (Pantser)',
  'character-first': 'Character-First',
  'outline-first': 'Outline-First (Plotter)',
  'world-first': 'World-First',
};

function StudioLayoutPresetImpl() {
  const applyPreset = useStudioStore((s) => s.applyPreset);
  const doExportLayout = useStudioStore((s) => s.exportLayout);
  const doImportLayout = useStudioStore((s) => s.importLayout);
  const [open, setOpen] = useState(false);
  const [importText, setImportText] = useState('');
  const [showImport, setShowImport] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  const handleExport = () => {
    const json = doExportLayout();
    navigator.clipboard.writeText(json).catch(() => {
      setImportText(json);
      setShowImport(true);
    });
    setOpen(false);
  };

  const handleImport = () => {
    setImportError(null);
    const success = doImportLayout(importText);
    if (!success) {
      setImportError('Invalid layout JSON. Please check the format.');
    } else {
      setShowImport(false);
      setImportText('');
      setOpen(false);
    }
  };

  return (
    <div ref={menuRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="rounded-md px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
      >
        Layout &#x25BE;
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-1 min-w-[200px] rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-1 shadow-xl">
          <div className="mb-1 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
            Presets
          </div>
          {Object.entries(LAYOUT_PRESETS_MENU).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => { applyPreset(key as AuthorPreset); setOpen(false); }}
              className="flex w-full items-center rounded-md px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
            >
              {label}
            </button>
          ))}
          <div className="my-1 border-t border-[var(--border-primary)]" />
          <button
            type="button"
            onClick={handleExport}
            className="flex w-full items-center rounded-md px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
          >
            Export Layout (copy to clipboard)
          </button>
          <button
            type="button"
            onClick={() => setShowImport(!showImport)}
            className="flex w-full items-center rounded-md px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
          >
            Import Layout (paste JSON)
          </button>
          {showImport && (
            <div className="mt-1 p-2">
              <textarea
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
                placeholder="Paste layout JSON here..."
                className="h-24 w-full resize-none rounded-md border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-2 text-[10px] text-[var(--text-primary)]"
              />
              {importError && (
                <div className="mt-1 text-[10px] text-red-400">{importError}</div>
              )}
              <button
                type="button"
                onClick={handleImport}
                className="mt-1 w-full rounded-md bg-[var(--accent-primary)] px-2 py-1 text-[10px] font-medium text-white hover:opacity-90"
              >
                Apply Imported Layout
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export const StudioLayoutPreset = memo(StudioLayoutPresetImpl);
export { LAYOUT_PRESETS_MENU };
