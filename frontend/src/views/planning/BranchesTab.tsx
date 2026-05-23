import type { ReactNode } from 'react';

interface BranchesTabProps {
  children: ReactNode;
}

export function BranchesTab({ children }: BranchesTabProps) {
  return <>{children}</>;
}
