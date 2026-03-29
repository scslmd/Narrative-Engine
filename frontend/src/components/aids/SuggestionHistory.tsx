import { useState } from 'react';
import type { RevisionSuggestion } from '../../types/aids';

interface SuggestionHistoryProps {
  suggestions: RevisionSuggestion[];
  onSelect?: (suggestion: RevisionSuggestion) => void;
}

export function SuggestionHistory({ suggestions, onSelect }: SuggestionHistoryProps) {
  const [filter, setFilter] = useState<'all' | 'pending' | 'accepted' | 'rejected'>('all');

  const filteredSuggestions = suggestions.filter(s => {
    if (filter === 'all') return true;
    return s.state.toLowerCase() === filter;
  });

  const groupedByDate = groupSuggestionsByDate(filteredSuggestions);

  return (
    <div className="flex flex-col h-full">
      {/* Filter tabs */}
      <div className="flex border-b border-gray-200 bg-white">
        {(['all', 'pending', 'accepted', 'rejected'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 text-sm font-medium capitalize ${
              filter === f
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {f}
            <span className="ml-1 text-gray-400">
              ({suggestions.filter(s => f === 'all' || s.state.toLowerCase() === f).length})
            </span>
          </button>
        ))}
      </div>

      {/* History list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {Object.entries(groupedByDate).map(([date, dateSuggestions]) => (
          <div key={date}>
            <h3 className="text-sm font-medium text-gray-500 mb-2">{formatDate(date)}</h3>
            <div className="space-y-2">
              {dateSuggestions.map(suggestion => (
                <SuggestionItem
                  key={suggestion.suggestion_id}
                  suggestion={suggestion}
                  onClick={() => onSelect?.(suggestion)}
                />
              ))}
            </div>
          </div>
        ))}

        {filteredSuggestions.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No suggestions found</p>
          </div>
        )}
      </div>
    </div>
  );
}

function SuggestionItem({
  suggestion,
  onClick,
}: {
  suggestion: RevisionSuggestion;
  onClick?: () => void;
}) {
  const stateColor = {
    PENDING: 'bg-yellow-100 text-yellow-800',
    ACCEPTED: 'bg-green-100 text-green-800',
    REJECTED: 'bg-red-100 text-red-800',
  }[suggestion.state];

  return (
    <div
      className={`bg-white border border-gray-200 rounded-lg p-3 cursor-pointer hover:border-gray-300 transition-colors`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-2">
        <span className={`px-2 py-0.5 text-xs rounded ${stateColor}`}>
          {suggestion.state}
        </span>
        <span className="text-xs text-gray-400">
          {new Date(suggestion.created_at).toLocaleTimeString()}
        </span>
      </div>

      <div className="text-sm text-gray-700 mb-1">
        <span className="text-red-600 line-through mr-2">{truncate(suggestion.anchor_text, 30)}</span>
        <span className="text-green-600">{truncate(suggestion.proposed_text, 40)}</span>
      </div>

      <p className="text-xs text-gray-500 italic">{suggestion.rationale}</p>
    </div>
  );
}

function groupSuggestionsByDate(suggestions: RevisionSuggestion[]): Record<string, RevisionSuggestion[]> {
  return suggestions.reduce((acc, suggestion) => {
    const date = new Date(suggestion.created_at).toLocaleDateString();
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(suggestion);
    return acc;
  }, {} as Record<string, RevisionSuggestion[]>);
}

function formatDate(date: string): string {
  const d = new Date(date);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date === today.toLocaleDateString()) {
    return 'Today';
  }
  if (date === yesterday.toLocaleDateString()) {
    return 'Yesterday';
  }
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
}

function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + '...';
}
