import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { getWorldBibleEntries, createWorldBibleEntry, updateWorldBibleEntry } from './worldBible';

const mockEntry = {
  entry_id: 'entry-1',
  project_id: 'proj-1',
  entry_type: 'location' as const,
  title: 'Test Location',
  summary: 'A test location',
};

describe('worldBible service', () => {
  describe('getWorldBibleEntries', () => {
    it('returns list of world bible entries for a project', async () => {
      server.use(
        http.get('/story-development/world-bible', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockEntry],
            meta: {},
          });
        }),
      );

      const result = await getWorldBibleEntries('proj-1');

      expect(result).toHaveLength(1);
      expect(result[0].entry_type).toBe('location');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/world-bible', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getWorldBibleEntries('proj-missing')).rejects.toThrow();
    });
  });

  describe('createWorldBibleEntry', () => {
    it('creates a world bible entry (201)', async () => {
      server.use(
        http.post('/story-development/world-bible', () => {
          return HttpResponse.json({ ...mockEntry, title: 'New Org' }, { status: 201 });
        }),
      );

      const result = await createWorldBibleEntry({
        project_id: 'proj-1',
        entry_type: 'organization',
        title: 'New Org',
        summary: 'A new organization',
      });

      expect(result.title).toBe('New Org');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/world-bible', () => {
          return HttpResponse.json({ detail: 'Bad request' }, { status: 400 });
        }),
      );

      await expect(createWorldBibleEntry({
        project_id: 'proj-1',
        entry_type: 'location',
        title: '',
        summary: '',
      })).rejects.toThrow();
    });
  });

  describe('updateWorldBibleEntry', () => {
    it('updates a world bible entry (200)', async () => {
      server.use(
        http.patch('/story-development/world-bible/location/Test%20Location', () => {
          return HttpResponse.json({ ...mockEntry, summary: 'Updated summary' });
        }),
      );

      const result = await updateWorldBibleEntry('location', 'Test Location', 'proj-1', {
        summary: 'Updated summary',
      });

      expect(result.summary).toBe('Updated summary');
    });

    it('throws on error response', async () => {
      server.use(
        http.patch('/story-development/world-bible/location/Missing', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(updateWorldBibleEntry('location', 'Missing', 'proj-1', {})).rejects.toThrow();
    });
  });
});
