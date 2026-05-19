import { useParams, Outlet } from 'react-router-dom';
import { WorkspaceShell } from '../components/WorkspaceShell';
import { BottomUtilityLayer } from '../components/BottomUtilityLayer';

export function Workspace() {
  const { projectId } = useParams<{ projectId: string }>();

  if (!projectId) {
    return <div className="text-center py-8 text-gray-500">No project selected</div>;
  }

  return (
    <>
      <WorkspaceShell>
        <section className="min-h-0 h-full overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
          <Outlet />
        </section>
      </WorkspaceShell>
      <BottomUtilityLayer projectId={projectId} />
    </>
  );
}
