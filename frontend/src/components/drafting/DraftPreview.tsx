import type { DraftArtifact } from '../../types/drafting';

interface DraftPreviewProps {
  artifact: DraftArtifact;
}

export default function DraftPreview({ artifact }: DraftPreviewProps) {
  const getStatusColor = () => {
    switch (artifact.status) {
      case 'DRAFT':
        return 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300';
      case 'PROPOSED':
        return 'bg-blue-100 text-blue-700';
      case 'CANONICAL':
        return 'bg-green-100 text-green-700';
      case 'SUPERSEDED':
        return 'bg-yellow-100 text-yellow-700';
      case 'REJECTED':
        return 'bg-red-100 text-red-700';
      case 'ARCHIVED':
        return 'bg-gray-200 dark:bg-slate-600 text-gray-500 dark:text-slate-400';
      default:
        return 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300';
    }
  };

  const previewContent = artifact.content.substring(0, 500);

  return (
    <div className="border rounded-lg p-4 bg-white dark:bg-slate-800">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900 dark:text-slate-100">{artifact.title}</h3>
        <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor()}`}>
          {artifact.status}
        </span>
      </div>

      <div className="flex gap-2 mb-3 flex-wrap">
        {artifact.source_plan_ids.length > 0 && (
          <span className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded">
            Plans: {artifact.source_plan_ids.length}
          </span>
        )}
        {artifact.provenance_note && (
          <span className="px-2 py-1 text-xs bg-purple-50 text-purple-700 rounded">
            Note available
          </span>
        )}
      </div>

      <div className="bg-gray-50 dark:bg-slate-700 rounded p-3 mb-3">
        <p className="text-sm text-gray-600 dark:text-slate-400 line-clamp-4">{previewContent}</p>
        {artifact.content.length > 500 && (
          <p className="text-xs text-gray-400 dark:text-slate-500 mt-1">...more content available</p>
        )}
      </div>

      <div className="text-xs text-gray-500 dark:text-slate-400 font-mono">
        ID: {artifact.artifact_id}
      </div>
    </div>
  );
}
