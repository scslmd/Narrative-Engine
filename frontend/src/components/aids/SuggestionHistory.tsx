import { useState } from 'react';
import type { RevisionSuggestion } from '../../types/aids';

interface SuggestionHistoryProps {
  suggestions: RevisionSuggestion[];
  selectedSuggestionId?: string | null;
  onSelect?: (suggestion: RevisionSuggestion) => void;
}

type SuggestionFilter = 'all' | 'requested' | 'pending' | 'accepted' | 'rejected' | 'superseded';

export function SuggestionHistory({
  suggestions,
  selectedSuggestionId,
  onSelect,
}: SuggestionHistoryProps) {
  const [filter, setFilter] = useState<SuggestionFilter>('all');

  const filteredSuggestions = suggestions.filter((suggestion) => {
    if (filter === 'all') {
      return true;
    }

    return suggestion.status.toLowerCase() === filter;
  });

  const groupedByDocument = groupSuggestionsByDocument(filteredSuggestions);

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-wrap border-b border-gray-200 bg-white">
        {(['all', 'requested', 'pending', 'accepted', 'rejected', 'superseded'] as const).map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => setFilter(value)}
            className={`px-4 py-2 text-sm font-medium capitalize ${
              filter === value
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {value}
            <span className="ml-1 text-gray-400">
              ({suggestions.filter((suggestion) => value === 'all' || suggestion.status.toLowerCase() === value).length})
            </span>
          </button>
        ))}
      </div>

      <div className="flex-1 space-y-6 overflow-y-auto p-4">
        {Object.entries(groupedByDocument).map(([documentId, documentSuggestions]) => (
          <div key={documentId}>
            <h3 className="mb-2 text-sm font-medium text-gray-500">
              {documentId}
              <span className="ml-2 text-gray-400">({documentSuggestions.length})</span>
            </h3>
            <div className="space-y-2">
              {documentSuggestions.map((suggestion) => (
                <SuggestionItem
                  key={suggestion.suggestion_id}
                  suggestion={suggestion}
                  selected={selectedSuggestionId === suggestion.suggestion_id}
                  onClick={() => onSelect?.(suggestion)}
                />
              ))}
            </div>
          </div>
        ))}

        {filteredSuggestions.length === 0 && (
          <div className="py-8 text-center text-gray-500">
            <p>No suggestions found</p>
          </div>
        )}
      </div>
    </div>
  );
}

function SuggestionItem({
  suggestion,
  selected,
  onClick,
}: {
  suggestion: RevisionSuggestion;
  selected: boolean;
  onClick?: () => void;
}) {
  const stateColor = {
    REQUESTED: 'bg-slate-100 text-slate-700',
    PENDING: 'bg-yellow-100 text-yellow-800',
    ACCEPTED: 'bg-green-100 text-green-800',
    REJECTED: 'bg-red-100 text-red-800',
    SUPERSEDED: 'bg-gray-100 text-gray-700',
  }[suggestion.status];

  return (
    <button
      type="button"
      className={`w-full rounded-lg border bg-white p-3 text-left transition-colors ${
        selected ? 'border-blue-500 ring-2 ring-blue-100' : 'border-gray-200 hover:border-gray-300'
      }`}
      onClick={onClick}
    >
      <div className="mb-2 flex items-start justify-between gap-3">
        <span className={`rounded px-2 py-0.5 text-xs ${stateColor}`}>{suggestion.status}</span>
        <span className="text-xs text-gray-400">{suggestion.target_document_id}</span>
      </div>

      <div className="mb-2 text-sm text-gray-700">
        <span className="mr-2 text-red-600 line-through">{truncate(suggestion.source_text, 40)}</span>
        <span className="text-green-600">{truncate(suggestion.proposed_text, 48)}</span>
      </div>

      <p className="text-xs italic text-gray-500">{suggestion.rationale}</p>

      {suggestion.source_context.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {suggestion.source_context.slice(0, 4).map((context) => (
            <span key={context} className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
              {context}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}

function groupSuggestionsByDocument(
  suggestions: RevisionSuggestion[],
): Record<string, RevisionSuggestion[]> {
  return suggestions.reduce((acc, suggestion) => {
    if (!acc[suggestion.target_document_id]) {
      acc[suggestion.target_document_id] = [];
    }

    acc[suggestion.target_document_id].push(suggestion);
    return acc;
  }, {} as Record<string, RevisionSuggestion[]>);
}

function truncate(text: string, length: number): string {
  if (text.length <= length) {
    return text;
  }

  return `${text.slice(0, length)}...`;
}
