import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { StudioCommandBar } from '../components/studio/StudioCommandBar';
import { StudioContextPanel } from '../components/studio/StudioContextPanel';
import { StudioProjectRail } from '../components/studio/StudioProjectRail';
import { WritingView } from './WritingView';
import { useStudioStore } from '../stores/studioStore';
import { useWritingView } from '../hooks/useWritingView';
import { useThemeStore } from '../stores/themeStore';
import { resolveEffectiveMode } from '../theme/theme';

export function StudioView() {
  const { projectId } = useParams<{ projectId: string }>();
  const leftRailMode = useStudioStore((state) => state.leftRailMode);
  const contextPanelMode = useStudioStore((state) => state.contextPanelMode);
  const leftRailWidth = useStudioStore((state) => state.leftRailWidth);
  const contextPanelWidth = useStudioStore((state) => state.contextPanelWidth);
  const setLeftRailMode = useStudioStore((state) => state.setLeftRailMode);
  const setContextPanelMode = useStudioStore((state) => state.setContextPanelMode);
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

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

  const railColumn = leftRailMode === 'collapsed' ? '80px' : `${leftRailWidth}px`;
  const contextColumn = `${contextPanelWidth}px`;

  const leftDrawerOpen = leftRailMode === 'overlay';
  const contextDrawerOpen = contextPanelMode === 'overlay';
  const drawerOpen = leftDrawerOpen || contextDrawerOpen;

  const handleChapterSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedDocumentId(e.target.value);
    setIsEditing(false);
    setEditContent('');
  };

  const chapterOptions = useMemo(() => manuscriptDocuments.map(doc => ({
    document_id: doc.document_id,
    title: doc.display_title ? `${doc.title} — ${doc.display_title}` : doc.title,
  })), [manuscriptDocuments]);

  return (
    <div className="relative flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
      <StudioCommandBar />
      <div
        className="grid min-h-0 flex-1 grid-cols-1 xl:grid-cols-[minmax(0,0)_minmax(0,1fr)_minmax(0,0)]"
        style={{ gridTemplateColumns: `${railColumn} minmax(0,1fr) ${contextColumn}` }}
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
        <div className="min-h-0 overflow-hidden border-l border-[var(--border-primary)] hidden xl:block">
          <StudioContextPanel projectId={projectId} />
        </div>
      </div>

      {leftDrawerOpen && (
        <div className="absolute left-0 top-0 z-30 h-full w-72 overflow-hidden border-r border-[var(--border-primary)] bg-[var(--bg-primary)] xl:hidden">
          <StudioProjectRail projectId={projectId} />
        </div>
      )}

      {contextDrawerOpen && (
        <div className="absolute right-0 top-0 z-30 h-full w-[min(28rem,100%)] overflow-hidden border-l border-[var(--border-primary)] bg-[var(--bg-primary)] xl:hidden">
          <StudioContextPanel projectId={projectId} showCloseButton />
        </div>
      )}

      {drawerOpen && (
        <button
          type="button"
          aria-label="Close Studio drawers"
          onClick={() => {
            setLeftRailMode('collapsed');
            setContextPanelMode('closed');
          }}
          className="absolute inset-0 z-20 bg-black/20 xl:hidden"
        />
      )}
    </div>
  );
}
