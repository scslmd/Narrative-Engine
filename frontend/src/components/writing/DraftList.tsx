import { Plus } from 'lucide-react';
import { DraftArtifactCard } from './DraftArtifactCard';
import { DraftForm } from './DraftForm';
import type { DraftArtifact } from '../../types/drafting';

interface DraftListProps {
  artifacts: DraftArtifact[];
  expandedDraft: string | null;
  draftForm: { title: string; content: string } | null;
  isPending: boolean;
  promotePending: boolean;
  continuePending: boolean;
  alternatePending: boolean;
  isLoading: boolean;
  isDark: boolean;
  onCreateDraft: () => void;
  onSubmitDraft: () => void;
  onCancelDraft: () => void;
  onTitleChange: (title: string) => void;
  onContentChange: (content: string) => void;
  onToggleDraft: (id: string) => void;
  onPromoteDraft: (id: string) => void;
  onContinueDraft: (id: string) => void;
  onAlternateVariant: (id: string) => void;
  onGenerateAIDraft: () => void;
}

export function DraftList({
  artifacts,
  expandedDraft,
  draftForm,
  isPending,
  promotePending,
  continuePending,
  alternatePending,
  isLoading,
  isDark,
  onCreateDraft,
  onSubmitDraft,
  onCancelDraft,
  onTitleChange,
  onContentChange,
  onToggleDraft,
  onPromoteDraft,
  onContinueDraft,
  onAlternateVariant,
  onGenerateAIDraft,
}: DraftListProps) {
  if (isLoading) {
    return (
      <div className="space-y-1.5">
        {[1, 2].map((i) => (
          <div key={i} className={`h-10 rounded-md animate-shimmer ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`}></div>
        ))}
      </div>
    );
  }

  if (artifacts.length === 0 && !draftForm) {
    return (
      <div>
        <p className={`text-xs ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>No drafts yet</p>
        <div className="flex gap-1.5 mt-1.5">
          <button
            onClick={onCreateDraft}
            className="text-xs text-indigo-500 hover:text-indigo-400 font-medium"
          >
            + New Draft
          </button>
          <button
            onClick={onGenerateAIDraft}
            className="text-xs text-amber-500 hover:text-amber-400 font-medium"
            title="Generate with AI"
            aria-label="Generate with AI"
          >
            ⚡ AI
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {artifacts.map((artifact) => (
        <DraftArtifactCard
          key={artifact.artifact_id}
          artifact={artifact}
          isExpanded={expandedDraft === artifact.artifact_id}
          onToggle={() => onToggleDraft(artifact.artifact_id)}
          onPromote={() => onPromoteDraft(artifact.artifact_id)}
          promotePending={promotePending}
          onContinue={() => onContinueDraft(artifact.artifact_id)}
          continuePending={continuePending}
          onAlternateVariant={() => onAlternateVariant(artifact.artifact_id)}
          alternatePending={alternatePending}
          isDark={isDark}
        />
      ))}
      {!draftForm && (
        <div className="flex gap-1.5">
          <button
            onClick={onCreateDraft}
            className={`flex-1 text-xs py-1.5 rounded border border-dashed transition-colors ${isDark ? 'border-slate-700 text-slate-500 hover:text-slate-300 hover:border-slate-600' : 'border-slate-300 text-slate-400 hover:text-slate-600 hover:border-slate-400'}`}
          >
            <Plus className="w-3 h-3 inline-block mr-1" />
            New Draft
          </button>
          <button
            onClick={onGenerateAIDraft}
            className={`text-xs py-1.5 px-2 rounded border border-dashed transition-colors ${isDark ? 'border-amber-800 text-amber-500 hover:text-amber-400 hover:border-amber-700' : 'border-amber-300 text-amber-600 hover:text-amber-700 hover:border-amber-400'}`}
            title="Generate with AI"
            aria-label="Generate with AI"
          >
            ⚡ AI
          </button>
        </div>
      )}
      {draftForm && (
        <DraftForm
          title={draftForm.title}
          content={draftForm.content}
          isPending={isPending}
          onTitleChange={onTitleChange}
          onContentChange={onContentChange}
          onSubmit={onSubmitDraft}
          onCancel={onCancelDraft}
          isDark={isDark}
        />
      )}
    </div>
  );
}
