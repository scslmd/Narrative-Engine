import { useState, useCallback } from 'react';
import type { Severity } from '../../types/review';
import { getFindings } from '../../services/review';
import { FindingCard } from './FindingCard';
import { useApiQuery } from '../../hooks/useApiQuery';
import { LoadingState } from '../ui/LoadingState';
import { EmptyState } from '../ui/EmptyState';
import { ErrorBanner } from '../ui/ErrorBanner';

interface FindingsListProps {
  projectId: string;
}

const severities: Severity[] = ['low', 'medium', 'high', 'critical'];

export function FindingsList({ projectId }: FindingsListProps) {
  const [severityFilter, setSeverityFilter] = useState<Severity[] | null>(null);
  const [sourceKindFilter, setSourceKindFilter] = useState<string | null>(null);

  const findingsQuery = useApiQuery({
    queryKey: ['review', 'findings', projectId, JSON.stringify(severityFilter), sourceKindFilter || ''],
    serviceFn: () =>
      getFindings({
        project_id: projectId,
        severity: severityFilter || undefined,
        source_object_kind: sourceKindFilter || undefined,
      }),
    onErrorToast: false,
  });

  const handleSelectFinding = useCallback(() => {
    // Selection handled by parent component
  }, []);

  return (
    <div className="h-full flex flex-col">
      <header className="border-b px-4 py-3 bg-white">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Findings</h2>

          <button
            onClick={() => void findingsQuery.refetch()}
            disabled={findingsQuery.isLoading}
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

      <ErrorBanner error={findingsQuery.error} onRetry={() => void findingsQuery.retry()} />

      <main className="flex-1 overflow-y-auto p-4 space-y-3">
        <LoadingState isLoading={findingsQuery.isLoading}>
          {findingsQuery.data && findingsQuery.data.length === 0 ? (
            <EmptyState
              title="No review findings yet"
              description="Findings are generated when checker/inspect jobs run on project artifacts such as chapter plans, scene plans, and manuscripts."
            />
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-2">{findingsQuery.data?.length || 0} finding(s)</p>
              {(findingsQuery.data || []).map((finding) => (
                <FindingCard
                  key={finding.finding_id}
                  finding={finding}
                  projectId={projectId}
                  onSelect={handleSelectFinding}
                />
              ))}
            </>
          )}
        </LoadingState>
      </main>
    </div>
  );
}
