import { AidsPanel } from '../aids/AidsPanel';
import { useWritingDocumentController } from '../../domains/writing/useWritingDocumentController';
import { useManuscriptAssist } from '../../hooks/useManuscriptAssist';
import { useMergedSuggestions } from '../../hooks/useMergedSuggestions';

interface StudioSuggestionsPanelProps {
  projectId: string;
}

export function StudioSuggestionsPanel({ projectId }: StudioSuggestionsPanelProps) {
  const writingController = useWritingDocumentController({
    projectId,
    chapterId: undefined,
  });

  const selectedDocument = writingController.selectedDocument;

  const assist = useManuscriptAssist({
    projectId,
    documentId: selectedDocument?.document_id ?? null,
    documentVersion: selectedDocument?.version,
    content: writingController.isEditing
      ? writingController.editContent
      : selectedDocument?.content,
  });

  const merged = useMergedSuggestions({
    revisionSuggestions: writingController.revisionSuggestions,
    llmSuggestions: assist.llmSuggestions,
    onRevisionAccept: writingController.handleSuggestionAccept,
    onRevisionReject: writingController.handleSuggestionReject,
    onLlmAccept: assist.applySuggestion,
    onLlmReject: assist.rejectSuggestion,
    onLlmArchive: assist.archiveSuggestion,
  });

  return (
    <AidsPanel
      projectId={projectId}
      suggestions={merged.suggestions}
      onSuggestionAccept={(suggestionId) => void merged.handleSuggestionAccept(suggestionId)}
      onSuggestionReject={(suggestionId) => void merged.handleSuggestionReject(suggestionId)}
      onSuggestionArchive={(suggestionId) => void merged.handleSuggestionArchive(suggestionId)}
    />
  );
}
