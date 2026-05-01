import { ReactNode } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, MemoryRouterProps } from 'react-router-dom';
import { ToastProvider } from '../hooks/useToast';

interface TestRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
  route?: string;
  initialEntries?: MemoryRouterProps['initialEntries'];
}

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 5 * 60 * 1000,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

function Wrapper({
  children,
  queryClient,
  route,
  initialEntries,
}: {
  children: ReactNode;
  queryClient: QueryClient;
  route?: string;
  initialEntries?: MemoryRouterProps['initialEntries'];
}) {
  const routerEntries = initialEntries ?? (route ? [route] : ['/']);

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <MemoryRouter
          initialEntries={routerEntries}
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          {children}
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export function customRender(
  ui: ReactNode,
  options: TestRenderOptions = {},
) {
  const queryClient = options.queryClient ?? createTestQueryClient();
  const utils = render(ui, {
    wrapper: ({ children }: { children: ReactNode }) => (
      <Wrapper
        queryClient={queryClient}
        route={options.route}
        initialEntries={options.initialEntries}
      >
        {children}
      </Wrapper>
    ),
    ...options,
  });

  return {
    ...utils,
    queryClient,
  };
}

export { customRender as render };
export { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
export { userEvent } from '@testing-library/user-event';
export type { RenderResult } from '@testing-library/react';
