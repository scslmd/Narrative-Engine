import type { ReactNode } from 'react';

interface CheckerTabProps {
  children: ReactNode;
}

export function CheckerTab({ children }: CheckerTabProps) {
  return <>{children}</>;
}
