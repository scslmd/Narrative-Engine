import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { StudioCommandBar } from '../components/studio/StudioCommandBar';
import { StudioProjectRail } from '../components/studio/StudioProjectRail';
import { WritingView } from './WritingView';
import { useStudioStore } from '../stores/studioStore';
import { useWritingView } from '../hooks/useWritingView';
import { useThemeStore } from '../stores/themeStore';
import { resolveEffectiveMode } from '../theme/theme';

export function StudioView() {
  const { projectId } = useParams<{ projectId: string }>();
  const leftRailMode = useStudioStore((state) => state.leftRailMode);
  const leftRailWidth = useStudioStore((state) => state.leftRailWidth);
  const setLeftRailMode = useStudioStore((state) => state.setLeftRailMode);
  const { mode: themeMode } = useThemeStore();
  const isDark = resolveEffectiveMode(themeMode) === 'dark';

  const {
    manuscriptDocuments,
    selectedDocumentId,
    manuscriptQueryLoading,
    setSelectedDocumentId,
    setIsEditing,
    setEditContent,
  } = useWritingView(isDark);

  const chapterOptions = useMemo(() => manuscriptDocuments.map(doc => ({
    document_id: doc.document_id,
    title: doc.display_title ? `${doc.title} — ${doc.display_title}` : doc.title,
  })), [manuscriptDocuments]);

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

  const railColumn = leftRailMode === 'collapsed' ? '80px' : `${leftRailWidth}px`;
  const leftDrawerOpen = leftRailMode === 'overlay';

  const handleChapterSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedDocumentId(e.target.value);
    setIsEditing(false);
    setEditContent('');
  };

  return (
    <div className="relative flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
      <StudioCommandBar />
      <div
        className="grid min-h-0 flex-1 grid-cols-1 xl:grid-cols-[minmax(0,0)_minmax(0,1fr)]"
        style={{ gridTemplateColumns: `${railColumn} minmax(0,1fr)` }}
      >
        <div className="min-h-0 overflow-hidden hidden xl:block">
          <StudioProjectRail projectId={projectId} compact={leftRailMode === 'collapsed'} />
        </div>
        <main className="min-h-0 overflow-hidden bg-[var(--bg-primary)]">
          <WritingView
            embedded
            chapterSelectOptions={chapterOptions}
            selectedChapterId={selectedDocumentId}
            isLoadingChapterSelect={manuscriptQueryLoading}
            onChapterSelect={handleChapterSelect}
          />
        </main>
      </div>

      {leftDrawerOpen && (
        <div className="absolute left-0 top-0 z-30 h-full w-72 overflow-hidden border-r border-[var(--border-primary)] bg-[var(--bg-primary)] xl:hidden">
          <StudioProjectRail projectId={projectId} />
        </div>
      )}

      {leftDrawerOpen && (
        <button
          type="button"
          aria-label="Close Studio drawer"
          onClick={() => setLeftRailMode('collapsed')}
          className="absolute inset-0 z-20 bg-black/20 xl:hidden"
        />
      )}
    </div>
  );
}
