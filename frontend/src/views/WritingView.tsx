import { useParams } from 'react-router-dom';
import { FileText, BookOpen, Code } from 'lucide-react';
import { AidsPanel } from '../components/aids/AidsPanel';
import { ManuscriptList } from '../components/writing/ManuscriptList';
import { DraftList } from '../components/writing/DraftList';
import { ManuscriptEditor } from '../components/writing/ManuscriptEditor';
import { useWritingView } from '../hooks/useWritingView';
import { useManuscriptAssist } from '../hooks/useManuscriptAssist';
import { useThemeStore } from '../stores/themeStore';
import type { RevisionSuggestion } from '../types/aids';

export function WritingView() {
  const { projectId } = useParams<{ projectId: string }>();
  const { mode } = useThemeStore();
  const isDark = mode === 'dark';

  const {
    manuscriptDocuments,
    draftArtifacts,
    revisionSuggestions,
    openSuggestions,
    selectedDocumentId,
    selectedDocument,
    isEditing,
    editContent,
    draftForm,
    expandedDraft,
    manuscriptQueryLoading,
    draftsQueryLoading,
    wordCount,
    charCount,
    setSelectedDocumentId,
    setIsEditing,
    setEditContent,
    setDraftForm,
    handleEdit,
    handleCancel,
    handleSave,
    handleSuggestionAccept,
    handleSuggestionReject,
    handleCreateDraft,
    handleSubmitDraft,
    handleCancelDraft,
    handleToggleDraft,
    promotePending,
    promoteDraft,
    continuePending,
    alternatePending,
    continueDraftAction,
    alternateVariantAction,
    createDraftPending,
  } = useWritingView(isDark);
  const assist = useManuscriptAssist({
    projectId,
    documentId: selectedDocument?.document_id ?? null,
    documentVersion: selectedDocument?.version,
    content: isEditing ? editContent : selectedDocument?.content,
  });

  const mergedSuggestions: RevisionSuggestion[] = [
    ...revisionSuggestions,
    ...assist.llmSuggestions.map((item) => ({
      suggestion_id: item.suggestion_id,
      project_id: item.project_id,
      target_document_id: item.target_document_id,
      source_text: item.source_text,
      proposed_text: item.proposed_text,
      rationale: item.rationale,
      source_context: item.source_context,
      status:
        item.status === 'ARCHIVED'
          ? 'REJECTED'
          : item.status,
    })),
  ];

  if (!projectId) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-slate-500">No project selected</p>
      </div>
    );
  }

  return (
    <div className="h-full flex gap-4">
      <div className={`w-72 flex-shrink-0 rounded-xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} shadow-card flex flex-col overflow-hidden`}>
        <div className={`flex items-center gap-2 px-4 py-3 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
          <FileText className={`w-4 h-4 ${isDark ? 'text-blue-400' : 'text-blue-500'}`} />
          <h3 className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Manuscripts</h3>
        </div>

        <div className="flex-1 overflow-y-auto p-3">
          <ManuscriptList
            documents={manuscriptDocuments}
            selectedDocumentId={selectedDocumentId}
            isLoading={manuscriptQueryLoading}
            onSelect={(id) => {
              setSelectedDocumentId(id);
              setIsEditing(false);
              setEditContent('');
            }}
            isDark={isDark}
          />
        </div>

        <div className={`border-t ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
          <div className={`px-4 py-2.5 border-t ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
            <div className={`flex items-center gap-2 mb-2 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              <Code className="w-3.5 h-3.5" />
              <h3 className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Drafts</h3>
              <span className={`ml-auto text-xs ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>({draftArtifacts.length})</span>
            </div>
          </div>

          <div className="px-3 pb-3 space-y-1.5 max-h-40 overflow-y-auto">
            <DraftList
              artifacts={draftArtifacts}
              expandedDraft={expandedDraft}
              draftForm={draftForm}
              isPending={createDraftPending}
              promotePending={promotePending}
              continuePending={continuePending}
              alternatePending={alternatePending}
              isLoading={draftsQueryLoading}
              isDark={isDark}
              onCreateDraft={handleCreateDraft}
              onSubmitDraft={handleSubmitDraft}
              onCancelDraft={handleCancelDraft}
              onTitleChange={(title) => setDraftForm(draftForm ? { ...draftForm, title } : null)}
              onContentChange={(content) => setDraftForm(draftForm ? { ...draftForm, content } : null)}
              onToggleDraft={handleToggleDraft}
              onPromoteDraft={promoteDraft}
              onContinueDraft={continueDraftAction}
              onAlternateVariant={alternateVariantAction}
            />
          </div>
        </div>
      </div>

      <div className={`flex-1 rounded-xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} shadow-card flex flex-col overflow-hidden`}>
        {selectedDocument ? (
          <ManuscriptEditor
            document={selectedDocument}
            isEditing={isEditing}
            editContent={editContent}
            wordCount={wordCount}
            charCount={charCount}
            openSuggestions={openSuggestions}
            onEdit={handleEdit}
            onSave={handleSave}
            onCancel={handleCancel}
            onContentChange={setEditContent}
            onSelectionChange={assist.setSelectionFromEditor}
            selectedRange={assist.selectedRange}
            onAssistRequest={(kind, instruction) => {
              if (kind === 'fork_from_selection') {
                void assist.submitAssist(kind, instruction, { create_draft_artifact: true });
                return;
              }
              void assist.submitAssist(kind, instruction);
            }}
            isDark={isDark}
          />
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <BookOpen className={`w-10 h-10 mx-auto mb-3 ${isDark ? 'text-slate-700' : 'text-slate-300'}`} />
              <p className={`text-sm ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>Select a manuscript from the sidebar</p>
            </div>
          </div>
        )}
      </div>

      <AidsPanel
        projectId={projectId}
        suggestions={mergedSuggestions}
        onSuggestionAccept={(suggestionId) => {
          const llm = assist.llmSuggestions.find((item) => item.suggestion_id === suggestionId);
          if (llm) {
            void assist.applySuggestion(suggestionId);
            return;
          }
          void handleSuggestionAccept(suggestionId);
        }}
        onSuggestionReject={(suggestionId) => {
          const llm = assist.llmSuggestions.find((item) => item.suggestion_id === suggestionId);
          if (llm) {
            void assist.rejectSuggestion(suggestionId);
            return;
          }
          void handleSuggestionReject(suggestionId);
        }}
      />
    </div>
  );
}
