import { useParams } from 'react-router-dom';
import { ViewShell } from '../components/shell/ViewShell';
import InspectMode from '../components/inspect/InspectMode';

export function InspectView() {
  const { projectId } = useParams<{ projectId: string; jobId?: string }>();

  if (!projectId) {
    return <div className="text-[var(--text-secondary)]">No project selected</div>;
  }

  return (
    <ViewShell title="Inspect" subtitle={projectId}>
      <InspectMode />
    </ViewShell>
  );
}
