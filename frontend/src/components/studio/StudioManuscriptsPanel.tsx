import { useCallback, useState } from 'react';
import { ManuscriptList } from '../writing/ManuscriptList';
import { useWritingView } from '../../hooks/useWritingView';
import { useSettingsStore } from '../../stores/settingsStore';
import { useThemeStore } from '../../stores/themeStore';
import { resolveEffectiveMode } from '../../theme/theme';

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
  } = useWritingView(isDark);

  const [scrollTarget, setScrollTarget] = useState<{ documentId: string; lineIndex: number } | null>(null);

  const handleOutlineNavigate = useCallback((documentId: string, lineIndex: number) => {
    setScrollTarget({ documentId, lineIndex });
  }, []);

  const handleSelect = (id: string) => {
    setSelectedDocumentId(id);
    setIsEditing(false);
    setEditContent('');
    onSelect?.(id);
  };

  const includeParagraphs = outlineDetail === 'detailed';

  return (
   <div className="flex h-full flex-col">
       <div className="flex items-center justify-end px-2.5 py-1 border-b border-gray-200 dark:border-slate-700">
         <span className="text-[9px] text-gray-500 dark:text-slate-400">
           {manuscriptDocuments.length} documents
         </span>
       </div>

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
    </div>
  );
}
