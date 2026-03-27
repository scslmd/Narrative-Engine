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
        <div className="flex h-full gap-4">
          <div className="w-80 flex-shrink-0 overflow-hidden">
            <Outlet />
          </div>
          <div className="flex-1 flex gap-4 overflow-hidden">
            <div className="w-80 flex-shrink-0 h-full overflow-hidden">
              <NotesPanel projectId={projectId} />
            </div>
            <div className="flex-1 h-full overflow-hidden">
              <JobLaunchPanel projectId={projectId} />
            </div>
          </div>
        </div>
      </WorkspaceShell>
      <BottomUtilityLayer projectId={projectId} />
    </>
  );
}
