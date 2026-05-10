import { useCallback, useState } from 'react';
import { useParams } from 'react-router-dom';
import { FileText, BookOpen, Code } from 'lucide-react';
import { AidsPanel } from '../components/aids/AidsPanel';
import { ManuscriptList } from '../components/writing/ManuscriptList';
import { DraftList } from '../components/writing/DraftList';
import { DraftForm } from '../components/writing/DraftForm';
import { ManuscriptEditor } from '../components/writing/ManuscriptEditor';
import { useWritingView } from '../hooks/useWritingView';
import { useManuscriptAssist } from '../hooks/useManuscriptAssist';
import { useSettingsStore } from '../stores/settingsStore';
import { useToastStore } from '../stores/toastStore';
import { useThemeStore } from '../stores/themeStore';
import { resolveEffectiveMode } from '../theme/theme';
import type { ManuscriptAssistKind } from '../types/manuscriptAssist';
import type { RevisionSuggestion } from '../types/aids';

const ASSIST_LABELS: Record<ManuscriptAssistKind, string> = {
  developmental_review: 'Developmental review',
  canon_check: 'Canon check',
  character_voice_check: 'Character voice check',
  pacing_review: 'Pacing review',
  theme_review: 'Theme review',
  line_edit_selection: 'Line edit selection',
  expand_sensory_sight: 'Expand: sight & color',
  expand_sensory_sound: 'Expand: sound & rhythm',
  expand_sensory_smell: 'Expand: smell & atmosphere',
  expand_sensory_texture: 'Expand: touch & texture',
  expand_sensory_taste: 'Expand: taste & flavor',
  expand_metaphor: 'Expand: metaphor & simile',
  expand_show_dont_tell: 'Expand: show don\'t tell',
  compress_selection: 'Compress selection',
  rewrite_selection_same_voice: 'Rewrite selection (same voice)',
  alternate_selection: 'Alternate selection',
  continue_from_selection: 'Continue from selection',
  fork_from_selection: 'Fork from selection',
  generate_next_chapter: 'Generate next chapter',
  generate_alternate_chapter: 'Generate alternate chapter',
  continuity_repair: 'Continuity repair',
  ai_generate_draft: 'AI generate draft',
};

export function WritingView() {
  const { projectId, chapterId } = useParams<{ projectId: string; chapterId: string }>();
  const { mode, _systemTick } = useThemeStore();
  void _systemTick;
  const isDark = resolveEffectiveMode(mode) === 'dark';
  const { outlineDetail } = useSettingsStore();

  const [scrollTarget, setScrollTarget] = useState<{ documentId: string; lineIndex: number } | null>(null);

  const handleOutlineNavigate = useCallback((documentId: string, lineIndex: number) => {
    setScrollTarget({ documentId, lineIndex });
  }, []);

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
    draftFormAI,
    pendingDrafts,
    setDraftFormAI,
    handleGenerateDraftForm,
    handleGenerateDraft,
    generateDraftPending,
  } = useWritingView(isDark);
  const addToast = useToastStore((state) => state.addToast);
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

  const hasChapter = !!chapterId;
  const includeParagraphs = outlineDetail === 'detailed';

  return (
    <div className={`h-full grid gap-4 ${hasChapter ? 'grid-cols-1' : 'xl:grid-cols-[18rem_minmax(0,1fr)_20rem]'}`}>
      {hasChapter ? null : (
      <section
        aria-label="Manuscript and drafts panel"
        className={`min-h-0 rounded-xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} shadow-card flex flex-col overflow-hidden`}
      >
        <div className={`flex items-center gap-2 px-4 py-3 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
          <FileText className={`w-4 h-4 ${isDark ? 'text-blue-400' : 'text-blue-500'}`} />
          <h3 className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Manuscripts</h3>
        </div>

        <div className="flex-1 overflow-y-auto p-3">
          <ManuscriptList
            documents={manuscriptDocuments}
            selectedDocumentId={selectedDocumentId}
            isLoading={manuscriptQueryLoading}
            includeParagraphs={includeParagraphs}
            onSelect={(id) => {
              setSelectedDocumentId(id);
              setIsEditing(false);
              setEditContent('');
            }}
            onNavigate={handleOutlineNavigate}
            isDark={isDark}
          />
        </div>

        <div className={`border-t ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
          <div className={`px-4 py-2.5 border-t ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
            <div className="flex items-center gap-2 mb-2 text-body">
              <Code className="w-3.5 h-3.5" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-body">Drafts</h3>
              <span className="ml-auto text-xs text-muted">({draftArtifacts.length})</span>
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
              onGenerateAIDraft={handleGenerateDraftForm}
            />

            {Object.keys(pendingDrafts).length > 0 && (
              <div className={`text-[10px] px-1.5 py-1 rounded ${isDark ? 'bg-amber-900/30 text-amber-400' : 'bg-amber-50 text-amber-600'}`}>
                {Object.values(pendingDrafts).map((pd) => (
                  <div key={pd.assistId} className="flex items-center gap-1">
                    <span className="inline-block w-1 h-1 rounded-full bg-amber-500 animate-pulse"></span>
                    {pd.error ? (
                      <span className="text-red-400">{pd.title} - {pd.error}</span>
                    ) : (
                      <span>{pd.title}...</span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {draftFormAI && (
              <DraftForm
                title={draftFormAI.title}
                content=""
                brief={draftFormAI.brief}
                isPending={generateDraftPending}
                mode="ai"
                onTitleChange={(title) => setDraftFormAI({ ...draftFormAI, title })}
                onContentChange={() => {}}
                onBriefChange={(brief) => setDraftFormAI({ ...draftFormAI, brief })}
                onSubmit={handleGenerateDraft}
                onCancel={() => setDraftFormAI(null)}
                isDark={isDark}
              />
            )}
          </div>
        </div>
      </section>)}

      <section
        aria-label="Manuscript editor panel"
        className={`min-h-0 rounded-xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} shadow-card flex flex-col overflow-hidden`}
      >
        <div className={`px-4 py-2.5 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'} flex items-center justify-between`}>
          <h2 className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Editor</h2>
          <span className="text-xs text-muted">{selectedDocument ? selectedDocument.title : 'No manuscript selected'}</span>
        </div>
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
              const label = ASSIST_LABELS[kind] ?? kind;
              if (kind === 'fork_from_selection') {
                void assist.submitAssist(kind, instruction, { create_draft_artifact: true });
                addToast(`${label} submitted`, 'info');
                return;
              }
              void assist.submitAssist(kind, instruction);
              addToast(`${label} submitted`, 'info');
            }}
            scrollTarget={scrollTarget?.documentId === selectedDocument.document_id ? scrollTarget?.lineIndex : null}
            isDark={isDark}
          />
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <BookOpen className={`w-10 h-10 mx-auto mb-3 ${isDark ? 'text-slate-700' : 'text-slate-300'}`} />
              <p className="text-sm text-muted">Select a manuscript from the sidebar</p>
            </div>
          </div>
        )}
      </section>

      {hasChapter ? null : (
      <section aria-label="Revision suggestions panel" className="min-h-0">
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
          onSuggestionArchive={(suggestionId) => {
            const llm = assist.llmSuggestions.find((item) => item.suggestion_id === suggestionId);
            if (llm) {
              void assist.archiveSuggestion(suggestionId);
              return;
            }
          }}
        />
      </section>)}
    </div>
  );
}
