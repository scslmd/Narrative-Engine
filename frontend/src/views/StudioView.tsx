import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { StudioProjectRail } from '../components/studio/StudioProjectRail';
import { StudioContextPanel } from '../components/studio/StudioContextPanel';
import { WritingView } from './WritingView';
import { ViewShell } from '../components/shell/ViewShell';
import { useStudioStore } from '../stores/studioStore';
import { useWritingView } from '../hooks/useWritingView';

export function StudioView() {
  const { projectId } = useParams<{ projectId: string }>();
  const leftRailMode = useStudioStore((state) => state.leftRailMode);
  const panelVisible = useStudioStore((state) => state.panelVisible);
  const setPanelVisible = useStudioStore((state) => state.setPanelVisible);

  const {
    manuscriptDocuments,
    selectedDocumentId,
    manuscriptQueryLoading,
    setSelectedDocumentId,
    setIsEditing,
    setEditContent,
  } = useWritingView(false);

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
    <ViewShell
      title="Studio Desk"
      subtitle={projectId}
      leftRailContent={
        <StudioProjectRail projectId={projectId} compact={leftRailMode === 'collapsed'} />
      }
      rightPanelContent={
        <StudioContextPanel
          projectId={projectId}
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
  );
}
