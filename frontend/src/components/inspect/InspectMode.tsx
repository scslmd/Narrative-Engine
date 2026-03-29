import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useUIStore } from '../../stores/uiStore';
import InspectTabs from './InspectTabs';

export default function InspectMode() {
  const { jobId: routeJobId } = useParams<{ jobId?: string }>();
  const navigate = useNavigate();
  const { inspectContext, setInspectContext, projectId } = useUIStore();
  
  useEffect(() => {
    if (routeJobId && (!inspectContext || inspectContext.jobId !== routeJobId)) {
      const runKind: 'pipeline_job' | 'role_model_check' = 
        inspectContext?.jobId === routeJobId ? inspectContext.runKind : 'pipeline_job';
      const attemptNumber = inspectContext?.jobId === routeJobId ? inspectContext.attemptNumber : undefined;
      
      setInspectContext({ 
        jobId: routeJobId, 
        runKind,
        attemptNumber 
      });
    }
  }, [routeJobId, inspectContext, setInspectContext]);

  const handleBackToManuscript = () => {
    if (projectId) {
      navigate(`/workspace/${projectId}/write`, { replace: true });
    } else {
      navigate('/');
    }
  };

  if (!inspectContext?.jobId) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-gray-500">Select a job to inspect</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      <header className="border-b px-4 py-3 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Inspect Run</h2>
            <p className="text-sm text-gray-500">Run ID: {inspectContext.jobId}</p>
            <p className="text-sm text-gray-500">Run Kind: {inspectContext.runKind}</p>
          </div>

          <button
            onClick={handleBackToManuscript}
            className="px-4 py-2 bg-white border rounded hover:bg-gray-50 text-sm"
          >
            Back to Manuscript
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-hidden">
        <InspectTabs context={inspectContext} />
      </main>
    </div>
  );
}
