import { useState } from 'react';
import type { CheckerFinding, Severity } from '../../types/review';
import { getFindings } from '../../services/review';
import { FindingCard } from './FindingCard';

interface FindingsListProps {
  projectId: string;
}

const severities: Severity[] = ['low', 'medium', 'high', 'critical'];

export function FindingsList({ projectId }: FindingsListProps) {
  const [findings, setFindings] = useState<CheckerFinding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [severityFilter, setSeverityFilter] = useState<Severity[] | null>(null);
  const [sourceKindFilter, setSourceKindFilter] = useState<string | null>(null);

  const loadFindings = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getFindings({
        project_id: projectId,
        severity: severityFilter || undefined,
        source_object_kind: sourceKindFilter || undefined,
      });
      setFindings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load findings');
      setFindings([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectFinding = () => {
    // Selection handled by parent component
  };

  return (
    <div className="h-full flex flex-col">
      <header className="border-b px-4 py-3 bg-white">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Findings</h2>
          
          <button
            onClick={loadFindings}
            disabled={loading}
            className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Refresh
          </button>
        </div>

        <div className="flex gap-2">
          <select
            value={severityFilter || ''}
            onChange={(e) => setSeverityFilter(e.target.value ? [e.target.value as Severity] : null)}
            className="px-3 py-1.5 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Severities</option>
            {severities.map((sev) => (
              <option key={sev} value={sev}>{sev.charAt(0).toUpperCase() + sev.slice(1)}</option>
            ))}
          </select>

          <select
            value={sourceKindFilter || ''}
            onChange={(e) => setSourceKindFilter(e.target.value || null)}
            className="px-3 py-1.5 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Object Types</option>
            <option value="chapter-plan">Chapter Plan</option>
            <option value="scene-plan">Scene Plan</option>
            <option value="manuscript">Manuscript</option>
            <option value="sequence">Sequence</option>
          </select>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="border rounded-lg p-4 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                <div className="h-6 bg-gray-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="text-center py-8 text-red-600">
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && findings.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No findings for this project</p>
          </div>
        )}

        {!loading && !error && findings.length > 0 && (
          <>
            <p className="text-sm text-gray-500 mb-2">{findings.length} finding(s)</p>
            {findings.map((finding) => (
              <FindingCard 
                key={finding.finding_id} 
                finding={finding}
                projectId={projectId}
                onSelect={handleSelectFinding}
              />
            ))}
          </>
        )}
      </main>
    </div>
  );
}
