import { useNavigate } from 'react-router-dom';
import type { InspectRunLink } from '../../types/inspectLinks';
import { useUIStore } from '../../stores/uiStore';

interface InspectRunLinkCardProps {
  link: InspectRunLink;
}

export function InspectRunLinkCard({ link }: InspectRunLinkCardProps) {
  const navigate = useNavigate();
  const { projectId } = useUIStore();

  const handleViewRunDetails = () => {
    if (projectId && link.run_id) {
      // Navigate to inspect view with the job/run ID
      navigate(`/workspace/${projectId}/inspect/${link.run_id}`);
    }
  };

  const getRunKindColor = (kind: string) => {
    switch (kind.toLowerCase()) {
      case 'architect':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'sequencer':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'drafter':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'compiler':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="border rounded-lg p-4 bg-white hover:border-blue-300">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h4 className="font-semibold text-gray-900">{link.run_kind}</h4>
          <p className="text-sm text-gray-500">Run ID: {link.run_id.substring(0, 8)}...</p>
        </div>
        <span className={`px-2 py-1 rounded text-xs font-medium border ${getRunKindColor(link.run_kind)}`}>
          {link.run_kind}
        </span>
      </div>

      <div className="space-y-2 mt-3">
        <div className="text-sm">
          <span className="font-medium text-gray-700">Object:</span>
          <span className="ml-2 text-gray-600">{link.object_kind}: {link.object_id.substring(0, 12)}...</span>
        </div>

        {link.label && (
          <div className="text-sm">
            <span className="font-medium text-gray-700">Label:</span>
            <span className="ml-2 text-gray-600">{link.label}</span>
          </div>
        )}

        {link.attempt_number !== null && (
          <div className="text-xs text-gray-500">
            Attempt: #{link.attempt_number}
          </div>
        )}
      </div>

      <button
        onClick={handleViewRunDetails}
        className="mt-3 w-full px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
      >
        View Run Details
      </button>
    </div>
  );
}
