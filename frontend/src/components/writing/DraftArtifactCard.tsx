const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'text-slate-400',
  PROPOSED: 'text-blue-400',
  CANONICAL: 'text-emerald-400',
  SUPERSEDED: 'text-slate-500',
  REJECTED: 'text-red-400',
  ARCHIVED: 'text-amber-400',
};

const STATUS_COLORS_LIGHT: Record<string, string> = {
  DRAFT: 'text-slate-500',
  PROPOSED: 'text-blue-600',
  CANONICAL: 'text-emerald-600',
  SUPERSEDED: 'text-slate-400',
  REJECTED: 'text-red-500',
  ARCHIVED: 'text-amber-600',
};

interface DraftArtifactCardProps {
  artifact: {
    artifact_id: string;
    title: string;
    status: string;
    content: string;
  };
  isExpanded: boolean;
  onToggle: () => void;
  onPromote: () => void;
  promotePending: boolean;
  isDark: boolean;
}

export function DraftArtifactCard({ artifact, isExpanded, onToggle, onPromote, promotePending, isDark }: DraftArtifactCardProps) {
  const isLight = !isDark;
  const statusColor = isLight
    ? STATUS_COLORS_LIGHT[artifact.status] || STATUS_COLORS_LIGHT.DRAFT
    : STATUS_COLORS[artifact.status] || STATUS_COLORS.DRAFT;

  return (
    <div className={`rounded-md border transition-all duration-150 ${isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-slate-50 border-slate-200'}`}>
      <button
        onClick={onToggle}
        className="w-full text-left p-2"
      >
        <div className="flex items-center gap-1.5">
          <div className={`flex-1 font-medium text-xs truncate ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
            {artifact.title}
          </div>
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${isDark ? 'bg-slate-700' : 'bg-slate-200'} ${statusColor}`}>
            {artifact.status}
          </span>
        </div>
      </button>
      {isExpanded && (
        <div className={`px-2 pb-2 space-y-1.5 border-t ${isDark ? 'border-slate-700' : 'border-slate-200'}`}>
          <p className={`text-[10px] truncate ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
            {artifact.content.substring(0, 100)}{artifact.content.length > 100 ? '...' : ''}
          </p>
          <div className="flex gap-1.5">
            <button
              onClick={onPromote}
              disabled={promotePending}
              className="flex items-center gap-1 text-[10px] px-2 py-1 rounded bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-40 font-medium"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
              Promote
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
