import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { InspectRunLink } from '../../types/inspectLinks';
import { getInspectLinks } from '../../services/inspectLinks';
import { InspectRunLinkCard } from './InspectRunLinkCard';

interface InspectRunLinksListProps {
  projectId?: string;
}

export function InspectRunLinksList({ projectId }: InspectRunLinksListProps) {
  const [filterByFinding, setFilterByFinding] = useState<string>('');
  const [filterByRunId, setFilterByRunId] = useState<string>('');
  const [filterByKind, setFilterByKind] = useState<string>('');

  const { data: links = [], isLoading } = useQuery<InspectRunLink[]>({
    queryKey: ['inspect-links', projectId, filterByFinding, filterByRunId],
    queryFn: () => getInspectLinks(projectId, filterByFinding || undefined, filterByRunId || undefined),
  });

  const filteredLinks = links.filter(link => {
    if (filterByKind && link.run_kind.toLowerCase() !== filterByKind.toLowerCase()) {
      return false;
    }
    return true;
  });

  const runKinds = Array.from(new Set(links.map(l => l.run_kind)));

  if (isLoading) {
    return <div className="text-gray-500">Loading inspect run links...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-4 flex-wrap">
        <input
          type="text"
          placeholder="Filter by finding ID..."
          value={filterByFinding}
          onChange={(e) => setFilterByFinding(e.target.value)}
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

        {(filterByFinding || filterByRunId || filterByKind) && (
          <button
            onClick={() => {
              setFilterByFinding('');
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
        Showing {filteredLinks.length} of {links.length} links
      </div>

      {filteredLinks.length === 0 ? (
        <div className="border rounded-lg p-8 text-center bg-gray-50">
          <p className="text-gray-600">No inspect run links found</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredLinks.map(link => (
            <InspectRunLinkCard key={link.link_id} link={link} />
          ))}
        </div>
      )}
    </div>
  );
}
