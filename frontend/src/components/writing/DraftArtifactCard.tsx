const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'text-slate-400',
  PROPOSED: 'text-blue-400',
  CANONICAL: 'text-emerald-400',
  SUPERSEDED: 'text-slate-500',
  REJECTED: 'text-red-400',
  ARCHIVED: 'text-amber-400',
  PENDING: 'text-amber-400',
};

const STATUS_COLORS_LIGHT: Record<string, string> = {
  DRAFT: 'text-slate-500',
  PROPOSED: 'text-blue-600',
  CANONICAL: 'text-emerald-600',
  SUPERSEDED: 'text-slate-400',
  REJECTED: 'text-red-500',
  ARCHIVED: 'text-amber-600',
  PENDING: 'text-amber-500',
};

type ArtifactBase = {
  artifact_id: string;
  title: string;
  content: string;
  status: string;
};

interface DraftArtifactCardProps {
  artifact: ArtifactBase;
  isExpanded: boolean;
  onToggle: () => void;
  onPromote: () => void;
  promotePending: boolean;
  onContinue: () => void;
  continuePending: boolean;
  onAlternateVariant: () => void;
  alternatePending: boolean;
  isDark: boolean;
  generationError?: string | null;
  onRetry?: () => void;
  onErrorDismiss?: () => void;
}

export function DraftArtifactCard({
  artifact,
  isExpanded,
  onToggle,
  onPromote,
  promotePending,
  onContinue,
  continuePending,
  onAlternateVariant,
  alternatePending,
  isDark,
  generationError,
  onRetry,
  onErrorDismiss,
}: DraftArtifactCardProps) {
  const isLight = !isDark;
  const statusColor = isLight
    ? STATUS_COLORS_LIGHT[artifact.status] || STATUS_COLORS_LIGHT.DRAFT
    : STATUS_COLORS[artifact.status] || STATUS_COLORS.DRAFT;

  const hasContent = artifact.content && artifact.content.trim().length > 0;

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
          {artifact.status === 'PENDING' && !generationError && (
            <span className={`text-[10px] ml-2 ${isDark ? 'text-amber-400' : 'text-amber-600'}`}>
              <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-pulse mr-1"></span>
              Generating...
            </span>
          )}
        </div>
      </button>
      {generationError && (
        <div className={`mx-2 mt-2 p-2 rounded text-[10px] ${isDark ? 'bg-red-900/30 text-red-400 border border-red-800' : 'bg-red-50 text-red-600 border border-red-200'}`}>
          <p className="font-medium mb-1">Generation failed: {generationError}</p>
          <div className="flex gap-1.5">
            <button onClick={onRetry}
              className="text-[10px] px-2 py-0.5 rounded bg-red-600 text-white hover:bg-red-500 font-medium">
              Retry
            </button>
            <button onClick={onErrorDismiss}
              className={`text-[10px] px-2 py-0.5 rounded font-medium ${isDark ? 'bg-slate-700 text-slate-300 hover:text-white' : 'bg-slate-200 text-slate-600 hover:text-slate-800'}`}>
              Dismiss
            </button>
          </div>
        </div>
      )}
      {isExpanded && (
        <div className={`px-2 pb-2 space-y-1.5 border-t ${isDark ? 'border-slate-700' : 'border-slate-200'}`}>
          <p className="text-[10px] truncate text-subtle">
            {artifact.content.substring(0, 100)}{artifact.content.length > 100 ? '...' : ''}
          </p>
          {artifact.status !== 'PENDING' && <>
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
            <div className="flex gap-1.5">
              <button
                onClick={onContinue}
                disabled={!hasContent || continuePending}
                title={!hasContent ? 'No prior content to continue from' : undefined}
                className={`flex items-center gap-1 text-[10px] px-2 py-1 rounded font-medium disabled:opacity-40 ${isDark ? 'bg-sky-600 text-white hover:bg-sky-500' : 'bg-sky-500 text-white hover:bg-sky-400'}`}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
                Continue
              </button>
              <button
                onClick={onAlternateVariant}
                disabled={!hasContent || alternatePending}
                title={!hasContent ? 'No prior content to create variant from' : undefined}
                className={`flex items-center gap-1 text-[10px] px-2 py-1 rounded font-medium disabled:opacity-40 ${isDark ? 'bg-violet-600 text-white hover:bg-violet-500' : 'bg-violet-500 text-white hover:bg-violet-400'}`}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a4 4 0 008 0V7M4 9l4-2m0 0l4-2m-4 2V3" />
                </svg>
                Alternate
              </button>
            </div>
          </>}
        </div>
      )}
    </div>
  );
}
