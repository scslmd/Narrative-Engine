import { useJobLineage } from '../../hooks/useJobLineage';
import ArtifactCard from './ArtifactCard';
import type { InspectContext } from '../../types/inspect';

interface ArtifactLineageProps {
  context: InspectContext;
}

export default function ArtifactLineage({ context }: ArtifactLineageProps) {
  const { jobId, runKind, attemptNumber } = context;
  const { artifacts, loading, error, refetch } = useJobLineage(jobId, runKind, attemptNumber);

  if (loading) {
    return (
      <div className="space-y-3 p-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-lg p-4 border animate-pulse">
            <div className="h-5 bg-gray-200 rounded w-3/4 mb-3"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-3">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
        <button 
          onClick={refetch}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (artifacts.length === 0) {
    return (
      <div className="p-4 text-center">
        <p className="text-sm text-gray-500">No artifacts generated yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-4">
      {artifacts.map((artifact) => (
        <ArtifactCard key={artifact.artifact_id} artifact={artifact} />
      ))}
    </div>
  );
}
