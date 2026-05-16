import { useParams } from 'react-router-dom';
import { StudioCommandBar } from '../components/studio/StudioCommandBar';
import { StudioContextPanel } from '../components/studio/StudioContextPanel';
import { StudioProjectRail } from '../components/studio/StudioProjectRail';
import { WritingView } from './WritingView';
import { useStudioStore } from '../stores/studioStore';

export function StudioView() {
  const { projectId } = useParams<{ projectId: string }>();
  const leftRailOpen = useStudioStore((state) => state.leftRailOpen);
  const contextPanelOpen = useStudioStore((state) => state.contextPanelOpen);

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
      <StudioCommandBar />
      <div
        className="grid min-h-0 flex-1"
        style={{ gridTemplateColumns: `${leftRailOpen ? '13rem' : '0rem'} minmax(0,1fr) ${contextPanelOpen ? '26rem' : '0rem'}` }}
      >
        <div className="min-h-0 overflow-hidden">
          {leftRailOpen ? <StudioProjectRail projectId={projectId} /> : null}
        </div>
        <main className="min-h-0 overflow-hidden bg-[var(--bg-primary)]">
          <WritingView />
        </main>
        <div className="min-h-0 overflow-hidden border-l border-[var(--border-primary)]">
          {contextPanelOpen ? <StudioContextPanel projectId={projectId} /> : null}
        </div>
      </div>
    </div>
  );
}
