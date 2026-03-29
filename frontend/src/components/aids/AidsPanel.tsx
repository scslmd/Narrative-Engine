import { useState } from 'react';
import type { RevisionSuggestion } from '../../types/aids';
import { DiffViewer } from './DiffViewer';
import { SuggestionHistory } from './SuggestionHistory';

interface AidsPanelProps {
  projectId: string;
  suggestions?: RevisionSuggestion[];
  onSuggestionSelect?: (suggestion: RevisionSuggestion) => void;
  onSuggestionAccept?: (suggestionId: string) => void;
  onSuggestionReject?: (suggestionId: string) => void;
}

export function AidsPanel({
  suggestions = [],
  onSuggestionSelect,
  onSuggestionAccept,
  onSuggestionReject,
}: AidsPanelProps) {
  const [activeTab, setActiveTab] = useState<'suggestions' | 'diff' | 'history'>('suggestions');
  const [selectedSuggestionId, setSelectedSuggestionId] = useState<string | null>(null);

  const selectedSuggestion = suggestions.find((suggestion) => suggestion.suggestion_id === selectedSuggestionId) ?? null;
  const openSuggestions = suggestions.filter(
    (suggestion) => suggestion.status === 'REQUESTED' || suggestion.status === 'PENDING',
  );

  const handleSuggestionSelect = (suggestion: RevisionSuggestion) => {
    setSelectedSuggestionId(suggestion.suggestion_id);
    setActiveTab('diff');
    onSuggestionSelect?.(suggestion);
  };

  return (
    <div className="flex h-full w-96 flex-col border-l border-gray-200 bg-gray-50">
      <div className="border-b border-gray-200 bg-white p-4">
        <h2 className="text-lg font-semibold text-gray-900">Manuscript Aids</h2>
        <p className="mt-1 text-sm text-gray-500">
          {openSuggestions.length} open suggestion{openSuggestions.length === 1 ? '' : 's'}
        </p>
      </div>

      <div className="flex border-b border-gray-200 bg-white">
        <button
          onClick={() => setActiveTab('suggestions')}
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === 'suggestions'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Suggestions
        </button>
        <button
          onClick={() => setActiveTab('diff')}
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === 'diff'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Diff Viewer
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === 'history'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          History
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'suggestions' && (
          <div className="space-y-4">
            {openSuggestions.length === 0 ? (
              <div className="py-8 text-center text-gray-500">
                <p>No open suggestions</p>
                <p className="mt-2 text-sm">Open manuscript suggestions will appear here.</p>
              </div>
            ) : (
              openSuggestions.map((suggestion) => (
                <div
                  key={suggestion.suggestion_id}
                  role="button"
                  tabIndex={0}
                  className={`w-full cursor-pointer rounded-lg border bg-white p-4 text-left transition-colors ${
                    selectedSuggestionId === suggestion.suggestion_id
                      ? 'border-blue-500 ring-2 ring-blue-100'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleSuggestionSelect(suggestion)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      handleSuggestionSelect(suggestion);
                    }
                  }}
                >
                  <div className="mb-2 flex items-start justify-between gap-3">
                    <span className="text-xs font-mono text-gray-500">{suggestion.status}</span>
                    <span className="text-xs text-gray-400">{suggestion.target_document_id}</span>
                  </div>

                  <div className="mb-2 text-sm text-gray-700">
                    <span className="mr-2 text-red-600 line-through">
                      {suggestion.source_text || 'Source text unavailable'}
                    </span>
                    <span className="text-green-600">
                      {suggestion.proposed_text ? `-> ${suggestion.proposed_text}` : '-> No proposed text'}
                    </span>
                  </div>

                  <p className="text-xs italic text-gray-500">{suggestion.rationale}</p>

                  <div className="mt-3 flex gap-2">
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        onSuggestionAccept?.(suggestion.suggestion_id);
                      }}
                      className="rounded bg-green-100 px-2 py-1 text-xs text-green-700 hover:bg-green-200"
                    >
                      Accept
                    </button>
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        onSuggestionReject?.(suggestion.suggestion_id);
                      }}
                      className="rounded bg-red-100 px-2 py-1 text-xs text-red-700 hover:bg-red-200"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'diff' && (
          <DiffViewer
            originalText={selectedSuggestion?.source_text ?? null}
            modifiedText={selectedSuggestion?.proposed_text ?? null}
            originalLabel="Source"
            modifiedLabel="Proposed"
            emptyStateTitle="Select a suggestion to compare"
            emptyStateDescription="Pick a suggestion from the open list or history to view the source and proposed text side by side."
          />
        )}

        {activeTab === 'history' && (
          <SuggestionHistory
            suggestions={suggestions}
            selectedSuggestionId={selectedSuggestionId}
            onSelect={handleSuggestionSelect}
          />
        )}
      </div>
    </div>
  );
}
