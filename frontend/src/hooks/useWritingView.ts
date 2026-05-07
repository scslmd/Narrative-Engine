import { useState, useEffect, useMemo, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getManuscriptDocuments,
  getDraftArtifacts,
  getRevisionSuggestions,
  updateManuscriptContent,
  triggerManuscriptReview,
  createRevisionSuggestion,
  createDraftArtifact,
  promoteDraftToManuscript,
  continueDraft,
  createAlternateVariant,
} from '../services/drafting';
import { submitManuscriptAssist } from '../services/manuscriptAssist';
import type { ManuscriptDocument, DraftArtifact } from '../types/drafting';
import type { RevisionSuggestion } from '../types/aids';
import { toast } from '../lib/toast';

export interface DraftFormState {
  title: string;
  content: string;
}

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

export interface WritingViewHookResult {
  projectId: string | undefined;
  selectedDocumentId: string | null;
  isDark: boolean;
  manuscriptDocuments: ManuscriptDocument[];
  draftArtifacts: DraftArtifact[];
  revisionSuggestions: RevisionSuggestion[];
  openSuggestions: RevisionSuggestion[];
  selectedDocument: ManuscriptDocument | undefined;
  isEditing: boolean;
  editContent: string;
  draftForm: DraftFormState | null;
  expandedDraft: string | null;
  manuscriptQueryLoading: boolean;
  draftsQueryLoading: boolean;
  wordCount: number;
  charCount: number;
  setSelectedDocumentId: (id: string) => void;
  setIsEditing: (editing: boolean) => void;
  setEditContent: (content: string) => void;
  setDraftForm: (form: DraftFormState | null) => void;
  setExpandedDraft: (id: string | null) => void;
  handleEdit: () => void;
  handleCancel: () => void;
  handleSave: () => Promise<void>;
  handleSuggestionAccept: (suggestionId: string) => Promise<void>;
  handleSuggestionReject: (suggestionId: string) => Promise<void>;
  handleCreateDraft: () => void;
  handleSubmitDraft: () => void;
  handleCancelDraft: () => void;
  handleToggleDraft: (artifactId: string) => void;
  createDraftPending: boolean;
  promotePending: boolean;
  promoteDraft: (artifactId: string) => void;
  continuePending: boolean;
  alternatePending: boolean;
  continueDraftAction: (artifactId: string) => void;
  alternateVariantAction: (artifactId: string) => void;
  draftFormAI: DraftFormAIState | null;
  pendingDrafts: Record<string, PendingDraftInfo>;
  setDraftFormAI: (form: DraftFormAIState | null) => void;
  handleGenerateDraftForm: () => void;
  handleGenerateDraft: () => void;
  generateDraftPending: boolean;
}

export function useWritingView(isDark: boolean): WritingViewHookResult {
  const { projectId, chapterId } = useParams<{ projectId: string; chapterId?: string }>();
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [draftForm, setDraftForm] = useState<DraftFormState | null>(null);
  const [draftFormAI, setDraftFormAI] = useState<DraftFormAIState | null>(null);
  const [pendingDrafts, setPendingDrafts] = useState<Record<string, PendingDraftInfo>>({});
  const [expandedDraft, setExpandedDraft] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const manuscriptQuery = useQuery({
    queryKey: ['manuscript-documents', projectId],
    queryFn: () => getManuscriptDocuments(projectId!),
    enabled: !!projectId,
  });

  const draftsQuery = useQuery({
    queryKey: ['draft-artifacts', projectId],
    queryFn: () => getDraftArtifacts(projectId!),
    enabled: !!projectId,
  });

  const suggestionsQuery = useQuery({
    queryKey: ['revision-suggestions', projectId, selectedDocumentId ?? 'all'],
    queryFn: () => getRevisionSuggestions(projectId!, selectedDocumentId ?? undefined),
    enabled: !!projectId && !!selectedDocumentId,
  });

  const manuscriptDocuments = useMemo(
    () => (manuscriptQuery.data as ManuscriptDocument[]) ?? [],
    [manuscriptQuery.data],
  );
  const draftArtifacts = (draftsQuery.data as DraftArtifact[]) ?? [];
  const revisionSuggestions = useMemo(
    () => (suggestionsQuery.data as RevisionSuggestion[]) ?? [],
    [suggestionsQuery.data],
  );

  const openSuggestions = useMemo(
    () => revisionSuggestions.filter((s) => s.status === 'REQUESTED' || s.status === 'PENDING'),
    [revisionSuggestions],
  );

  const createDraftMutation = useMutation({
    mutationFn: (data: { title: string; content: string }) =>
      createDraftArtifact({
        artifact_id: `draft-${Date.now()}`,
        project_id: projectId!,
        title: data.title,
        content: data.content,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['draft-artifacts', projectId] });
      setDraftForm(null);
      toast.success('Draft created');
    },
    onError: () => {
      toast.error('Failed to create draft');
    },
  });

  const promoteMutation = useMutation({
    mutationFn: (artifactId: string) =>
      promoteDraftToManuscript({
        project_id: projectId!,
        document_id: `doc-${Date.now()}`,
        draft_artifact_id: artifactId,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['draft-artifacts', projectId] });
      void queryClient.invalidateQueries({ queryKey: ['manuscript-documents', projectId] });
      setExpandedDraft(null);
      toast.success('Draft promoted to manuscript');
    },
    onError: () => {
      toast.error('Failed to promote draft');
    },
  });

  const continueMutation = useMutation({
    mutationFn: (artifactId: string) =>
      continueDraft(artifactId, projectId!),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['draft-artifacts', projectId] });
      toast.success('Draft continued');
    },
    onError: (err) => {
      if (err instanceof Error && err.message.includes('404')) {
        toast.error('No prior content to continue from');
      } else {
        toast.error('Failed to continue draft');
      }
    },
  });

  const alternateMutation = useMutation({
    mutationFn: (artifactId: string) =>
      createAlternateVariant(artifactId, projectId!),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['draft-artifacts', projectId] });
      toast.success('Alternate variant created');
    },
    onError: (err) => {
      if (err instanceof Error && err.message.includes('404')) {
        toast.error('No prior content to create variant from');
      } else {
        toast.error('Failed to create alternate variant');
      }
    },
  });

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
    if (manuscriptDocuments.length === 0) {
      setSelectedDocumentId(null);
      return;
    }

    if (chapterId) {
      const docForChapter = manuscriptDocuments.find(
        (doc: ManuscriptDocument) => doc.chapter_id === chapterId,
      );

      if (docForChapter) {
        if (docForChapter.document_id !== selectedDocumentId) {
          setSelectedDocumentId(docForChapter.document_id);
        }
        return;
      }
    }

    const selectedDocumentStillExists = manuscriptDocuments.some(
      (doc: ManuscriptDocument) => doc.document_id === selectedDocumentId,
    );

    if (!selectedDocumentStillExists) {
      setSelectedDocumentId(manuscriptDocuments[0].document_id);
    }
  }, [manuscriptDocuments, chapterId, selectedDocumentId]);

  useEffect(() => {
    const assistIds = Object.keys(pendingDrafts);
    if (assistIds.length === 0) return;

    const interval = setInterval(async () => {
      for (const assistId of Object.keys(pendingDrafts)) {
        try {
          const { getManuscriptAssist } = await import('../services/manuscriptAssist');
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
          // Keep polling on error
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [pendingDrafts, projectId, queryClient]);

  const selectedDocument = manuscriptDocuments.find(
    (doc: ManuscriptDocument) => doc.document_id === selectedDocumentId,
  );

  const handleEdit = useCallback(() => {
    if (selectedDocument) {
      setEditContent(selectedDocument.content);
      setIsEditing(true);
    }
  }, [selectedDocument]);

  const handleCancel = useCallback(() => {
    setIsEditing(false);
    setEditContent('');
  }, []);

  const handleSave = useCallback(async () => {
    if (!selectedDocumentId || !projectId) return;
    try {
      await updateManuscriptContent(selectedDocumentId, projectId, editContent);
      await queryClient.invalidateQueries({ queryKey: ['manuscript-documents', projectId] });
      await queryClient.invalidateQueries({ queryKey: ['revision-suggestions', projectId, selectedDocumentId] });
      setIsEditing(false);
      setEditContent('');

      try {
        const findings = await triggerManuscriptReview(selectedDocumentId, projectId);
        if (findings.length > 0) {
          toast.success(`Manuscript saved. ${findings.length} review finding(s) added.`);
        } else {
          toast.success('Manuscript saved. Review complete - no issues found.');
        }
      } catch {
        toast.success('Manuscript saved. Review queued.');
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save manuscript');
    }
  }, [selectedDocumentId, projectId, editContent, queryClient]);

  const handleSuggestionAccept = useCallback(
    async (suggestionId: string) => {
      if (!selectedDocument || !projectId) return;
      const suggestion = revisionSuggestions.find((s) => s.suggestion_id === suggestionId);
      if (!suggestion) return;

      const updatedContent = selectedDocument.content.replace(
        suggestion.source_text,
        suggestion.proposed_text,
      );

      try {
        await updateManuscriptContent(selectedDocument.document_id, projectId, updatedContent);
        await queryClient.invalidateQueries({ queryKey: ['manuscript-documents', projectId] });
        await queryClient.invalidateQueries({ queryKey: ['revision-suggestions', projectId, selectedDocument.document_id] });
        if (isEditing) {
          setEditContent(updatedContent);
        }
        toast.success('Suggestion applied');
      } catch {
        toast.error('Failed to apply suggestion');
      }
    },
    [selectedDocument, projectId, revisionSuggestions, queryClient, isEditing],
  );

  const handleSuggestionReject = useCallback(
    async (suggestionId: string) => {
      if (!selectedDocumentId || !projectId) return;
      const suggestion = revisionSuggestions.find((s) => s.suggestion_id === suggestionId);
      if (!suggestion) return;

      try {
        await createRevisionSuggestion({
          suggestion_id: suggestion.suggestion_id,
          project_id: projectId,
          target_document_id: selectedDocumentId,
          source_text: suggestion.source_text,
          proposed_text: suggestion.proposed_text,
          rationale: suggestion.rationale,
          source_context: suggestion.source_context,
          status: 'REJECTED',
        });
        await queryClient.invalidateQueries({ queryKey: ['revision-suggestions', projectId, selectedDocumentId] });
        toast.success('Suggestion rejected');
      } catch {
        toast.error('Failed to reject suggestion');
      }
    },
    [selectedDocumentId, projectId, revisionSuggestions, queryClient],
  );

  const wordCount = useMemo(() => {
    if (!selectedDocument) return 0;
    const text = isEditing ? editContent : selectedDocument.content;
    return text.trim() ? text.trim().split(/\s+/).length : 0;
  }, [selectedDocument, editContent, isEditing]);

  const charCount = useMemo(() => {
    if (!selectedDocument) return 0;
    const text = isEditing ? editContent : selectedDocument.content;
    return text.length;
  }, [selectedDocument, editContent, isEditing]);

  const handleCreateDraft = useCallback(() => {
    setDraftForm({ title: '', content: '' });
  }, []);

  const handleSubmitDraft = useCallback(() => {
    if (!draftForm || !draftForm.title.trim()) return;
    createDraftMutation.mutate({
      title: draftForm.title.trim(),
      content: draftForm.content.trim() || 'Untitled draft',
    });
  }, [draftForm, createDraftMutation]);

  const handleCancelDraft = useCallback(() => {
    setDraftForm(null);
  }, []);

  const handleToggleDraft = useCallback((artifactId: string) => {
    setExpandedDraft(expandedDraft === artifactId ? null : artifactId);
  }, [expandedDraft]);

  const promoteDraft = useCallback((artifactId: string) => {
    promoteMutation.mutate(artifactId);
  }, [promoteMutation]);

  const continueDraftAction = useCallback((artifactId: string) => {
    continueMutation.mutate(artifactId);
  }, [continueMutation]);

  const alternateVariantAction = useCallback((artifactId: string) => {
    alternateMutation.mutate(artifactId);
  }, [alternateMutation]);

  const handleGenerateDraftForm = useCallback(() => {
    setDraftFormAI({ title: '', brief: '', mode: 'ai' });
  }, []);

  const handleGenerateDraft = useCallback(async () => {
    if (!draftFormAI || !draftFormAI.title.trim() || !draftFormAI.brief.trim()) return;
    generateDraftMutation.mutate({
      title: draftFormAI.title.trim(),
      brief: draftFormAI.brief.trim(),
    });
  }, [draftFormAI, generateDraftMutation]);

  return {
    projectId,
    selectedDocumentId,
    isDark,
    manuscriptDocuments,
    draftArtifacts,
    revisionSuggestions,
    openSuggestions,
    selectedDocument,
    isEditing,
    editContent,
    draftForm,
    expandedDraft,
    manuscriptQueryLoading: manuscriptQuery.isLoading,
    draftsQueryLoading: draftsQuery.isLoading,
    wordCount,
    charCount,
    setSelectedDocumentId,
    setIsEditing,
    setEditContent,
    setDraftForm,
    setExpandedDraft,
    handleEdit,
    handleCancel,
    handleSave,
    handleSuggestionAccept,
    handleSuggestionReject,
    handleCreateDraft,
    handleSubmitDraft,
    handleCancelDraft,
    handleToggleDraft,
    createDraftPending: createDraftMutation.isPending,
    promotePending: promoteMutation.isPending,
    promoteDraft,
    continuePending: continueMutation.isPending,
    alternatePending: alternateMutation.isPending,
    continueDraftAction,
    alternateVariantAction,
    draftFormAI,
    pendingDrafts,
    setDraftFormAI,
    handleGenerateDraftForm,
    handleGenerateDraft,
    generateDraftPending: generateDraftMutation.isPending,
  };
}
