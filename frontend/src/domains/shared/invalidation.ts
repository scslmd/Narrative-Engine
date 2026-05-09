import type { QueryClient } from '@tanstack/react-query';

export function invalidateMany(queryClient: QueryClient, keys: readonly (readonly unknown[])[]): Promise<void[]> {
  return Promise.all(
    keys.map((queryKey) => queryClient.invalidateQueries({ queryKey })),
  );
}

