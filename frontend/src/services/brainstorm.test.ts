import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import {
  getBrainstormItems,
  createBrainstormItem,
  clusterBrainstormItems,
  promoteBrainstormItem,
} from './brainstorm';

const mockItem = {
  item_id: 'item-1',
  project_id: 'proj-1',
  content: 'Test idea',
  status: 'keep' as const,
  tags: [],
  source_notes: null,
  item_type: null,
};

describe('brainstorm service', () => {
  describe('getBrainstormItems', () => {
    it('returns list of brainstorm items for a project', async () => {
      server.use(
        http.get('/story-development/brainstorm/items', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockItem],
            meta: {},
          });
        }),
      );

      const result = await getBrainstormItems('proj-1');

      expect(result).toHaveLength(1);
      expect(result[0].item_id).toBe('item-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/brainstorm/items', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getBrainstormItems('proj-missing')).rejects.toThrow();
    });
  });

  describe('createBrainstormItem', () => {
    it('creates a brainstorm item (201)', async () => {
      server.use(
        http.post('/story-development/brainstorm/items', () => {
          return HttpResponse.json({ ...mockItem, content: 'New idea' }, { status: 201 });
        }),
      );

      const result = await createBrainstormItem({
        project_id: 'proj-1',
        content: 'New idea',
      });

      expect(result.content).toBe('New idea');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/brainstorm/items', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createBrainstormItem({ project_id: 'proj-1', content: '' })).rejects.toThrow();
    });
  });

  describe('clusterBrainstormItems', () => {
    it('clusters brainstorm items (200)', async () => {
      server.use(
        http.post('/story-development/brainstorm/items/cluster', () => {
          return HttpResponse.json([
            { ...mockItem, item_id: 'item-1' },
            { ...mockItem, item_id: 'item-2' },
          ]);
        }),
      );

      const result = await clusterBrainstormItems({
        project_id: 'proj-1',
        item_ids: ['item-1', 'item-2'],
      });

      expect(result).toHaveLength(2);
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/brainstorm/items/cluster', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(clusterBrainstormItems({ project_id: 'proj-1', item_ids: [] })).rejects.toThrow();
    });
  });

  describe('promoteBrainstormItem', () => {
    it('promotes a brainstorm item to a target type (201)', async () => {
      server.use(
        http.post('/story-development/brainstorm/items/promote', async ({ request }) => {
          const body = (await request.json()) as Record<string, string>;
          expect(body.item_id).toBe('item-1');
          expect(body.project_id).toBe('proj-1');
          expect(body.target_object_kind).toBe('character');
          return HttpResponse.json({
            promoted_to: 'character',
            target_id: 'char-abc',
          }, { status: 201 });
        }),
      );

      const result = await promoteBrainstormItem('item-1', 'proj-1', 'character', 'char-abc');

      expect(result.promoted_to).toBe('character');
      expect(result.target_id).toBe('char-abc');
    });

    it('throws on 409 conflict (already promoted)', async () => {
      server.use(
        http.post('/story-development/brainstorm/items/promote', () =>
          HttpResponse.json({ detail: 'Already promoted' }, { status: 409 }),
        ),
      );

      await expect(promoteBrainstormItem('item-1', 'proj-1', 'character', 'char-abc')).rejects.toThrow();
    });

    it('throws on 400 invalid target type', async () => {
      server.use(
        http.post('/story-development/brainstorm/items/promote', () =>
          HttpResponse.json({ detail: 'Invalid target type' }, { status: 400 }),
        ),
      );

      await expect(promoteBrainstormItem('item-1', 'proj-1', 'invalid_type', 'char-abc')).rejects.toThrow();
    });
  });
});
