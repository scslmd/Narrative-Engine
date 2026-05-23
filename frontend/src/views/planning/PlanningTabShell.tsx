import type { ReactNode } from 'react';

interface PlanningTabShellProps {
  children: ReactNode;
}

export function PlanningTabShell({ children }: PlanningTabShellProps) {
  return <>{children}</>;
}
