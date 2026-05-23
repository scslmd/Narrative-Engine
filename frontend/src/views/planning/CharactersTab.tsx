import type { ReactNode } from 'react';

interface CharactersTabProps {
  children: ReactNode;
}

export function CharactersTab({ children }: CharactersTabProps) {
  return <>{children}</>;
}
