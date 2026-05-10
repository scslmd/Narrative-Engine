import { useCallback, useMemo, useState } from 'react';
import { useQueries, useQueryClient } from '@tanstack/react-query';
import {
  applyLLMSuggestion,
  archiveLLMSuggestion,
  getManuscriptAssistGates,
  getLLMSuggestions,
  listManuscriptAssists,
  rejectLLMSuggestion,
  retryManuscriptAssist,
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

  const queries = useQueries({
    queries: [
      {
        queryKey: ['manuscript-assist', 'runs', projectId, documentId ?? null],
        queryFn: () => listManuscriptAssists(projectId!, documentId ?? undefined),
        enabled: Boolean(projectId && documentId),
      },
      {
        queryKey: ['manuscript-assist', 'suggestions', projectId, documentId ?? null, 'open'],
        queryFn: () => getLLMSuggestions(projectId!, documentId!, undefined),
        enabled: Boolean(projectId && documentId),
      },
    ],
  });

  const latestAssistId = (queries[0].data as ManuscriptAssistResult[] | undefined)?.[0]?.assist_id;
  const gatesQuery = useQueries({
    queries: [
      {
        queryKey: ['manuscript-assist', 'gates', latestAssistId],
        queryFn: () => getManuscriptAssistGates(latestAssistId!),
        enabled: Boolean(latestAssistId),
      },
    ],
  });

  const mutations = useMemo(() => {
    return {
      submit: async (args: { kind: ManuscriptAssistKind; instruction: string; options?: SubmitAssistOptions }) => {
        await submitManuscriptAssist({
          project_id: projectId!,
          document_id: documentId!,
          assist_kind: args.kind,
          instruction: args.instruction,
          text_range: selectedRange,
          create_branch: args.options?.create_branch,
          create_draft_artifact: args.options?.create_draft_artifact,
        });
        await queryClient.invalidateQueries({ queryKey: ['manuscript-assist', 'runs', projectId, documentId ?? null] });
        await queryClient.invalidateQueries({ queryKey: ['manuscript-assist', 'suggestions', projectId, documentId ?? null, 'open'] });
      },
      apply: async (suggestionId: string) => {
        await applyLLMSuggestion({
          project_id: projectId!,
          document_id: documentId!,
          suggestion_id: suggestionId,
          expected_document_version: documentVersion ?? 1,
          apply_mode: 'replace_range',
        });
        await queryClient.invalidateQueries({ queryKey: ['manuscript-documents', projectId] });
        await queryClient.invalidateQueries({ queryKey: ['manuscript-assist', 'suggestions', projectId, documentId ?? null, 'open'] });
      },
      reject: async (suggestionId: string) => {
        await rejectLLMSuggestion(projectId!, suggestionId);
        await queryClient.invalidateQueries({ queryKey: ['manuscript-assist', 'suggestions', projectId, documentId ?? null, 'open'] });
      },
      archive: async (suggestionId: string) => {
        await archiveLLMSuggestion(projectId!, suggestionId);
        await queryClient.invalidateQueries({ queryKey: ['manuscript-assist', 'suggestions', projectId, documentId ?? null, 'open'] });
      },
      retry: async (assistId: string) => {
        await retryManuscriptAssist(assistId);
        await queryClient.invalidateQueries({ queryKey: ['manuscript-assist', 'runs', projectId, documentId ?? null] });
      },
    };
  }, [projectId, documentId, documentVersion, selectedRange, queryClient]);

  const [submitPending, setSubmitPending] = useState(false);

  const setSelectionFromEditor = useCallback((start: number, end: number, textContent: string) => {
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
  }, []);

  const submitAssist = useCallback(
    async (kind: ManuscriptAssistKind, instruction: string, options?: SubmitAssistOptions) => {
      setSubmitPending(true);
      try {
        await mutations.submit({ kind, instruction, options });
      } finally {
        setSubmitPending(false);
      }
    },
    [mutations],
  );

  const applySuggestion = useCallback(
    async (suggestionId: string) => mutations.apply(suggestionId),
    [mutations],
  );

  const rejectSuggestion = useCallback(
    async (suggestionId: string) => mutations.reject(suggestionId),
    [mutations],
  );

  const archiveSuggestion = useCallback(
    async (suggestionId: string) => mutations.archive(suggestionId),
    [mutations],
  );

  const retryAssist = useCallback(
    async (assistId: string) => mutations.retry(assistId),
    [mutations],
  );

  const assistRuns: ManuscriptAssistResult[] = useMemo(
    () => queries[0].data ?? [],
    [queries[0].data],
  );
  const llmSuggestions: LLMRevisionSuggestion[] = useMemo(
    () => queries[1].data ?? [],
    [queries[1].data],
  );

  return {
    selectedRange,
    assistRuns,
    llmSuggestions,
    isSubmittingAssist: submitPending,
    submitAssist,
    applySuggestion,
    rejectSuggestion,
    archiveSuggestion,
    setSelectionFromEditor,
    content,
    retryAssist,
    latestAssistGates: (gatesQuery[0].data ?? []),
  };
}
