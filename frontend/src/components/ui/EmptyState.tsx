import type { ReactNode } from 'react';

interface EmptyStateProps {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps): ReactNode {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
      <h3 className="text-lg font-medium text-gray-700 dark:text-slate-300">{title}</h3>
      {description && <p className="text-sm text-gray-500 dark:text-slate-400">{description}</p>}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
