import { Section } from './ui';
import { useIsDark } from './hooks';
import type { PlanningDependency } from '../../types/planning';
import type { ApiError } from '../../lib/api';
import { ErrorBanner } from '../ui/ErrorBanner';
import { LoadingState } from '../ui/LoadingState';
import { EmptyState } from '../ui/EmptyState';

export interface DependenciesSectionProps {
  dependencies: PlanningDependency[];
  isLoading: boolean;
  error: ApiError | null;
  onRetry: () => void;
}

export function DependenciesSection({
  dependencies,
  isLoading,
  error,
  onRetry,
}: DependenciesSectionProps) {
  const isDark = useIsDark();
  return (
    <Section title="Dependencies" count={dependencies.length}>
      {error ? (
        <ErrorBanner error={error} onRetry={onRetry} />
      ) : (
        <LoadingState isLoading={isLoading}>
          {dependencies.length === 0 ? (
            <EmptyState title="No dependencies" description="Dependencies track relationships between planning artifacts." />
          ) : (
            <div className="space-y-2">
              {dependencies.map((dep) => (
                <div key={dep.dependency_id} className={`p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} text-sm`}>
                  <span className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{dep.upstream_id}</span>
                  <span className="mx-2 text-muted">→</span>
                  <span className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{dep.downstream_id}</span>
                  {dep.reason && (
                    <div className="mt-1 text-xs italic text-subtle">{dep.reason}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </LoadingState>
      )}
    </Section>
  );
}
