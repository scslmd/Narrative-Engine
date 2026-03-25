import type { DraftArtifact } from '../../types/drafting';

interface DraftPreviewProps {
  artifact: DraftArtifact;
}

export default function DraftPreview({ artifact }: DraftPreviewProps) {
  const getStateColor = () => {
    switch (artifact.state) {
      case 'DRAFT':
        return 'bg-gray-100 text-gray-700';
      case 'REVIEW':
        return 'bg-yellow-100 text-yellow-700';
      case 'APPROVED':
        return 'bg-green-100 text-green-700';
    }
  };

  const previewContent = artifact.content.substring(0, 500);

  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">{artifact.title}</h3>
        <span className={`px-2 py-1 text-xs font-medium rounded ${getStateColor()}`}>
          {artifact.state}
        </span>
      </div>

      <div className="flex gap-2 mb-3">
        <span className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded">
          Provider: {artifact.provider}
        </span>
        <span className="px-2 py-1 text-xs bg-purple-50 text-purple-700 rounded">
          Model: {artifact.model}
        </span>
      </div>

      <div className="bg-gray-50 rounded p-3 mb-3">
        <p className="text-sm text-gray-600 line-clamp-4">{previewContent}</p>
        {artifact.content.length > 500 && (
          <p className="text-xs text-gray-400 mt-1">...more content available</p>
        )}
      </div>

      <div className="text-xs text-gray-500">
        Created: {new Date(artifact.created_at).toLocaleString()}
      </div>
    </div>
  );
}
