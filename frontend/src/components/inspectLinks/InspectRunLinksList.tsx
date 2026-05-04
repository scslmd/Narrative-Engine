import { useState } from 'react';
import type { InspectRunLink } from '../../types/inspectLinks';
import { getInspectLinks } from '../../services/inspectLinks';
import { InspectRunLinkCard } from './InspectRunLinkCard';
import { useApiQuery } from '../../hooks/useApiQuery';
import { LoadingState } from '../ui/LoadingState';
import { EmptyState } from '../ui/EmptyState';
import { ErrorBanner } from '../ui/ErrorBanner';

interface InspectRunLinksListProps {
  projectId?: string;
}

export function InspectRunLinksList({ projectId }: InspectRunLinksListProps) {
  const [filterByObjectKind, setFilterByObjectKind] = useState<string>('');
  const [filterByObjectId, setFilterByObjectId] = useState<string>('');
  const [filterByRunId, setFilterByRunId] = useState<string>('');
  const [filterByKind, setFilterByKind] = useState<string>('');

  const linksQuery = useApiQuery<InspectRunLink[]>({
    queryKey: ['inspect-links', projectId || '', filterByObjectKind, filterByObjectId, filterByRunId],
    serviceFn: () =>
      getInspectLinks(
        projectId,
        filterByObjectKind || undefined,
        filterByObjectId || undefined,
        filterByRunId || undefined,
      ),
    onErrorToast: false,
  });

  const filteredLinks = (linksQuery.data || []).filter(link => {
    if (filterByKind && link.run_kind.toLowerCase() !== filterByKind.toLowerCase()) {
      return false;
    }
    return true;
  });

  const runKinds = Array.from(new Set((linksQuery.data || []).map(l => l.run_kind)));

  return (
    <div className="space-y-4">
      <ErrorBanner error={linksQuery.error} onRetry={() => void linksQuery.retry()} />

      <LoadingState isLoading={linksQuery.isLoading}>
        <div className="flex gap-4 flex-wrap">
          <input
            type="text"
            placeholder="Filter by object kind..."
            value={filterByObjectKind}
            onChange={(e) => setFilterByObjectKind(e.target.value)}
            className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          <input
            type="text"
            placeholder="Filter by object ID..."
            value={filterByObjectId}
            onChange={(e) => setFilterByObjectId(e.target.value)}
            className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          <input
            type="text"
            placeholder="Filter by run ID..."
            value={filterByRunId}
            onChange={(e) => setFilterByRunId(e.target.value)}
            className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          <select
            value={filterByKind}
            onChange={(e) => setFilterByKind(e.target.value)}
            className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All run kinds</option>
            {runKinds.map(kind => (
              <option key={kind} value={kind}>{kind}</option>
            ))}
          </select>

          {(filterByObjectKind || filterByObjectId || filterByRunId || filterByKind) && (
            <button
              onClick={() => {
                setFilterByObjectKind('');
                setFilterByObjectId('');
                setFilterByRunId('');
                setFilterByKind('');
              }}
              className="px-3 py-2 text-sm bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              Clear filters
            </button>
          )}
        </div>

        <div className="text-sm text-gray-600">
          Showing {filteredLinks.length} of {linksQuery.data?.length || 0} links
        </div>

        {(linksQuery.data || []).length === 0 ? (
          <EmptyState
            title="No inspect run links yet"
            description="Inspect run links are created when jobs or checker runs are associated with project artifacts."
          />
        ) : filteredLinks.length === 0 ? (
          <div className="border rounded-lg p-8 text-center bg-gray-50">
            <p className="text-gray-600">No inspect run links match your current filters. Try clearing filters to see all available links.</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredLinks.map(link => (
              <InspectRunLinkCard key={link.link_id} link={link} />
            ))}
          </div>
        )}
      </LoadingState>
    </div>
  );
}
