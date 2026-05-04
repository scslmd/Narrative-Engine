import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { getRelationships, deleteRelationship, updateRelationship } from './relationships';

const mockEdge = {
  edge_id: 'edge-1',
  project_id: 'proj-1',
  source_character_id: 'char-1',
  target_character_id: 'char-2',
  relationship_type: 'ally',
};

describe('relationships service', () => {
  describe('getRelationships', () => {
    it('returns list of relationships for a project', async () => {
      server.use(
        http.get('/story-development/relationships', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockEdge],
            meta: {},
          });
        }),
      );

      const result = await getRelationships('proj-1');

      expect(result).toHaveLength(1);
      expect(result[0].edge_id).toBe('edge-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/relationships', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getRelationships('proj-missing')).rejects.toThrow();
    });
  });

  describe('deleteRelationship', () => {
    it('deletes a relationship edge (200)', async () => {
      server.use(
        http.delete('/story-development/relationships/edge-1', () => {
          return HttpResponse.json(null);
        }),
      );

      await expect(deleteRelationship('edge-1', 'proj-1')).resolves.toBeUndefined();
    });

    it('throws on error response', async () => {
      server.use(
        http.delete('/story-development/relationships/edge-missing', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(deleteRelationship('edge-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('updateRelationship', () => {
    it('updates a relationship edge (200)', async () => {
      server.use(
        http.patch('/story-development/relationships/edge-1', async ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          const body = await request.json();
          expect(body).toHaveProperty('relation_kind');
          return HttpResponse.json({
            edge_id: 'edge-1',
            source_character_id: 'char-1',
            target_character_id: 'char-2',
            relation_kind: 'rival',
            summary: 'updated summary',
            tension: null,
            notes: null,
          });
        }),
      );

      const result = await updateRelationship('edge-1', { relation_kind: 'rival', summary: 'updated summary' }, 'proj-1');

      expect(result.edge_id).toBe('edge-1');
      expect(result.relation_kind).toBe('rival');
    });

    it('throws on error response', async () => {
      server.use(
        http.patch('/story-development/relationships/edge-missing', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(updateRelationship('edge-missing', {}, 'proj-1')).rejects.toThrow();
    });
  });
});
