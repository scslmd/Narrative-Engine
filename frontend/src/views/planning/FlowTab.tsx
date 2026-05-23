import type { ReactNode } from 'react';

interface FlowTabProps {
  children: ReactNode;
}

export function FlowTab({ children }: FlowTabProps) {
  return <>{children}</>;
}
