import { useState } from 'react';
import type { RevisionSuggestion } from '../../types/aids';

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

  const pendingSuggestions = suggestions.filter(s => s.state === 'PENDING');
  const acceptedSuggestions = suggestions.filter(s => s.state === 'ACCEPTED');
  const rejectedSuggestions = suggestions.filter(s => s.state === 'REJECTED');

  // selectedSuggestion available via selectedSuggestionId if needed

  return (
    <div className="w-96 bg-gray-50 border-l border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <h2 className="text-lg font-semibold text-gray-900">Manuscript Aids</h2>
        <p className="text-sm text-gray-500 mt-1">
          {pendingSuggestions.length} pending suggestions
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-white">
        <button
          onClick={() => setActiveTab('suggestions')}
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === 'suggestions'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Suggestions
        </button>
        <button
          onClick={() => setActiveTab('diff')}
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === 'diff'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Diff Viewer
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === 'history'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          History
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'suggestions' && (
          <div className="space-y-4">
            {pendingSuggestions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No pending suggestions</p>
                <p className="text-sm mt-2">Suggestions will appear here</p>
              </div>
            ) : (
              pendingSuggestions.map(suggestion => (
                <div
                  key={suggestion.suggestion_id}
                  className={`bg-white border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedSuggestionId === suggestion.suggestion_id
                      ? 'border-blue-500 ring-2 ring-blue-100'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => {
                    setSelectedSuggestionId(suggestion.suggestion_id);
                    onSuggestionSelect?.(suggestion);
                  }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-xs font-mono text-gray-500">
                      {suggestion.suggestion_type}
                    </span>
                    <span className="text-xs text-gray-400">
                      {new Date(suggestion.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  
                  <div className="text-sm text-gray-700 mb-2">
                    <span className="text-red-600 line-through">{suggestion.anchor_text}</span>
                    <span className="text-green-600"> → {suggestion.proposed_text}</span>
                  </div>
                  
                  <p className="text-xs text-gray-500 italic">{suggestion.rationale}</p>
                  
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSuggestionAccept?.(suggestion.suggestion_id);
                      }}
                      className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                    >
                      Accept
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSuggestionReject?.(suggestion.suggestion_id);
                      }}
                      className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
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
          <div className="text-center py-8 text-gray-500">
            <p>Diff Viewer</p>
            <p className="text-sm mt-2">Select two versions to compare</p>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-700">Accepted ({acceptedSuggestions.length})</h3>
            {acceptedSuggestions.map(suggestion => (
              <div key={suggestion.suggestion_id} className="text-sm text-gray-600 p-2 bg-green-50 rounded">
                {suggestion.proposed_text}
              </div>
            ))}
            
            <h3 className="text-sm font-medium text-gray-700 mt-4">Rejected ({rejectedSuggestions.length})</h3>
            {rejectedSuggestions.map(suggestion => (
              <div key={suggestion.suggestion_id} className="text-sm text-gray-600 p-2 bg-red-50 rounded">
                {suggestion.proposed_text}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
