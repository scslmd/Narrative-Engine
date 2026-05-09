import { useParams } from 'react-router-dom';
import {
  useAssistController,
  type DraftFormAIState,
  type PendingDraftInfo,
} from '../domains/writing/useAssistController';
import {
  useWritingDocumentController,
  type DraftFormState,
} from '../domains/writing/useWritingDocumentController';
import type { RevisionSuggestion } from '../types/aids';
import type { DraftArtifact, ManuscriptDocument } from '../types/drafting';

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
  const writingController = useWritingDocumentController({ projectId, chapterId });
  const assistController = useAssistController({
    projectId,
    selectedDocumentId: writingController.selectedDocumentId,
  });

  return {
    projectId,
    selectedDocumentId: writingController.selectedDocumentId,
    isDark,
    manuscriptDocuments: writingController.manuscriptDocuments,
    draftArtifacts: writingController.draftArtifacts,
    revisionSuggestions: writingController.revisionSuggestions,
    openSuggestions: writingController.openSuggestions,
    selectedDocument: writingController.selectedDocument,
    isEditing: writingController.isEditing,
    editContent: writingController.editContent,
    draftForm: writingController.draftForm,
    expandedDraft: writingController.expandedDraft,
    manuscriptQueryLoading: writingController.manuscriptQueryLoading,
    draftsQueryLoading: writingController.draftsQueryLoading,
    wordCount: writingController.wordCount,
    charCount: writingController.charCount,
    setSelectedDocumentId: writingController.setSelectedDocumentId,
    setIsEditing: writingController.setIsEditing,
    setEditContent: writingController.setEditContent,
    setDraftForm: writingController.setDraftForm,
    setExpandedDraft: writingController.setExpandedDraft,
    handleEdit: writingController.handleEdit,
    handleCancel: writingController.handleCancel,
    handleSave: writingController.handleSave,
    handleSuggestionAccept: writingController.handleSuggestionAccept,
    handleSuggestionReject: writingController.handleSuggestionReject,
    handleCreateDraft: writingController.handleCreateDraft,
    handleSubmitDraft: writingController.handleSubmitDraft,
    handleCancelDraft: writingController.handleCancelDraft,
    handleToggleDraft: writingController.handleToggleDraft,
    createDraftPending: writingController.createDraftPending,
    promotePending: writingController.promotePending,
    promoteDraft: writingController.promoteDraft,
    continuePending: writingController.continuePending,
    alternatePending: writingController.alternatePending,
    continueDraftAction: writingController.continueDraftAction,
    alternateVariantAction: writingController.alternateVariantAction,
    draftFormAI: assistController.draftFormAI,
    pendingDrafts: assistController.pendingDrafts,
    setDraftFormAI: assistController.setDraftFormAI,
    handleGenerateDraftForm: assistController.handleGenerateDraftForm,
    handleGenerateDraft: assistController.handleGenerateDraft,
    generateDraftPending: assistController.generateDraftPending,
  };
}
