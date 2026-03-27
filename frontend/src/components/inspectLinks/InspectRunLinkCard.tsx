import type { InspectRunLink } from '../../types/inspectLinks';

interface InspectRunLinkCardProps {
  link: InspectRunLink;
  onViewRunDetails?: (link: InspectRunLink) => void;
}

export function InspectRunLinkCard({ link, onViewRunDetails }: InspectRunLinkCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
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
          <span className="font-medium text-gray-700">Finding ID:</span>
          <span className="ml-2 text-gray-600">{link.finding_id.substring(0, 8)}...</span>
        </div>

        <div className="text-xs text-gray-500">
          Created: {formatDate(link.created_at)}
        </div>
      </div>

      <button
        onClick={() => onViewRunDetails?.(link)}
        className="mt-3 w-full px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
      >
        View Run Details
      </button>
    </div>
  );
}
