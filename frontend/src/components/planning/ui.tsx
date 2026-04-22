import { useIsDark } from './hooks';

export function Section({
  title,
  count,
  children,
  actions,
}: {
  title: string;
  count?: number;
  children: React.ReactNode;
  actions?: React.ReactNode;
}) {
  const isDark = useIsDark();
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h3 className={`font-semibold text-sm uppercase tracking-wider ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
          {title}
          {count !== undefined && (
            <span className={`ml-2 font-normal ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>({count})</span>
          )}
        </h3>
        {actions}
      </div>
      {children}
    </div>
  );
}

export function EmptyState({ text }: { text: string }) {
  const isDark = useIsDark();
  return (
    <p className={`text-sm ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>{text}</p>
  );
}

export function WorkspaceStatus({
  title,
  detail,
  tone = 'neutral',
}: {
  title: string;
  detail: string;
  tone?: 'neutral' | 'error';
}) {
  const isDark = useIsDark();
  return (
    <div className="flex h-48 items-center justify-center">
      <div className={`max-w-sm rounded-lg border p-5 text-center ${
        tone === 'error'
          ? isDark ? 'border-red-900/50 bg-red-950/30 text-red-300' : 'border-red-200 bg-red-50 text-red-800'
          : isDark ? 'border-slate-800 bg-slate-900 text-slate-300' : 'border-slate-200 bg-white text-slate-700'
      }`}>
        <p className="text-sm font-semibold">{title}</p>
        <p className={`mt-1.5 text-xs ${tone === 'error' ? (isDark ? 'text-red-400/80' : 'text-red-600') : (isDark ? 'text-slate-500' : 'text-slate-500')}`}>{detail}</p>
      </div>
    </div>
  );
}
