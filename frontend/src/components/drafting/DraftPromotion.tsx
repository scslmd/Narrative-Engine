import { useState, useEffect } from 'react';
import type { DraftArtifact, PromotedManuscript } from '../../types/drafting';
import { getDraftArtifacts, isMockMode } from '../../services/drafting';
import DraftPreview from './DraftPreview';
import PromotionModal from './PromotionModal';

interface DraftPromotionProps {
  projectId: string;
}

export default function DraftPromotion({ projectId }: DraftPromotionProps) {
  const [artifacts, setArtifacts] = useState<DraftArtifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<DraftArtifact | null>(null);

  useEffect(() => {
    loadArtifacts();
  }, [projectId]);

  const loadArtifacts = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getDraftArtifacts(projectId);
      setArtifacts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load draft artifacts');
    } finally {
      setLoading(false);
    }
  };

  const handlePromoteSuccess = (manuscript: PromotedManuscript) => {
    console.log('Draft promoted:', manuscript.document_id);
  };

  if (!isMockMode()) {
    return (
      <div className="p-4 border rounded-lg bg-gray-50">
        <h3 className="font-semibold text-gray-900 mb-2">Draft Promotion</h3>
        <p className="text-sm text-gray-600">
          Backend endpoint not yet available. Set VITE_USE_MOCKS=true to enable mock mode.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {isMockMode() && (
        <div className="bg-yellow-100 border border-yellow-300 px-4 py-2 text-sm text-yellow-800 rounded">
          Mock mode enabled - promotion will simulate backend behavior
        </div>
      )}

      <h3 className="font-semibold text-gray-900">Draft Artifacts</h3>

      {loading && (
        <div className="flex items-center justify-center p-8">
          <svg className="animate-spin h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {!loading && !error && artifacts.length === 0 && (
        <div className="text-center p-8 text-gray-500">
          No draft artifacts found for this project.
        </div>
      )}

      <div className="space-y-4">
        {artifacts.map((artifact) => (
          <div key={artifact.id} className="border rounded-lg p-4 bg-white">
            <DraftPreview artifact={artifact} />
            
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setSelectedArtifact(artifact)}
                className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors"
              >
                Promote to Manuscript
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedArtifact && (
        <PromotionModal
          artifact={selectedArtifact}
          onClose={() => setSelectedArtifact(null)}
          onSuccess={handlePromoteSuccess}
        />
      )}
    </div>
  );
}
