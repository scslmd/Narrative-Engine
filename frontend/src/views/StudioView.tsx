import { useParams } from 'react-router-dom';
import { ChevronDown, FileText } from 'lucide-react';
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
        <main className="min-h-0 overflow-hidden bg-[var(--bg-primary)] flex flex-col">
          <div className={`flex items-center gap-2 px-4 py-2 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
            <FileText className={`w-3.5 h-3.5 ${isDark ? 'text-blue-400' : 'text-blue-500'}`} />
            <h3 className={`text-[10px] font-semibold uppercase tracking-wider ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Chapters</h3>
            <ChevronDown className={`w-3 h-3 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
            <select
              value={selectedDocumentId || ''}
              onChange={handleChapterSelect}
              disabled={manuscriptQueryLoading || manuscriptDocuments.length === 0}
              className={`text-xs rounded-md border px-2 py-1 outline-none focus:ring-1 focus:ring-blue-500 ${isDark ? 'bg-slate-800 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
            >
              {manuscriptDocuments.map((doc) => (
                <option key={doc.document_id} value={doc.document_id}>
                  {doc.title}
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-h-0 overflow-hidden">
            <WritingView embedded />
          </div>
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
