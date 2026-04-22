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
  isLoading: boolean;
  isDark: boolean;
  onCreateDraft: () => void;
  onSubmitDraft: () => void;
  onCancelDraft: () => void;
  onTitleChange: (title: string) => void;
  onContentChange: (content: string) => void;
  onToggleDraft: (id: string) => void;
  onPromoteDraft: (id: string) => void;
}

export function DraftList({
  artifacts,
  expandedDraft,
  draftForm,
  isPending,
  promotePending,
  isLoading,
  isDark,
  onCreateDraft,
  onSubmitDraft,
  onCancelDraft,
  onTitleChange,
  onContentChange,
  onToggleDraft,
  onPromoteDraft,
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
        <button
          onClick={onCreateDraft}
          className="text-xs mt-1.5 text-indigo-500 hover:text-indigo-400 font-medium"
        >
          + New Draft
        </button>
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
          isDark={isDark}
        />
      ))}
      {!draftForm && (
        <button
          onClick={onCreateDraft}
          className={`w-full text-xs py-1.5 rounded border border-dashed transition-colors ${isDark ? 'border-slate-700 text-slate-500 hover:text-slate-300 hover:border-slate-600' : 'border-slate-300 text-slate-400 hover:text-slate-600 hover:border-slate-400'}`}
        >
          <Plus className="w-3 h-3 inline-block mr-1" />
          New Draft
        </button>
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
