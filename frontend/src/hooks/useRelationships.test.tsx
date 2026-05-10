import { describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useRelationships } from './useRelationships';

vi.mock('../services/relationships', () => ({
  createRelationship: vi.fn(),
  updateRelationship: vi.fn(),
  deleteRelationship: vi.fn(),
}));

const { createRelationship: mockCreate, updateRelationship: mockUpdate, deleteRelationship: mockDelete } = await import(
  '../services/relationships'
);

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const WithProviders = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>{children}</QueryClientProvider>
);

describe('useRelationships', () => {
  it('calls create service and invalidates relationships cache', async () => {
    const mockEdge = {
      edge_id: 'edge-1',
      source_character_id: 'char-1',
      target_character_id: 'char-2',
      relation_kind: 'ALLY',
      summary: 'Childhood friends',
      tension: null,
      notes: null,
    };
    (mockCreate as ReturnType<typeof vi.fn>).mockResolvedValue(mockEdge);

    const { result } = renderHook(() => useRelationships('proj-1'), {
      wrapper: WithProviders,
    });

    await act(async () => {
      await result.current.createRelationship({
        project_id: 'proj-1',
        source_character_id: 'char-1',
        target_character_id: 'char-2',
        relation_kind: 'ALLY',
        summary: 'Childhood friends',
      });
    });

    expect(mockCreate).toHaveBeenCalledWith({
      project_id: 'proj-1',
      source_character_id: 'char-1',
      target_character_id: 'char-2',
      relation_kind: 'ALLY',
      summary: 'Childhood friends',
    });
  });

  it('calls update service and invalidates relationships cache', async () => {
    const mockEdge = {
      edge_id: 'edge-1',
      source_character_id: 'char-1',
      target_character_id: 'char-2',
      relation_kind: 'ALLY',
      summary: 'Updated summary',
      tension: null,
      notes: null,
    };
    (mockUpdate as ReturnType<typeof vi.fn>).mockResolvedValue(mockEdge);

    const { result } = renderHook(() => useRelationships('proj-1'), {
      wrapper: WithProviders,
    });

    await act(async () => {
      await result.current.updateRelationship('edge-1', { summary: 'Updated summary' });
    });

    expect(mockUpdate).toHaveBeenCalledWith('edge-1', { summary: 'Updated summary' }, 'proj-1');
  });

  it('calls delete service and invalidates relationships cache', async () => {
    (mockDelete as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);

    const { result } = renderHook(() => useRelationships('proj-1'), {
      wrapper: WithProviders,
    });

    await act(async () => {
      await result.current.deleteRelationship('edge-1');
    });

    expect(mockDelete).toHaveBeenCalledWith('edge-1', 'proj-1');
  });
});
