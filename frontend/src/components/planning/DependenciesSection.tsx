import { Section, EmptyState, WorkspaceStatus } from './ui';
import { useIsDark } from './hooks';
import type { PlanningDependency } from '../../types/planning';

export interface DependenciesSectionProps {
  dependencies: PlanningDependency[];
  isLoading: boolean;
}

export function DependenciesSection({
  dependencies,
  isLoading,
}: DependenciesSectionProps) {
  const isDark = useIsDark();
  return (
    <Section title="Dependencies" count={dependencies.length}>
      {isLoading ? (
        <WorkspaceStatus title="Loading dependencies" detail="Fetching planning dependencies..." />
      ) : dependencies.length === 0 ? (
        <EmptyState text="No dependencies defined. Dependencies track relationships between planning artifacts." />
      ) : (
        <div className="space-y-2">
          {dependencies.map((dep) => (
            <div key={dep.dependency_id} className={`p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} text-sm`}>
              <span className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{dep.upstream_id}</span>
              <span className={`mx-2 ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>→</span>
              <span className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{dep.downstream_id}</span>
              {dep.reason && (
                <div className={`mt-1 text-xs italic ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>{dep.reason}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}
