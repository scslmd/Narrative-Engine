import { useEffect } from 'react';
import { useLocation, useParams, Outlet } from 'react-router-dom';
import { WorkspaceShell } from '../components/WorkspaceShell';
import { NotesPanel } from '../components/NotesPanel';
import { JobLaunchPanel } from '../components/JobLaunchPanel';
import { BottomUtilityLayer } from '../components/BottomUtilityLayer';
import { useThemeStore } from '../stores/themeStore';
import { useUIStore } from '../stores/uiStore';
import type { WorkspaceMode } from '../routes';

export function Workspace() {
  const { projectId, chapterId, jobId } = useParams<{ projectId: string; chapterId?: string; jobId?: string }>();
  const location = useLocation();
  const { setMode, setProjectId, setChapterId, setJobId } = useUIStore();
  const { setStage } = useThemeStore();

  useEffect(() => {
    if (!projectId) {
      return;
    }

    const nextMode = (location.pathname.split('/')[3] ?? 'plan') as WorkspaceMode;
    const stageMap = {
      plan: 'planning',
      write: 'writing',
      review: 'review',
      inspect: 'inspect',
    } as const;

    setMode(nextMode);
    setProjectId(projectId);
    setChapterId(chapterId ?? null);
    setJobId(jobId ?? null);
    setStage(stageMap[nextMode] ?? 'planning');
  }, [chapterId, jobId, location.pathname, projectId, setChapterId, setJobId, setMode, setProjectId, setStage]);

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
