import { useCallback, useMemo, useState } from 'react';
import { ManuscriptList } from '../writing/ManuscriptList';
import { DiffViewer } from '../aids/DiffViewer';
import { useWritingView } from '../../hooks/useWritingView';
import { useSettingsStore } from '../../stores/settingsStore';
import { useThemeStore } from '../../stores/themeStore';
import { resolveEffectiveMode } from '../../theme/theme';
import { GitCompare, X, History } from 'lucide-react';

interface StudioManuscriptsPanelProps {
  onSelect?: (documentId: string) => void;
}

export function StudioManuscriptsPanel({ onSelect }: StudioManuscriptsPanelProps) {
  const { mode: themeMode } = useThemeStore();
  const isDark = resolveEffectiveMode(themeMode) === 'dark';
  const { outlineDetail } = useSettingsStore();

  const {
    manuscriptDocuments,
    selectedDocumentId,
    manuscriptQueryLoading,
    setSelectedDocumentId,
    setIsEditing,
    setEditContent,
    revisionHistory,
  } = useWritingView(isDark);

  const [scrollTarget, setScrollTarget] = useState<{ documentId: string; lineIndex: number } | null>(null);
  const [compareMode, setCompareMode] = useState(false);
  const [compareBaseId, setCompareBaseId] = useState<string | null>(null);
  const [compareTargetId, setCompareTargetId] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  const handleOutlineNavigate = useCallback((documentId: string, lineIndex: number) => {
    setScrollTarget({ documentId, lineIndex });
  }, []);

  const handleSelect = (id: string) => {
    if (compareMode) {
      if (!compareBaseId) {
        setCompareBaseId(id);
      } else if (id !== compareBaseId) {
        setCompareTargetId(id);
      }
      return;
    }
    setSelectedDocumentId(id);
    setIsEditing(false);
    setEditContent('');
    onSelect?.(id);
  };

  const baseDoc = useMemo(
    () => manuscriptDocuments.find((d) => d.document_id === compareBaseId),
    [manuscriptDocuments, compareBaseId],
  );
  const targetDoc = useMemo(
    () => manuscriptDocuments.find((d) => d.document_id === compareTargetId),
    [manuscriptDocuments, compareTargetId],
  );

  const includeParagraphs = outlineDetail === 'detailed';

  const exitCompare = () => {
    setCompareMode(false);
    setCompareBaseId(null);
    setCompareTargetId(null);
  };

  const exitHistory = () => {
    setShowHistory(false);
  };

  if (showHistory && selectedDocumentId) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between px-2.5 py-1 border-b border-gray-200 dark:border-slate-700">
          <div className="flex items-center gap-1.5">
            <History className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-[9px] font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400">
              Revision History
            </span>
          </div>
          <button onClick={exitHistory} className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-300">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {revisionHistory.length === 0 ? (
            <p className="text-[10px] text-gray-400 dark:text-slate-500 text-center py-4">
              No revision history for this document.
            </p>
          ) : (
            <div className="space-y-1.5">
              {revisionHistory.map((entry, i) => (
                <div key={i} className={`rounded border p-1.5 text-[10px] ${isDark ? 'border-slate-700 bg-slate-800' : 'border-gray-200 bg-white'}`}>
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="font-medium text-gray-600 dark:text-slate-400">v{entry.version}</span>
                    <span className="text-gray-400 dark:text-slate-500">
                      {new Date(entry.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <pre className="text-gray-500 dark:text-slate-400 truncate">{entry.content.slice(0, 80)}...</pre>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-2.5 py-1 border-b border-gray-200 dark:border-slate-700">
        <span className="text-[9px] text-gray-500 dark:text-slate-400">
          {manuscriptDocuments.length} documents
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => {
              if (compareMode) exitCompare();
              else setCompareMode(true);
            }}
            className={`flex items-center gap-1 rounded px-1.5 py-0.5 text-[9px] transition-colors ${
              compareMode
                ? 'bg-blue-600 text-white'
                : 'text-gray-500 dark:text-slate-400 hover:bg-gray-200 dark:hover:bg-slate-700'
            }`}
            title="Compare two documents"
          >
            <GitCompare className="w-3 h-3" />
            {compareMode ? 'Comparing...' : 'Compare'}
          </button>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className={`flex items-center gap-1 rounded px-1.5 py-0.5 text-[9px] transition-colors ${
              showHistory
                ? 'bg-amber-600 text-white'
                : 'text-gray-500 dark:text-slate-400 hover:bg-gray-200 dark:hover:bg-slate-700'
            }`}
            title="Revision history"
          >
            <History className="w-3 h-3" />
          </button>
        </div>
      </div>

      {compareMode ? (
        <div className="flex-1 flex flex-col">
          <div className={`px-2 py-1 text-[9px] border-b ${isDark ? 'border-slate-700 text-slate-400' : 'border-gray-200 text-gray-500'}`}>
            {!compareBaseId
              ? 'Select a document as the base (left side)'
              : !compareTargetId
                ? `Base: ${baseDoc?.title || compareBaseId} — Select target (right side)`
                : `Comparing: ${baseDoc?.title} vs ${targetDoc?.title}`}
          </div>
          {compareBaseId && compareTargetId && baseDoc && targetDoc ? (
            <div className="flex-1 overflow-hidden">
              <DiffViewer
                originalText={baseDoc.content}
                modifiedText={targetDoc.content}
                originalLabel={baseDoc.title}
                modifiedLabel={targetDoc.title}
              />
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-2">
              <ManuscriptList
                documents={manuscriptDocuments}
                selectedDocumentId={compareTargetId ?? null}
                isLoading={manuscriptQueryLoading}
                includeParagraphs={includeParagraphs}
                onSelect={handleSelect}
                onNavigate={handleOutlineNavigate}
                isDark={isDark}
                highlightBase={compareBaseId}
              />
            </div>
          )}
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-y-auto p-2">
            <ManuscriptList
              documents={manuscriptDocuments}
              selectedDocumentId={selectedDocumentId}
              isLoading={manuscriptQueryLoading}
              includeParagraphs={includeParagraphs}
              onSelect={handleSelect}
              onNavigate={handleOutlineNavigate}
              isDark={isDark}
            />
          </div>

          {scrollTarget && (
            <div className="border-t border-gray-200 dark:border-slate-700 px-4 py-2">
              <p className="text-xs text-gray-500 dark:text-slate-400">
                Navigate to line {scrollTarget.lineIndex} in {scrollTarget.documentId}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
