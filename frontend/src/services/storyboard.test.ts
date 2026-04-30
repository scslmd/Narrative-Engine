import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { getStoryboardCards, createStoryboardCard } from './storyboard';

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
});
