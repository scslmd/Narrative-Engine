import { useCallback, useState } from 'react';
import { useParams } from 'react-router-dom';
import { FileText, BookOpen, Code } from 'lucide-react';
import { AidsPanel } from '../components/aids/AidsPanel';
import { ManuscriptList } from '../components/writing/ManuscriptList';
import { DraftList } from '../components/writing/DraftList';
import { DraftForm } from '../components/writing/DraftForm';
import { ManuscriptEditor } from '../components/writing/ManuscriptEditor';
import { ViewShell } from '../components/shell/ViewShell';
import { useWritingView } from '../hooks/useWritingView';
import { useManuscriptAssist } from '../hooks/useManuscriptAssist';
import { useMergedSuggestions } from '../hooks/useMergedSuggestions';
import { useSettingsStore } from '../stores/settingsStore';
import { useToastStore } from '../stores/toastStore';
import { useThemeStore } from '../stores/themeStore';
import { resolveEffectiveMode } from '../theme/theme';
import type { ManuscriptAssistKind } from '../types/manuscriptAssist';
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

interface WritingViewProps {
  embedded?: boolean;
  chapterSelectOptions?: Array<{ document_id: string; title: string }>;
  selectedChapterId?: string | null;
  isLoadingChapterSelect?: boolean;
  onChapterSelect?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
}

export function WritingView({ embedded = false, chapterSelectOptions, selectedChapterId, isLoadingChapterSelect, onChapterSelect }: WritingViewProps = {}) {
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

  const mergedSuggestions = useMergedSuggestions({
    revisionSuggestions,
    llmSuggestions: assist.llmSuggestions,
    onRevisionAccept: handleSuggestionAccept,
    onRevisionReject: handleSuggestionReject,
    onLlmAccept: assist.applySuggestion,
    onLlmReject: assist.rejectSuggestion,
    onLlmArchive: assist.archiveSuggestion,
  });

  if (!projectId) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-[var(--text-secondary)]">No project selected</p>
      </div>
    );
  }

  const hasChapter = !!chapterId;
  const includeParagraphs = outlineDetail === 'detailed';

  const showSidePanels = !embedded && !hasChapter;

  const innerContent = (
    <div className={`h-full grid gap-4 ${hasChapter ? 'grid-cols-1' : showSidePanels ? 'xl:grid-cols-[18rem_minmax(0,1fr)_20rem]' : 'grid-cols-1'}`}>
      {showSidePanels ? (
      <section
        aria-label="Manuscript and drafts panel"
        className="min-h-0 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card flex flex-col overflow-hidden"
      >
        <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border-primary)]">
          <FileText className="w-4 h-4 text-[var(--color-info)]" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Manuscripts</h3>
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

        <div className="border-t border-[var(--border-primary)]">
          <div className="px-4 py-2.5 border-t border-[var(--border-primary)]">
            <div className="flex items-center gap-2 mb-2 text-[var(--text-secondary)]">
              <Code className="w-3.5 h-3.5" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Drafts</h3>
              <span className="ml-auto text-xs text-[var(--text-tertiary)]">({draftArtifacts.length})</span>
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
              <div className="text-[10px] px-1.5 py-1 rounded bg-[var(--color-warning-subtle)] text-[var(--color-warning)]">
                {Object.values(pendingDrafts).map((pd) => (
                  <div key={pd.assistId} className="flex items-center gap-1">
                    <span className="inline-block w-1 h-1 rounded-full bg-[var(--color-warning)] animate-pulse"></span>
                    {pd.error ? (
                      <span className="text-[var(--color-danger)]">{pd.title} - {pd.error}</span>
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
      </section>) : null}

      <section
        aria-label="Manuscript editor panel"
        className={`min-h-0 flex flex-col overflow-hidden ${embedded ? '' : 'rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card'}`}
      >
        {!embedded && (
          <div className="px-4 py-2.5 border-b border-[var(--border-primary)] flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Editor</h2>
          </div>
        )}
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
            chapterSelectOptions={embedded ? chapterSelectOptions : undefined}
            selectedChapterId={embedded ? selectedChapterId : undefined}
            isLoadingChapterSelect={embedded ? isLoadingChapterSelect : undefined}
            onChapterSelect={embedded ? onChapterSelect : undefined}
          />
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <BookOpen className="w-10 h-10 mx-auto mb-3 text-[var(--text-tertiary)]" />
              <p className="text-sm text-[var(--text-secondary)]">Select a manuscript from the sidebar</p>
            </div>
          </div>
        )}
      </section>

      {showSidePanels ? (
      <section aria-label="Revision suggestions panel" className="min-h-0">
        <AidsPanel
          projectId={projectId}
          suggestions={mergedSuggestions.suggestions}
          onSuggestionAccept={(suggestionId) => void mergedSuggestions.handleSuggestionAccept(suggestionId)}
          onSuggestionReject={(suggestionId) => void mergedSuggestions.handleSuggestionReject(suggestionId)}
          onSuggestionArchive={(suggestionId) => void mergedSuggestions.handleSuggestionArchive(suggestionId)}
        />
      </section>) : null}
    </div>
  );

  if (embedded) {
    return innerContent;
  }

  return (
    <ViewShell title="Write" subtitle={projectId}>
      {innerContent}
    </ViewShell>
  );
}
