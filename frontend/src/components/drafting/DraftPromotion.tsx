import { useState, useEffect, useCallback } from 'react';
import type { DraftArtifact, ManuscriptDocument } from '../../types/drafting';
import { getDraftArtifacts } from '../../services/drafting';
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

  const loadArtifacts = useCallback(async () => {
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
  }, [projectId]);

  useEffect(() => {
    void loadArtifacts();
  }, [loadArtifacts]);

  const handlePromoteSuccess = (manuscript: ManuscriptDocument) => {
    setSelectedArtifact(null);
    void manuscript;
    void loadArtifacts();
  };

  return (
    <div className="space-y-4">
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
          <div key={artifact.artifact_id} className="border rounded-lg p-4 bg-white">
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
          projectId={projectId}
          onClose={() => setSelectedArtifact(null)}
          onSuccess={handlePromoteSuccess}
        />
      )}
    </div>
  );
}
