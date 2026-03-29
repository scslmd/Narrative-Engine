import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCheckerStatus } from '../../services/checker';
import { jobsService } from '../../services/jobs';
import { useUIStore } from '../../stores/uiStore';
import InspectTabs from './InspectTabs';

export default function InspectMode() {
  const { jobId: routeJobId } = useParams<{ jobId?: string }>();
  const navigate = useNavigate();
  const { inspectContext, setInspectContext, projectId } = useUIStore();
  const [isResolvingContext, setIsResolvingContext] = useState(false);
  const [resolutionError, setResolutionError] = useState<string | null>(null);

  useEffect(() => {
    if (!routeJobId) {
      setResolutionError(null);
      setIsResolvingContext(false);
      return;
    }

    if (inspectContext?.jobId === routeJobId) {
      setResolutionError(null);
      setIsResolvingContext(false);
      return;
    }

    let cancelled = false;

    const resolveContext = async () => {
      setIsResolvingContext(true);
      setResolutionError(null);

      const checkerStatus = await getCheckerStatus(routeJobId)
        .then((status) => ({ ok: true as const, status }))
        .catch(() => ({ ok: false as const }));

      if (cancelled) {
        return;
      }

      if (checkerStatus.ok) {
        setInspectContext({
          jobId: routeJobId,
          runKind: 'role_model_check',
          attemptNumber: checkerStatus.status.attempt_number,
        });
        setIsResolvingContext(false);
        return;
      }

      const jobStatus = await jobsService.getStatus(routeJobId)
        .then((status) => ({ ok: true as const, status }))
        .catch(() => ({ ok: false as const }));

      if (cancelled) {
        return;
      }

      if (jobStatus.ok) {
        setInspectContext({
          jobId: routeJobId,
          runKind: 'pipeline_job',
          attemptNumber: jobStatus.status.attempt_number,
        });
        setIsResolvingContext(false);
        return;
      }

      setResolutionError('Could not resolve an inspectable run for this route.');
      setIsResolvingContext(false);
    };

    void resolveContext();

    return () => {
      cancelled = true;
    };
  }, [routeJobId, inspectContext, setInspectContext]);

  const handleBackToManuscript = () => {
    if (projectId) {
      navigate(`/workspace/${projectId}/write`, { replace: true });
    } else {
      navigate('/');
    }
  };

  if (isResolvingContext) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-gray-500">Resolving inspect run...</p>
      </div>
    );
  }

  if (resolutionError) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-red-600">{resolutionError}</p>
      </div>
    );
  }

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
