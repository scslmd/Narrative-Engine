import { useCallback, useMemo } from 'react';
import type { RevisionSuggestion, SuggestionStatus } from '../types/aids';
import type { LLMRevisionSuggestion } from '../types/manuscriptAssist';

export interface UseMergedSuggestionsArgs {
  revisionSuggestions: RevisionSuggestion[];
  llmSuggestions: LLMRevisionSuggestion[];
  onRevisionAccept: (suggestionId: string) => Promise<void>;
  onRevisionReject: (suggestionId: string) => Promise<void>;
  onLlmAccept: (suggestionId: string) => Promise<void>;
  onLlmReject: (suggestionId: string) => Promise<void>;
  onLlmArchive: (suggestionId: string) => Promise<void>;
}

function convertLlmToRevision(item: LLMRevisionSuggestion): RevisionSuggestion {
  return {
    suggestion_id: item.suggestion_id,
    project_id: item.project_id,
    target_document_id: item.target_document_id,
    source_text: item.source_text,
    proposed_text: item.proposed_text,
    rationale: item.rationale,
    source_context: item.source_context,
    status: (item.status === 'ARCHIVED' ? 'REJECTED' : item.status) as SuggestionStatus,
  };
}

export function useMergedSuggestions(args: UseMergedSuggestionsArgs): {
  suggestions: RevisionSuggestion[];
  openSuggestions: RevisionSuggestion[];
  handleSuggestionAccept: (suggestionId: string) => Promise<void>;
  handleSuggestionReject: (suggestionId: string) => Promise<void>;
  handleSuggestionArchive: (suggestionId: string) => Promise<void>;
} {
  const {
    revisionSuggestions,
    llmSuggestions,
    onRevisionAccept,
    onRevisionReject,
    onLlmAccept,
    onLlmReject,
    onLlmArchive,
  } = args;

  const llmIds = useMemo(() => new Set(llmSuggestions.map((s) => s.suggestion_id)), [llmSuggestions]);

  const suggestions = useMemo(
    () => [...revisionSuggestions, ...llmSuggestions.map(convertLlmToRevision)],
    [revisionSuggestions, llmSuggestions],
  );

  const openSuggestions = useMemo(
    () => suggestions.filter((s) => s.status === 'REQUESTED' || s.status === 'PENDING'),
    [suggestions],
  );

  const handleSuggestionAccept = useCallback(
    async (suggestionId: string) => {
      if (llmIds.has(suggestionId)) {
        await onLlmAccept(suggestionId);
      } else {
        await onRevisionAccept(suggestionId);
      }
    },
    [llmIds, onLlmAccept, onRevisionAccept],
  );

  const handleSuggestionReject = useCallback(
    async (suggestionId: string) => {
      if (llmIds.has(suggestionId)) {
        await onLlmReject(suggestionId);
      } else {
        await onRevisionReject(suggestionId);
      }
    },
    [llmIds, onLlmReject, onRevisionReject],
  );

  const handleSuggestionArchive = useCallback(
    async (suggestionId: string) => {
      if (llmIds.has(suggestionId)) {
        await onLlmArchive(suggestionId);
      }
    },
    [llmIds, onLlmArchive],
  );

  return {
    suggestions,
    openSuggestions,
    handleSuggestionAccept,
    handleSuggestionReject,
    handleSuggestionArchive,
  };
}
