import { useState } from 'react';
import type { DraftArtifact, PromotedManuscript } from '../../types/drafting';
import { promoteDraft, isMockMode } from '../../services/drafting';
import { toast } from '../../lib/toast';

interface PromotionModalProps {
  artifact: DraftArtifact;
  onClose: () => void;
  onSuccess?: (manuscript: PromotedManuscript) => void;
}

export default function PromotionModal({ artifact, onClose, onSuccess }: PromotionModalProps) {
  const [isPromoting, setIsPromoting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePromote = async () => {
    setIsPromoting(true);
    setError(null);

    try {
      const result = await promoteDraft(artifact.id);
      
      if (isMockMode()) {
        toast.success(`Draft promoted to ${result.title} (mock mode)`);
      } else {
        toast.success('Draft promoted successfully');
      }

      onSuccess?.(result);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to promote draft');
      toast.error('Failed to promote draft');
    } finally {
      setIsPromoting(false);
    }
  };

  const previewContent = artifact.content.substring(0, 500);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {isMockMode() && (
          <div className="bg-yellow-100 border-b border-yellow-300 px-4 py-2 text-sm text-yellow-800">
            Promotion in mock mode - backend endpoint not yet available
          </div>
        )}

        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">Promote Draft to Manuscript</h2>

          <div className="mb-4">
            <h3 className="font-medium text-gray-900">{artifact.title}</h3>
            <p className="text-sm text-gray-500 mt-1">
              This will create a new manuscript document from this draft artifact.
            </p>
          </div>

          <div className="bg-gray-50 rounded p-4 mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Preview (first 500 characters)</h4>
            <p className="text-sm text-gray-600 whitespace-pre-wrap">{previewContent}</p>
          </div>

          <div className="bg-blue-50 rounded p-4 mb-4">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Provenance Information</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-gray-600">Artifact ID:</span>
              <span className="font-mono text-gray-900">{artifact.id}</span>
              
              <span className="text-gray-600">Provider:</span>
              <span className="text-gray-900">{artifact.provider}</span>
              
              <span className="text-gray-600">Model:</span>
              <span className="text-gray-900">{artifact.model}</span>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              disabled={isPromoting}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded transition-colors disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              onClick={handlePromote}
              disabled={isPromoting}
              className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isPromoting ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Promoting...
                </>
              ) : (
                'Promote to Manuscript'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
