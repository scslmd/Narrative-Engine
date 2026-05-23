import type { ReactNode } from 'react';

interface FoundationTabProps {
  children: ReactNode;
}

export function FoundationTab({ children }: FoundationTabProps) {
  return <>{children}</>;
}
