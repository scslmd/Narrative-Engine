import { memo, useRef, useEffect, useState } from 'react';
import { Pencil, Trash2, Plus } from 'lucide-react';
import { useStudioStore, type AuthorPreset } from '../../stores/studioStore';
import {
  getBuiltInPresets,
  PRESET_LABELS,
  listUserLayouts,
  saveUserLayout,
  renameUserLayout,
  deleteUserLayout,
  type AuthorPresetKey,
} from '../../stores/layoutPresets';

function StudioLayoutManagerImpl() {
  const applyPreset = useStudioStore((s) => s.applyPreset);
  const applyUserLayout = useStudioStore((s) => s.applyUserLayout);
  const factoryReset = useStudioStore((s) => s.factoryReset);
  const doExportLayout = useStudioStore((s) => s.exportLayout);
  const doImportLayout = useStudioStore((s) => s.importLayout);
  const state = useStudioStore((s) => ({
    panels: s.layout.panels,
    v1State: {
      leftRailMode: s.leftRailMode,
      contextPanelMode: s.contextPanelMode,
      contextPanelPinned: s.contextPanelPinned,
      leftRailWidth: s.leftRailWidth,
      contextPanelWidth: s.contextPanelWidth,
    },
  }));

  const [open, setOpen] = useState(false);
  const [importText, setImportText] = useState('');
  const [showImport, setShowImport] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [showSaveInput, setShowSaveInput] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [renameError, setRenameError] = useState<string | null>(null);
  const [userLayouts, setUserLayouts] = useState(() => listUserLayouts());
  const [toast, setToast] = useState<{ msg: string; action?: string; onConfirm?: () => void } | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [open]);

  const refreshLayouts = () => setUserLayouts(listUserLayouts());

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
    if (doImportLayout(importText)) {
      setShowImport(false);
      setImportText('');
      setOpen(false);
    } else {
      setImportError('Invalid layout JSON.');
    }
  };

  const handleSave = () => {
    setSaveError(null);
    const result = saveUserLayout(saveName, { panels: state.panels, v1State: state.v1State });
    if (result.success) {
      setSaveName('');
      setShowSaveInput(false);
      refreshLayouts();
    } else {
      setSaveError(
        result.error === 'empty'
          ? 'Name required'
          : result.error === 'too_long'
            ? 'Max 50 chars'
            : 'Storage full'
      );
    }
  };

  const handleRename = (id: string) => {
    setRenameError(null);
    const result = renameUserLayout(id, editName);
    if (result.success) {
      setEditingId(null);
      setEditName('');
      refreshLayouts();
    } else {
      setRenameError(
        result.error === 'duplicate'
          ? 'Name exists'
          : result.error === 'empty'
            ? 'Name required'
            : 'Error'
      );
    }
  };

  const handleDelete = (id: string, name: string) => {
    setToast({
      msg: `Delete "${name}"?`,
      action: 'Delete',
      onConfirm: () => {
        deleteUserLayout(id);
        refreshLayouts();
        setToast(null);
      },
    });
  };

  const presets = getBuiltInPresets();

  return (
    <>
      <div ref={menuRef} className="relative">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="rounded-md px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
        >
          Layout &#9662;
        </button>

        {open && (
          <div className="absolute right-0 z-50 mt-1 min-w-[240px] max-h-[80vh] overflow-y-auto rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-1 shadow-xl">
            <div className="mb-1 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
              Presets
            </div>

            {Object.entries(presets).map(([key]) => (
              <button
                key={key}
                type="button"
                onClick={() => {
                  applyPreset(key as AuthorPreset);
                  setOpen(false);
                }}
                className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
              >
                <span className="text-[10px] text-[var(--text-tertiary)]">&#9658;</span>
                {PRESET_LABELS[key as AuthorPresetKey]}
              </button>
            ))}

            <div className="my-1 border-t border-[var(--border-primary)]" />

            <div className="mb-1 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
              My Layouts
            </div>

            {userLayouts.length === 0 && (
              <div className="px-3 py-2 text-[11px] text-[var(--text-tertiary)]">No saved layouts</div>
            )}

            {userLayouts.map((layout) => (
              <div key={layout.id} className="flex items-center">
                {editingId === layout.id ? (
                  <div className="flex w-full items-center gap-1">
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleRename(layout.id);
                        if (e.key === 'Escape') {
                          setEditingId(null);
                          setRenameError(null);
                        }
                      }}
                      maxLength={50}
                      className="flex-1 rounded border border-[var(--accent-primary)] bg-[var(--bg-secondary)] px-2 py-0.5 text-[11px] text-[var(--text-primary)] outline-none"
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => handleRename(layout.id)}
                      className="text-[10px] font-medium text-[var(--accent-primary)] hover:opacity-80"
                    >
                      Save
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => {
                        applyUserLayout(layout.id);
                        setOpen(false);
                      }}
                      className="flex flex-1 items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
                    >
                      <span className="text-[10px] text-[var(--text-tertiary)]">&#9658;</span>
                      <span className="truncate">{layout.name}</span>
                    </button>
                    <button
                      type="button"
                      title="Rename"
                      onClick={() => {
                        setEditingId(layout.id);
                        setEditName(layout.name);
                        setRenameError(null);
                      }}
                      className="p-1 text-[var(--text-tertiary)] transition-colors hover:text-[var(--text-primary)]"
                    >
                      <Pencil className="h-3 w-3" />
                    </button>
                    <button
                      type="button"
                      title="Delete"
                      onClick={() => handleDelete(layout.id, layout.name)}
                      className="p-1 text-[var(--text-tertiary)] transition-colors hover:text-red-400"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </>
                )}
              </div>
            ))}

            {renameError && <div className="mt-1 px-2 text-[10px] text-red-400">{renameError}</div>}

            <div className="my-1 border-t border-[var(--border-primary)]" />

            {showSaveInput ? (
              <div className="flex items-center gap-1 px-1">
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSave();
                    if (e.key === 'Escape') {
                      setShowSaveInput(false);
                      setSaveError(null);
                    }
                  }}
                  placeholder="Layout name..."
                  maxLength={50}
                  className="flex-1 rounded border border-[var(--accent-primary)] bg-[var(--bg-secondary)] px-2 py-1 text-[11px] text-[var(--text-primary)] outline-none"
                  autoFocus
                />
                <button
                  type="button"
                  onClick={handleSave}
                  className="rounded bg-[var(--accent-primary)] px-2 py-0.5 text-[10px] font-medium text-white hover:opacity-90"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowSaveInput(false);
                    setSaveError(null);
                  }}
                  className="rounded px-2 py-0.5 text-[10px] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setShowSaveInput(true);
                  setSaveName('');
                  setSaveError(null);
                }}
                className="flex w-full items-center gap-1.5 rounded-md px-3 py-1.5 text-xs text-[var(--text-tertiary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
              >
                <Plus className="h-3 w-3 text-green-500" />
                Save Current Layout
              </button>
            )}
            {saveError && <div className="mt-1 px-2 text-[10px] text-red-400">{saveError}</div>}

            <div className="my-1 border-t border-[var(--border-primary)]" />

            <button
              type="button"
              onClick={handleExport}
              className="flex w-full items-center rounded-md px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
            >
              Export Layout (clipboard)
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
                  placeholder="Paste layout JSON..."
                  className="h-20 w-full resize-none rounded-md border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-2 text-[10px] text-[var(--text-primary)]"
                />
                {importError && <div className="mt-1 text-[10px] text-red-400">{importError}</div>}
                <button
                  type="button"
                  onClick={handleImport}
                  className="mt-1 w-full rounded-md bg-[var(--accent-primary)] px-2 py-1 text-[10px] font-medium text-white hover:opacity-90"
                >
                  Apply Imported Layout
                </button>
              </div>
            )}

            <div className="my-1 border-t border-[var(--border-primary)]" />

            <button
              type="button"
              onClick={() => {
                setToast({
                  msg: 'Reset to Factory Default?',
                  action: 'Reset',
                  onConfirm: () => {
                    factoryReset();
                    setOpen(false);
                    setToast(null);
                  },
                });
              }}
              className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--text-tertiary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-red-400"
            >
              &#8634; Reset to Factory Default
            </button>
          </div>
        )}
      </div>

      {toast && (
        <div className="fixed bottom-6 right-6 z-[100] flex items-center gap-3 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-4 py-2.5 text-xs text-[var(--text-primary)] shadow-xl">
          <span>{toast.msg}</span>
          {toast.action && (
            <button
              onClick={() => {
                toast.onConfirm?.();
              }}
              className="font-semibold text-[var(--accent-primary)] hover:opacity-80"
            >
              {toast.action}
            </button>
          )}
          <button
            onClick={() => setToast(null)}
            className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
          >
            &#10005;
          </button>
        </div>
      )}
    </>
  );
}

export const StudioLayoutManager = memo(StudioLayoutManagerImpl);
