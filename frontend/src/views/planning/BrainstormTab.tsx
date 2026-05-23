import type { ReactNode } from 'react';

interface BrainstormTabProps {
  children: ReactNode;
}

export function BrainstormTab({ children }: BrainstormTabProps) {
  return <>{children}</>;
}
