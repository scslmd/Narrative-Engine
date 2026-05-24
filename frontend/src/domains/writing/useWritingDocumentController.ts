import { useCallback, useEffect, useMemo, useState } from 'react';
import { useQueries, useQueryClient } from '@tanstack/react-query';
import { useRevisionHistoryStore } from '../../stores/revisionHistoryStore';
import {
  continueDraft,
  createAlternateVariant,
  createDraftArtifact,
  createRevisionSuggestion,
  getDraftArtifact,
  getDraftArtifacts,
  getManuscriptDocument,
  getManuscriptDocuments,
  getRevisionSuggestion,
  getRevisionSuggestions,
  promoteDraftToManuscript,
  triggerManuscriptReview,
  updateManuscriptContent,
} from '../../services/drafting';
import { toast } from '../../lib/toast';
import type { RevisionSuggestion } from '../../types/aids';
import type { DraftArtifact, ManuscriptDocument } from '../../types/drafting';

export interface DraftFormState {
  title: string;
  content: string;
}

interface DocumentState {
  selectedDocumentId: string | null;
  isEditing: boolean;
  editContent: string;
  draftForm: DraftFormState | null;
  expandedDraft: string | null;
}

const initialState: DocumentState = {
  selectedDocumentId: null,
  isEditing: false,
  editContent: '',
  draftForm: null,
  expandedDraft: null,
};

interface UseWritingDocumentControllerArgs {
  projectId?: string;
  chapterId?: string;
}

export function useWritingDocumentController({
  projectId,
  chapterId,
}: UseWritingDocumentControllerArgs) {
  const [state, setState] = useState<DocumentState>(initialState);
  const queryClient = useQueryClient();

  const setSelectedDocumentId = useCallback((id: string | null) => setState(s => ({ ...s, selectedDocumentId: id })), []);
  const setIsEditing = useCallback((editing: boolean) => setState(s => ({ ...s, isEditing: editing })), []);
  const setEditContent = useCallback((content: string) => setState(s => ({ ...s, editContent: content })), []);
  const setDraftForm = useCallback((form: DraftFormState | null) => setState(s => ({ ...s, draftForm: form })), []);
  const setExpandedDraft = useCallback((id: string | null) => setState(s => ({ ...s, expandedDraft: id })), []);

  const {
    selectedDocumentId,
    isEditing,
    editContent,
    draftForm,
    expandedDraft,
  } = state;

  const queries = useQueries({
    queries: [
      {
        queryKey: ['manuscript-documents', projectId],
        queryFn: () => getManuscriptDocuments(projectId!),
        enabled: !!projectId,
      },
      {
        queryKey: ['draft-artifacts', projectId],
        queryFn: () => getDraftArtifacts(projectId!),
        enabled: !!projectId,
      },
      {
        queryKey: ['revision-suggestions', projectId, selectedDocumentId ?? 'all'],
        queryFn: () => getRevisionSuggestions(projectId!, selectedDocumentId ?? undefined),
        enabled: !!projectId && !!selectedDocumentId,
      },
    ],
  });
  const [manuscriptDocumentsQuery, draftArtifactsQuery, revisionSuggestionsQuery] = queries;
  const manuscriptDocumentsData = manuscriptDocumentsQuery.data as ManuscriptDocument[] | undefined;
  const draftArtifactsData = draftArtifactsQuery.data as DraftArtifact[] | undefined;
  const revisionSuggestionsData = revisionSuggestionsQuery.data as RevisionSuggestion[] | undefined;

  const manuscriptDocuments = useMemo(
    () => manuscriptDocumentsData ?? [],
    [manuscriptDocumentsData],
  );
  const draftArtifacts = draftArtifactsData ?? [];
  const revisionSuggestions = useMemo(
    () => revisionSuggestionsData ?? [],
    [revisionSuggestionsData],
  );
  const openSuggestions = useMemo(
    () => revisionSuggestions.filter((s) => s.status === 'REQUESTED' || s.status === 'PENDING'),
    [revisionSuggestions],
  );

const mutations = useMemo(() => ({
      createDraft: async (data: { title: string; content: string }) => {
        await createDraftArtifact({
          artifact_id: `draft-${Date.now()}`,
          project_id: projectId!,
          title: data.title,
          content: data.content,
        });
        await queryClient.invalidateQueries({ queryKey: ['draft-artifacts', projectId] });
        setDraftForm(null);
        toast.success('Draft created');
      },
      promote: async (artifactId: string) => {
        await promoteDraftToManuscript({
          project_id: projectId!,
          document_id: `doc-${Date.now()}`,
          draft_artifact_id: artifactId,
        });
        await queryClient.invalidateQueries({ queryKey: ['draft-artifacts', projectId] });
        await queryClient.invalidateQueries({ queryKey: ['manuscript-documents', projectId] });
        setExpandedDraft(null);
        toast.success('Draft promoted to manuscript');
      },
      continue: async (artifactId: string) => {
        await continueDraft(artifactId, projectId!);
        await queryClient.invalidateQueries({ queryKey: ['draft-artifacts', projectId] });
        toast.success('Draft continued');
      },
      alternate: async (artifactId: string) => {
        await createAlternateVariant(artifactId, projectId!);
        await queryClient.invalidateQueries({ queryKey: ['draft-artifacts', projectId] });
        toast.success('Alternate variant created');
      },
    }), [projectId, queryClient, setDraftForm, setExpandedDraft]);

  const [createDraftPending, setCreateDraftPending] = useState(false);
  const [promotePending, setPromotePending] = useState(false);
  const [continuePending, setContinuePending] = useState(false);
  const [alternatePending, setAlternatePending] = useState(false);

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
  }, [manuscriptDocuments, chapterId, selectedDocumentId, setSelectedDocumentId]);

  const selectedDocument = manuscriptDocuments.find(
    (doc: ManuscriptDocument) => doc.document_id === selectedDocumentId,
  );

  useEffect(() => {
    if (!selectedDocumentId || !projectId) return;
    void getManuscriptDocument(selectedDocumentId, projectId);
  }, [selectedDocumentId, projectId]);

  const handleEdit = useCallback(() => {
    if (selectedDocument) {
      setEditContent(selectedDocument.content);
      setIsEditing(true);
    }
  }, [selectedDocument, setEditContent, setIsEditing]);

  const handleCancel = useCallback(() => {
    setIsEditing(false);
    setEditContent('');
  }, [setIsEditing, setEditContent]);

  const handleSave = useCallback(async () => {
    if (!selectedDocumentId || !projectId) return;
    try {
      const prevContent = selectedDocument ? selectedDocument.content : editContent;
      await updateManuscriptContent(selectedDocumentId, projectId, editContent);
      await queryClient.invalidateQueries({ queryKey: ['manuscript-documents', projectId] });
      await queryClient.invalidateQueries({
        queryKey: ['revision-suggestions', projectId, selectedDocumentId],
      });

      useRevisionHistoryStore.getState().addEntry({
        documentId: selectedDocumentId,
        version: selectedDocument?.version ?? 0,
        content: prevContent,
        timestamp: Date.now(),
      });

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
  }, [selectedDocumentId, projectId, editContent, selectedDocument, queryClient, setIsEditing, setEditContent]);

  const handleSuggestionAccept = useCallback(
    async (suggestionId: string) => {
      if (!selectedDocument || !projectId) return;
      const suggestion =
        revisionSuggestions.find((s) => s.suggestion_id === suggestionId) ??
        (await getRevisionSuggestion(suggestionId, projectId));
      if (!suggestion) return;

      const updatedContent = selectedDocument.content.replace(
        suggestion.source_text,
        suggestion.proposed_text,
      );

      try {
        await updateManuscriptContent(selectedDocument.document_id, projectId, updatedContent);
        await queryClient.invalidateQueries({ queryKey: ['manuscript-documents', projectId] });
        await queryClient.invalidateQueries({
          queryKey: ['revision-suggestions', projectId, selectedDocument.document_id],
        });
        if (isEditing) {
          setEditContent(updatedContent);
        }
        toast.success('Suggestion applied');
      } catch {
        toast.error('Failed to apply suggestion');
      }
    },
    [selectedDocument, projectId, revisionSuggestions, queryClient, isEditing, setEditContent],
  );

  const handleSuggestionReject = useCallback(
    async (suggestionId: string) => {
      if (!selectedDocumentId || !projectId) return;
      const suggestion =
        revisionSuggestions.find((s) => s.suggestion_id === suggestionId) ??
        (await getRevisionSuggestion(suggestionId, projectId));
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
        await queryClient.invalidateQueries({
          queryKey: ['revision-suggestions', projectId, selectedDocumentId],
        });
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
  }, [setDraftForm]);

  const handleSubmitDraft = useCallback(async () => {
    if (!draftForm || !draftForm.title.trim()) return;
    setCreateDraftPending(true);
    try {
      await mutations.createDraft({
        title: draftForm.title.trim(),
        content: draftForm.content.trim() || 'Untitled draft',
      });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create draft');
    } finally {
      setCreateDraftPending(false);
    }
  }, [draftForm, mutations, setCreateDraftPending]);

  const handleCancelDraft = useCallback(() => {
    setDraftForm(null);
  }, [setDraftForm]);

  const handleToggleDraft = useCallback(
    (artifactId: string) => {
      if (projectId) {
        void getDraftArtifact(artifactId, projectId);
      }
      setExpandedDraft(expandedDraft === artifactId ? null : artifactId);
    },
    [expandedDraft, projectId, setExpandedDraft],
  );

  const promoteDraft = useCallback(async (artifactId: string) => {
    setPromotePending(true);
    try {
      await mutations.promote(artifactId);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to promote draft');
    } finally {
      setPromotePending(false);
    }
  }, [mutations, setPromotePending]);

  const continueDraftAction = useCallback(async (artifactId: string) => {
    setContinuePending(true);
    try {
      await mutations.continue(artifactId);
    } catch (err) {
      if (err instanceof Error && err.message.includes('404')) {
        toast.error('No prior content to continue from');
      } else {
        toast.error(err instanceof Error ? err.message : 'Failed to continue draft');
      }
    } finally {
      setContinuePending(false);
    }
  }, [mutations, setContinuePending]);

  const handleUndo = useCallback(() => {
    if (!selectedDocumentId) return;
    const history = useRevisionHistoryStore.getState().getHistory(selectedDocumentId);
    if (history.length > 0) {
      setEditContent(history[0].content);
      setIsEditing(true);
    }
  }, [selectedDocumentId, setEditContent, setIsEditing]);

  const revisionHistory = useMemo(() => {
    if (!selectedDocumentId) return [];
    return useRevisionHistoryStore.getState().getHistory(selectedDocumentId);
  }, [selectedDocumentId, manuscriptDocuments]);

  const alternateVariantAction = useCallback(async (artifactId: string) => {
    setAlternatePending(true);
    try {
      await mutations.alternate(artifactId);
    } catch (err) {
      if (err instanceof Error && err.message.includes('404')) {
        toast.error('No prior content to create variant from');
      } else {
        toast.error(err instanceof Error ? err.message : 'Failed to create alternate variant');
      }
    } finally {
      setAlternatePending(false);
    }
  }, [mutations, setAlternatePending]);

  return {
    selectedDocumentId,
    setSelectedDocumentId,
    isEditing,
    setIsEditing,
    editContent,
    setEditContent,
    draftForm,
    setDraftForm,
    expandedDraft,
    setExpandedDraft,
    manuscriptDocuments,
    draftArtifacts,
    revisionSuggestions,
    openSuggestions,
    selectedDocument,
    manuscriptQueryLoading: manuscriptDocumentsQuery.isLoading,
    draftsQueryLoading: draftArtifactsQuery.isLoading,
    wordCount,
    charCount,
    handleEdit,
    handleCancel,
    handleSave,
    handleSuggestionAccept,
    handleSuggestionReject,
    handleCreateDraft,
    handleSubmitDraft,
    handleCancelDraft,
    handleToggleDraft,
    createDraftPending,
    promotePending,
    promoteDraft,
    continuePending,
    alternatePending,
    continueDraftAction,
    alternateVariantAction,
    handleUndo,
    revisionHistory,
  };
}
