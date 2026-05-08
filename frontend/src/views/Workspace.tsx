import { useParams, Outlet } from 'react-router-dom';
import { WorkspaceShell } from '../components/WorkspaceShell';
import { NotesPanel } from '../components/NotesPanel';
import { JobLaunchPanel } from '../components/JobLaunchPanel';
import { BottomUtilityLayer } from '../components/BottomUtilityLayer';

export function Workspace() {
  const { projectId } = useParams<{ projectId: string }>();

  if (!projectId) {
    return <div className="text-center py-8 text-gray-500">No project selected</div>;
  }

  return (
    <>
      <WorkspaceShell>
        <div className="grid h-full grid-cols-1 xl:grid-cols-[minmax(0,1fr)_20rem] gap-4">
          <section className="min-h-0 h-full overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
            <Outlet />
          </section>
          <aside className="min-h-0 h-full overflow-hidden flex flex-col gap-4">
            <div className="min-h-0 flex-1 overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
              <NotesPanel projectId={projectId} />
            </div>
            <div className="min-h-0 flex-1 overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
              <JobLaunchPanel projectId={projectId} />
            </div>
          </aside>
        </div>
      </WorkspaceShell>
      <BottomUtilityLayer projectId={projectId} />
    </>
  );
}
