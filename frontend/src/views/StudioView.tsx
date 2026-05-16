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
  const closeDrawers = useStudioStore((state) => state.closeDrawers);

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

  const drawerOpen = leftRailOpen || contextPanelOpen;

  return (
    <div className="relative flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
      <StudioCommandBar />
      <div
        className="grid min-h-0 flex- grid-cols-1 xl:grid-cols-[13rem_minmax(0,1fr)_26rem]"
        style={{ gridTemplateColumns: leftRailOpen ? '13rem minmax(0,1fr) 26rem' : '0rem minmax(0,1fr) 0rem' }}
      >
        <div className="min-h-0 overflow-hidden hidden xl:block">
          {leftRailOpen ? <StudioProjectRail projectId={projectId} /> : null}
        </div>
        <main className="min-h-0 overflow-hidden bg-[var(--bg-primary)]">
          <WritingView />
        </main>
        <div className="min-h-0 overflow-hidden border-l border-[var(--border-primary)] hidden xl:block">
          {contextPanelOpen ? <StudioContextPanel projectId={projectId} /> : null}
        </div>
      </div>

      {leftRailOpen && (
        <div className="absolute left-0 top-0 z-30 h-full w-72 overflow-hidden border-r border-[var(--border-primary)] bg-[var(--bg-primary)] xl:hidden">
          <StudioProjectRail projectId={projectId} />
        </div>
      )}

      {contextPanelOpen && (
        <div className="absolute right-0 top-0 z-30 h-full w-[min(28rem,100%)] overflow-hidden border-l border-[var(--border-primary)] bg-[var(--bg-primary)] xl:hidden">
          <StudioContextPanel projectId={projectId} />
        </div>
      )}

      {drawerOpen && (
        <button
          type="button"
          aria-label="Close Studio drawers"
          onClick={closeDrawers}
          className="absolute inset-0 z-20 bg-black/20 xl:hidden"
        />
      )}
    </div>
  );
}
