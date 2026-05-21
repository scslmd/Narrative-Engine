import { useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { StudioProjectRail } from '../components/studio/StudioProjectRail';
import { StudioContextPanel } from '../components/studio/StudioContextPanel';
import { StudioRadialHub } from '../components/studio/StudioRadialHub';
import { StudioCommandBar } from '../components/studio/StudioCommandBar';
import { StudioStatusBar } from '../components/studio/StudioStatusBar';
import { WritingView } from './WritingView';
import { ViewShell } from '../components/shell/ViewShell';
import { useStudioStore } from '../stores/studioStore';
import { useUIStore } from '../stores/uiStore';
import { useWritingView } from '../hooks/useWritingView';
import { usePanelUrlSync } from '../hooks/usePanelUrlSync';

export function StudioView() {
  const { projectId } = useParams<{ projectId: string }>();
  const leftRailMode = useStudioStore((state) => state.leftRailMode);
  const panelVisible = useStudioStore((state) => state.panelVisible);
  const setPanelVisible = useStudioStore((state) => state.setPanelVisible);
  const resetLayout = useStudioStore((state) => state.resetLayout);
  const loadLayout = useStudioStore((state) => state.loadLayout);

  const {
    manuscriptDocuments,
    selectedDocumentId,
    manuscriptQueryLoading,
    setSelectedDocumentId,
    setIsEditing,
    setEditContent,
  } = useWritingView(false);

  const setJobId = useUIStore((s) => s.setJobId);

  // Load layout synchronously before effects run, so usePanelUrlSync sees saved panels
  useEffect(() => {
    if (projectId) loadLayout(projectId);
  }, [projectId, loadLayout]);

  // Sync active panel with URL query params; handle deep-link params on mount
  usePanelUrlSync({
    projectId: projectId ?? null,
    onJobId: (jobId) => {
      if (jobId) setJobId(jobId);
    },
  });

  const chapterOptions = useMemo(() => manuscriptDocuments.map(doc => ({
    document_id: doc.document_id,
    title: doc.display_title ? `${doc.title} — ${doc.display_title}` : doc.title,
  })), [manuscriptDocuments]);

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

  const handleChapterSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedDocumentId(e.target.value);
    setIsEditing(false);
    setEditContent('');
  };

  const handleManuscriptSelect = (documentId: string) => {
    setSelectedDocumentId(documentId);
    setIsEditing(false);
    setEditContent('');
  };

  const handleTogglePanel = () => setPanelVisible(!panelVisible);

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
      <StudioCommandBar
        projectId={projectId}
        projectName="Studio Desk"
        railCollapsed={leftRailMode === 'collapsed'}
        panelVisible={panelVisible}
        onToggleRail={() => useStudioStore.getState().toggleLeftRail()}
        onTogglePanel={handleTogglePanel}
        onResetLayout={resetLayout}
      />
      <div className="relative flex-1 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <ViewShell
            title=""
            subtitle=""
            leftRailContent={
              <StudioProjectRail projectId={projectId} compact={leftRailMode === 'collapsed'} />
            }
            rightPanelContent={
              <StudioContextPanel
                projectId={projectId}
                showCloseButton={false}
                onManuscriptSelect={handleManuscriptSelect}
              />
            }
            showRightPanel={panelVisible}
            onToggleRightPanel={handleTogglePanel}
          >
            <WritingView
              embedded
              chapterSelectOptions={chapterOptions}
              selectedChapterId={selectedDocumentId}
              isLoadingChapterSelect={manuscriptQueryLoading}
              onChapterSelect={handleChapterSelect}
            />
          </ViewShell>
        </div>
        <div className="absolute inset-0 z-10">
          <StudioRadialHub projectId={projectId} />
        </div>
      </div>
      <StudioStatusBar projectId={projectId} />
    </div>
  );
}
