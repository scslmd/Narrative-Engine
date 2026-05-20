import { FileText, Plus, Sparkles } from 'lucide-react';
import { DraftList } from '../writing/DraftList';
import { DraftForm } from '../writing/DraftForm';
import { useWritingView } from '../../hooks/useWritingView';
import { useAssistController } from '../../domains/writing/useAssistController';
import { useThemeStore } from '../../stores/themeStore';
import { resolveEffectiveMode } from '../../theme/theme';

interface StudioDraftsPanelProps {
  projectId: string;
}

export function StudioDraftsPanel({ projectId }: StudioDraftsPanelProps) {
  const { mode: themeMode } = useThemeStore();
  const isDark = resolveEffectiveMode(themeMode) === 'dark';

  const {
    draftArtifacts,
    draftForm,
    expandedDraft,
    createDraftPending,
    promotePending,
    continuePending,
    alternatePending,
    draftsQueryLoading,
    handleCreateDraft,
    handleSubmitDraft,
    handleCancelDraft,
    handleToggleDraft,
    promoteDraft,
    continueDraftAction,
    alternateVariantAction,
    setDraftForm,
  } = useWritingView(isDark);

  const {
    draftFormAI,
    pendingDrafts,
    setDraftFormAI,
    handleGenerateDraftForm,
    handleGenerateDraft,
    generateDraftPending,
  } = useAssistController({
    projectId,
    selectedDocumentId: null,
  });

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200 dark:border-slate-700">
        <FileText className={`w-4 h-4 ${isDark ? 'text-blue-400' : 'text-blue-500'}`} />
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-900 dark:text-slate-100">
          Drafts
        </h3>
        <span className="ml-auto text-xs text-gray-500 dark:text-slate-400">
          ({draftArtifacts.length})
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {draftsQueryLoading ? (
          <div className="space-y-2">
            {[1, 2].map((i) => (
              <div key={i} className={`h-10 rounded-md animate-shimmer ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`} />
            ))}
          </div>
        ) : draftArtifacts.length === 0 && !draftForm && !draftFormAI ? (
          <div className="text-center py-8">
            <p className="text-sm text-gray-500 dark:text-slate-400 mb-3">No drafts yet</p>
            <div className="flex justify-center gap-2">
              <button
                onClick={handleCreateDraft}
                className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border transition-colors ${isDark ? 'border-slate-700 text-slate-300 hover:border-slate-600 hover:bg-slate-800' : 'border-slate-300 text-slate-600 hover:border-slate-400 hover:bg-slate-50'}`}
              >
                <Plus className="w-3.5 h-3.5" />
                New Draft
              </button>
              <button
                onClick={handleGenerateDraftForm}
                className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border transition-colors ${isDark ? 'border-amber-800 text-amber-400 hover:border-amber-700 hover:bg-slate-800' : 'border-amber-300 text-amber-600 hover:border-amber-400 hover:bg-amber-50'}`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                AI Generate
              </button>
            </div>
          </div>
        ) : (
          <>
            <DraftList
              artifacts={draftArtifacts}
              expandedDraft={expandedDraft}
              draftForm={draftForm}
              isPending={createDraftPending}
              promotePending={promotePending}
              continuePending={continuePending}
              alternatePending={alternatePending}
              isLoading={false}
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
              <div className={`text-xs px-2 py-2 rounded-md space-y-1 ${isDark ? 'bg-amber-900/20 text-amber-400 border border-amber-800/50' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}>
                {Object.values(pendingDrafts).map((pd) => (
                  <div key={pd.assistId} className="flex items-center gap-1.5">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                    {pd.error ? (
                      <span className="text-red-500">{pd.title} — {pd.error}</span>
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
          </>
        )}
      </div>
    </div>
  );
}
