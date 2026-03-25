import { useBibleStore } from '../../stores/bibleStore';
import PinnedEntry from './PinnedEntry';
import ErrorBoundary from '../ErrorBoundary';
import type { BibleEntryType } from '../../types/bible';

const TYPE_LABELS: Record<BibleEntryType, string> = {
  character: 'Characters',
  location: 'Locations',
  rule: 'Rules',
  object: 'Objects',
  concept: 'Concepts',
};

interface BibleEntryListProps {
  projectId: string;
}

export default function BibleEntryList({ projectId }: BibleEntryListProps) {
  const pinnedEntries = useBibleStore((state) => state.pinnedEntries);

  const grouped = pinnedEntries.reduce(
    (acc, entry) => {
      if (!acc[entry.type]) {
        acc[entry.type] = [];
      }
      acc[entry.type].push(entry);
      return acc;
    },
    {} as Record<BibleEntryType, typeof pinnedEntries>
  );

  const hasEntries = Object.keys(grouped).length > 0;

  if (!hasEntries) {
    return (
      <div className="p-4 text-center">
        <p className="text-sm text-gray-500 mb-1">No pinned entries</p>
        <p className="text-xs text-gray-400">Pin items from world bible for quick reference</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-3">
      {(Object.keys(grouped) as BibleEntryType[]).map((type) => (
        <div key={type}>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            {TYPE_LABELS[type]} ({grouped[type].length})
          </h3>
          
          <div className="space-y-2">
            {grouped[type].map((entry) => (
              <ErrorBoundary key={entry.id}>
                <PinnedEntry entry={entry} />
              </ErrorBoundary>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
