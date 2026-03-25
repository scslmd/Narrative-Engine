import { useBibleStore } from '../../stores/bibleStore';
import type { BibleEntry } from '../../types/bible';

const TYPE_ICONS: Record<BibleEntry['type'], string> = {
  character: '👤',
  location: '📍',
  rule: '⚖️',
  object: '🎁',
  concept: '💡',
};

interface PinnedEntryProps {
  entry: BibleEntry;
}

export default function PinnedEntry({ entry }: PinnedEntryProps) {
  const unpinEntry = useBibleStore((state) => state.unpinEntry);

  return (
    <div className="bg-white rounded-lg p-3 border shadow-sm">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-1">
          <span className="text-lg">{TYPE_ICONS[entry.type]}</span>
          <h4 className="font-medium text-gray-900 text-sm truncate">
            {entry.title}
          </h4>
        </div>

        <button
          onClick={() => unpinEntry(entry.id)}
          className="text-gray-400 hover:text-red-500 transition-colors p-0.5"
          title="Unpin"
        >
          ×
        </button>
      </div>

      <p className="text-xs text-gray-600 line-clamp-3">
        {entry.summary}
      </p>

      <span className={`inline-block mt-2 px-2 py-0.5 rounded-full text-xs font-medium ${
        entry.type === 'character' ? 'bg-purple-100 text-purple-700' :
        entry.type === 'location' ? 'bg-green-100 text-green-700' :
        entry.type === 'rule' ? 'bg-orange-100 text-orange-700' :
        entry.type === 'object' ? 'bg-blue-100 text-blue-700' :
        'bg-gray-100 text-gray-700'
      }`}>
        {entry.type}
      </span>
    </div>
  );
}
