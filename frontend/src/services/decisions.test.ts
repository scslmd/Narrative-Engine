import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { getDecisions, getDecisionPath } from './decisions';

const mockNode = {
  node_id: 'node-1',
  project_id: 'proj-1',
  decision_type: 'branch',
  created_at: '2026-01-01T00:00:00Z',
};

describe('decisions service', () => {
  describe('getDecisions', () => {
    it('returns list of decisions for a project', async () => {
      server.use(
        http.get('/story-development/decisions', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockNode],
            meta: {},
          });
        }),
      );

      const result = await getDecisions('proj-1');

      expect(result).toHaveLength(1);
      expect(result[0].node_id).toBe('node-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/decisions', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getDecisions('proj-missing')).rejects.toThrow();
    });
  });

  describe('getDecisionPath', () => {
    it('returns decision path with parent nodes', async () => {
      server.use(
        http.get('/story-development/decisions/node-1/path', () =>
          HttpResponse.json({
            project_id: 'proj-1',
            node: mockNode,
            parent_path: [{ node_id: 'parent-1' }, { node_id: 'parent-2' }],
          }),
        ),
      );

      const result = await getDecisionPath('node-1');

      expect(result.path_id).toBe('node-1');
      expect(result.nodes).toEqual(['parent-1', 'parent-2', 'node-1']);
    });

    it('returns path with single node when no parents', async () => {
      server.use(
        http.get('/story-development/decisions/node-root/path', () =>
          HttpResponse.json({
            project_id: 'proj-1',
            node: { ...mockNode, node_id: 'node-root' },
            parent_path: [],
          }),
        ),
      );

      const result = await getDecisionPath('node-root');

      expect(result.nodes).toEqual(['node-root']);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/decisions/node-missing/path', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getDecisionPath('node-missing')).rejects.toThrow();
    });
  });
});
