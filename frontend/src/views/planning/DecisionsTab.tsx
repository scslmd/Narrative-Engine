import type { ReactNode } from 'react';

interface DecisionsTabProps {
  children: ReactNode;
}

export function DecisionsTab({ children }: DecisionsTabProps) {
  return <>{children}</>;
}
