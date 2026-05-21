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
  onSuggestionArchive?: (suggestionId: string) => void;
}

export function AidsPanel({
  suggestions = [],
  onSuggestionSelect,
  onSuggestionAccept,
  onSuggestionReject,
  onSuggestionArchive,
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
    <div className="flex h-full w-full flex-col border-l border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900">
      <div className="flex shrink-0 flex-col border-b border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-slate-100">Manuscript Aids</h2>
        <p className="mt-0.5 text-[10px] text-gray-500 dark:text-slate-400">
          {openSuggestions.length} open suggestion{openSuggestions.length === 1 ? '' : 's'}
        </p>
      </div>

      <div className="flex border-b border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 gap-1">
        <button
          onClick={() => setActiveTab('suggestions')}
          className={`px-2 py-0.5 text-[10px] font-medium rounded transition-colors ${
            activeTab === 'suggestions'
              ? 'bg-blue-600 text-white'
              : 'text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-700'
          }`}
        >
          Suggestions
        </button>
        <button
          onClick={() => setActiveTab('diff')}
          className={`px-2 py-0.5 text-[10px] font-medium rounded transition-colors ${
            activeTab === 'diff'
              ? 'bg-blue-600 text-white'
              : 'text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-700'
          }`}
        >
          Diff
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-2 py-0.5 text-[10px] font-medium rounded transition-colors ${
            activeTab === 'history'
              ? 'bg-blue-600 text-white'
              : 'text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-700'
          }`}
        >
          History
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {activeTab === 'suggestions' && (
          <div className="space-y-2">
            {openSuggestions.length === 0 ? (
              <div className="py-6 text-center text-gray-500 dark:text-slate-400">
                <p className="text-xs">No open suggestions</p>
                <p className="mt-1 text-[10px]">Open manuscript suggestions will appear here.</p>
              </div>
            ) : (
              openSuggestions.map((suggestion) => (
                <div
                  key={suggestion.suggestion_id}
                  role="button"
                  tabIndex={0}
                  className={`w-full cursor-pointer rounded-lg border bg-white dark:bg-slate-800 p-2.5 text-left transition-colors ${
                    selectedSuggestionId === suggestion.suggestion_id
                      ? 'border-blue-500 ring-1 ring-blue-100'
                      : 'border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600'
                  }`}
                  onClick={() => handleSuggestionSelect(suggestion)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      handleSuggestionSelect(suggestion);
                    }
                  }}
                >
                  <div className="mb-1.5 flex items-start justify-between gap-2">
                    <span className="text-[10px] font-mono text-gray-500 dark:text-slate-400">{suggestion.status}</span>
                    <span className="text-[10px] text-gray-400 dark:text-slate-500">{suggestion.target_document_id}</span>
                  </div>

                  <div className="mb-1.5 text-xs text-gray-700 dark:text-slate-300">
                    <span className="mr-1.5 text-red-600 line-through">
                      {suggestion.source_text || 'Source text unavailable'}
                    </span>
                    <span className="text-green-600">
                      {suggestion.proposed_text ? `-> ${suggestion.proposed_text}` : '-> No proposed text'}
                    </span>
                  </div>

                  <p className="text-[10px] italic text-gray-500 dark:text-slate-400">{suggestion.rationale}</p>

                  {(onSuggestionAccept || onSuggestionReject || onSuggestionArchive) && (
                    <div className="mt-2 flex gap-1.5">
                      {onSuggestionAccept && (
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            onSuggestionAccept(suggestion.suggestion_id);
                          }}
                          className="rounded bg-green-100 dark:bg-green-900/40 px-1.5 py-0.5 text-[10px] text-green-700 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-900/60"
                        >
                          Accept
                        </button>
                      )}
                      {onSuggestionReject && (
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            onSuggestionReject(suggestion.suggestion_id);
                          }}
                          className="rounded bg-red-100 dark:bg-red-900/40 px-1.5 py-0.5 text-[10px] text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/60"
                        >
                          Reject
                        </button>
                      )}
                      {onSuggestionArchive && (
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            onSuggestionArchive(suggestion.suggestion_id);
                          }}
                          className="rounded bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 text-[10px] text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600"
                        >
                          Archive
                        </button>
                      )}
                    </div>
                  )}
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
