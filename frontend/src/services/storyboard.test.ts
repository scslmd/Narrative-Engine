import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { getStoryboardCards, createStoryboardCard, updateStoryboardCard, deleteStoryboardCard, reindexColumn } from './storyboard';

const mockCard = {
  card_id: 'card-1',
  project_id: 'proj-1',
  title: 'Test Card',
  content: 'Card content',
  card_type: 'scene',
  column_id: null,
  position: 0,
  tags: [],
  character_ids: [],
  dependencies: [],
  metadata: {},
};

describe('storyboard service', () => {
  describe('getStoryboardCards', () => {
    it('returns list of storyboard cards for a project', async () => {
      server.use(
        http.get('/storyboard/cards', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockCard],
            meta: {},
          });
        }),
      );

      const result = await getStoryboardCards('proj-1');

      expect(result).toHaveLength(1);
      expect(result[0].card_id).toBe('card-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/storyboard/cards', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getStoryboardCards('proj-missing')).rejects.toThrow();
    });
  });

  describe('createStoryboardCard', () => {
    it('creates a storyboard card (201)', async () => {
      server.use(
        http.post('/storyboard/cards', () => {
          return HttpResponse.json({ ...mockCard, title: 'New Card' }, { status: 201 });
        }),
      );

      const result = await createStoryboardCard('proj-1', {
        project_id: 'proj-1',
        card_id: 'card-new',
        title: 'New Card',
        content: 'New content',
      });

      expect(result.title).toBe('New Card');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/storyboard/cards', () => {
          return HttpResponse.json({ detail: 'Bad request' }, { status: 400 });
        }),
      );

      await expect(createStoryboardCard('proj-1', {
        project_id: 'proj-1',
        card_id: 'card-bad',
        title: '',
        content: '',
      })).rejects.toThrow();
    });
  });

  describe('updateStoryboardCard', () => {
    it('updates a storyboard card via PATCH', async () => {
      server.use(
        http.patch('/storyboard/cards/:cardId', async ({ params, request }) => {
          expect(params.cardId).toBe('card-1');
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          const body = (await request.json()) as Record<string, unknown>;
          expect(body.title).toBe('Updated Title');
          return HttpResponse.json({ ...mockCard, title: 'Updated Title' });
        }),
      );

      const result = await updateStoryboardCard('card-1', { title: 'Updated Title' }, 'proj-1');

      expect(result.title).toBe('Updated Title');
      expect(result.card_id).toBe('card-1');
    });

    it('updates card content and type', async () => {
      server.use(
        http.patch('/storyboard/cards/:cardId', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({
            ...mockCard,
            content: body.content as string,
            card_type: body.card_type as string,
          });
        }),
      );

      const result = await updateStoryboardCard('card-1', {
        content: 'New content',
        card_type: 'plot',
      });

      expect(result.content).toBe('New content');
      expect(result.card_type).toBe('plot');
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.patch('/storyboard/cards/:cardId', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(updateStoryboardCard('card-missing', { title: 'X' })).rejects.toThrow();
    });
  });

  describe('deleteStoryboardCard', () => {
    it('deletes a storyboard card via DELETE (204)', async () => {
      server.use(
        http.delete('/storyboard/cards/:cardId', ({ params, request }) => {
          expect(params.cardId).toBe('card-1');
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return new HttpResponse(null, { status: 204 });
        }),
      );

      await deleteStoryboardCard('card-1', 'proj-1');
    });

    it('throws on 404 not found', async () => {
      server.use(
        http.delete('/storyboard/cards/:cardId', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(deleteStoryboardCard('card-missing')).rejects.toThrow();
    });
  });

  describe('reindexColumn', () => {
    it('reindexes cards in a column via PUT', async () => {
      const reorderedCards = [
        { ...mockCard, card_id: 'card-a', position: 0 },
        { ...mockCard, card_id: 'card-b', position: 1 },
        { ...mockCard, card_id: 'card-c', position: 2 },
      ];

      server.use(
        http.put('/storyboard/cards/:columnId/reindex', async ({ params, request }) => {
          expect(params.columnId).toBe('col-1');
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          const body = (await request.json()) as Record<string, unknown>;
          expect(body.card_ids).toEqual(['card-a', 'card-b', 'card-c']);
          return HttpResponse.json({
            project_id: 'proj-1',
            items: reorderedCards,
            meta: { ordered_by: 'position_asc' },
          });
        }),
      );

      const result = await reindexColumn('col-1', ['card-a', 'card-b', 'card-c'], 'proj-1');

      expect(result).toHaveLength(3);
      expect(result[0].card_id).toBe('card-a');
      expect(result[0].position).toBe(0);
      expect(result[2].card_id).toBe('card-c');
      expect(result[2].position).toBe(2);
    });

    it('handles empty card list', async () => {
      server.use(
        http.put('/storyboard/cards/:columnId/reindex', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          expect(body.card_ids).toEqual([]);
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [],
            meta: {},
          });
        }),
      );

      const result = await reindexColumn('col-1', [], 'proj-1');
      expect(result).toHaveLength(0);
    });

    it('throws on 400 validation error', async () => {
      server.use(
        http.put('/storyboard/cards/:columnId/reindex', () => {
          return HttpResponse.json({ detail: 'Invalid card IDs' }, { status: 400 });
        }),
      );

      await expect(reindexColumn('col-1', ['invalid'])).rejects.toThrow();
    });
  });
});
