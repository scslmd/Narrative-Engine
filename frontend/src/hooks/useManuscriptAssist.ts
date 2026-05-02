import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  applyLLMSuggestion,
  getLLMSuggestions,
  listManuscriptAssists,
  rejectLLMSuggestion,
  submitManuscriptAssist,
} from '../services/manuscriptAssist';
import type {
  LLMRevisionSuggestion,
  ManuscriptAssistKind,
  ManuscriptAssistResult,
  TextRange,
} from '../types/manuscriptAssist';

interface UseManuscriptAssistArgs {
  projectId?: string;
  documentId?: string | null;
  documentVersion?: number;
  content?: string;
}

interface SubmitAssistOptions {
  create_branch?: boolean;
  create_draft_artifact?: boolean;
}

export function useManuscriptAssist({
  projectId,
  documentId,
  documentVersion,
  content,
}: UseManuscriptAssistArgs) {
  const queryClient = useQueryClient();
  const [selectedRange, setSelectedRange] = useState<TextRange | null>(null);

  const assistRunsQuery = useQuery({
    queryKey: ['manuscript-assist', 'runs', projectId, documentId ?? null],
    queryFn: () => listManuscriptAssists(projectId!, documentId ?? undefined),
    enabled: Boolean(projectId && documentId),
  });

  const suggestionsQuery = useQuery({
    queryKey: ['manuscript-assist', 'suggestions', projectId, documentId ?? null, 'open'],
    queryFn: () => getLLMSuggestions(projectId!, documentId!, undefined),
    enabled: Boolean(projectId && documentId),
  });

  const submitMutation = useMutation({
    mutationFn: (args: { kind: ManuscriptAssistKind; instruction: string; options?: SubmitAssistOptions }) =>
      submitManuscriptAssist({
        project_id: projectId!,
        document_id: documentId!,
        assist_kind: args.kind,
        instruction: args.instruction,
        text_range: selectedRange,
        create_branch: args.options?.create_branch,
        create_draft_artifact: args.options?.create_draft_artifact,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['manuscript-assist', 'runs', projectId, documentId ?? null] });
      await queryClient.invalidateQueries({ queryKey: ['manuscript-assist', 'suggestions', projectId, documentId ?? null, 'open'] });
    },
  });

  const applyMutation = useMutation({
    mutationFn: (suggestionId: string) =>
      applyLLMSuggestion({
        project_id: projectId!,
        document_id: documentId!,
        suggestion_id: suggestionId,
        expected_document_version: documentVersion ?? 1,
        apply_mode: 'replace_range',
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['manuscript-documents', projectId] });
      await queryClient.invalidateQueries({ queryKey: ['manuscript-assist', 'suggestions', projectId, documentId ?? null, 'open'] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (suggestionId: string) => rejectLLMSuggestion(projectId!, suggestionId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['manuscript-assist', 'suggestions', projectId, documentId ?? null, 'open'] });
    },
  });

  const setSelectionFromEditor = (start: number, end: number, textContent: string) => {
    if (start === end) {
      setSelectedRange(null);
      return;
    }
    const selectedText = textContent.slice(start, end);
    const anchorBefore = textContent.slice(Math.max(0, start - 120), start);
    const anchorAfter = textContent.slice(end, Math.min(textContent.length, end + 120));
    setSelectedRange({
      start_offset: start,
      end_offset: end,
      selected_text: selectedText,
      anchor_before: anchorBefore,
      anchor_after: anchorAfter,
    });
  };

  const submitAssist = (kind: ManuscriptAssistKind, instruction: string, options?: SubmitAssistOptions) =>
    submitMutation.mutateAsync({ kind, instruction, options });

  const applySuggestion = (suggestionId: string) => applyMutation.mutateAsync(suggestionId);

  const rejectSuggestion = (suggestionId: string) => rejectMutation.mutateAsync(suggestionId);

  const assistRuns: ManuscriptAssistResult[] = useMemo(
    () => assistRunsQuery.data ?? [],
    [assistRunsQuery.data],
  );
  const llmSuggestions: LLMRevisionSuggestion[] = useMemo(
    () => suggestionsQuery.data ?? [],
    [suggestionsQuery.data],
  );

  return {
    selectedRange,
    assistRuns,
    llmSuggestions,
    isSubmittingAssist: submitMutation.isPending,
    submitAssist,
    applySuggestion,
    rejectSuggestion,
    setSelectionFromEditor,
    content,
  };
}
