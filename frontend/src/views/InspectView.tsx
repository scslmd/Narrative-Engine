import { useParams } from 'react-router-dom';
import InspectMode from '../components/inspect/InspectMode';

export function InspectView() {
  const { projectId } = useParams<{ projectId: string; jobId?: string }>();

  if (!projectId) {
    return <div className="text-gray-500">No project selected</div>;
  }

  return (
    <div className="h-full">
      <InspectMode />
    </div>
  );
}
