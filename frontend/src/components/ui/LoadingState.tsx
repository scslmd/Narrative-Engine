import type { ReactNode } from 'react';

interface LoadingStateProps {
  isLoading: boolean;
  fallback?: ReactNode;
  children: ReactNode;
}

const SKELETON_WIDTHS = ['w-3/4', 'w-full', 'w-5/6'];

function Skeleton(): React.ReactElement {
  return (
    <div className="animate-pulse space-y-3" role="status" aria-label="Loading">
      {SKELETON_WIDTHS.map((width, index) => (
        <div
          key={index}
          data-testid="skeleton-line"
          className={`h-4 rounded bg-gray-200 ${width}`}
        />
      ))}
      <span className="sr-only">Loading...</span>
    </div>
  );
}

export function LoadingState({
  isLoading,
  fallback,
  children,
}: LoadingStateProps): React.ReactElement {
  if (!isLoading) return <>{children}</>;

  if (fallback) return <>{fallback}</>;

  return <Skeleton />;
}
