import { useCallback, useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { getManuscriptAssist, submitManuscriptAssist } from '../../services/manuscriptAssist';
import { toast } from '../../lib/toast';

export interface DraftFormAIState {
  title: string;
  brief: string;
  mode: 'ai';
}

export interface PendingDraftInfo {
  artifact_id: string;
  title: string;
  assistId: string;
  error?: string;
}

interface UseAssistControllerArgs {
  projectId?: string;
  selectedDocumentId?: string | null;
}

export function useAssistController({
  projectId,
  selectedDocumentId,
}: UseAssistControllerArgs) {
  const [draftFormAI, setDraftFormAI] = useState<DraftFormAIState | null>(null);
  const [pendingDrafts, setPendingDrafts] = useState<Record<string, PendingDraftInfo>>({});
  const queryClient = useQueryClient();

  const generateDraftMutation = useMutation({
    mutationFn: (data: { title: string; brief: string }) => {
      if (!projectId || !selectedDocumentId) throw new Error('Missing project or document');
      return submitManuscriptAssist({
        project_id: projectId,
        document_id: selectedDocumentId,
        assist_kind: 'ai_generate_draft',
        instruction: data.brief,
        create_draft_artifact: true,
      });
    },
    onSuccess: (result) => {
      const optimisticId = `pending-${Date.now()}`;
      setPendingDrafts((prev) => ({
        ...prev,
        [result.assist_id]: {
          artifact_id: optimisticId,
          title: result.summary || 'Generating...',
          assistId: result.assist_id,
        },
      }));
      setDraftFormAI(null);
      void queryClient.invalidateQueries({ queryKey: ['draft-artifacts', projectId] });
      toast.success('Draft generation started');
    },
    onError: () => {
      toast.error('Failed to start draft generation');
    },
  });

  useEffect(() => {
    const assistIds = Object.keys(pendingDrafts);
    if (assistIds.length === 0) return;

    const interval = setInterval(async () => {
      for (const assistId of Object.keys(pendingDrafts)) {
        try {
          const run = await getManuscriptAssist(assistId);

          if (run.status === 'completed') {
            setPendingDrafts((prev) => {
              const next = { ...prev };
              delete next[assistId];
              return next;
            });
            void queryClient.invalidateQueries({ queryKey: ['draft-artifacts', projectId] });
            toast.success('Draft generation complete');
          } else if (run.status === 'failed') {
            setPendingDrafts((prev) => ({
              ...prev,
              [assistId]: { ...prev[assistId], error: run.summary || 'Generation failed' },
            }));
          }
        } catch {
          // Keep polling on transient errors.
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [pendingDrafts, projectId, queryClient]);

  const handleGenerateDraftForm = useCallback(() => {
    setDraftFormAI({ title: '', brief: '', mode: 'ai' });
  }, []);

  const handleGenerateDraft = useCallback(() => {
    if (!draftFormAI || !draftFormAI.title.trim() || !draftFormAI.brief.trim()) return;
    generateDraftMutation.mutate({
      title: draftFormAI.title.trim(),
      brief: draftFormAI.brief.trim(),
    });
  }, [draftFormAI, generateDraftMutation]);

  return {
    draftFormAI,
    pendingDrafts,
    setDraftFormAI,
    handleGenerateDraftForm,
    handleGenerateDraft,
    generateDraftPending: generateDraftMutation.isPending,
  };
}
