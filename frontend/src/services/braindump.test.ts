import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import {
  createBrainDumpSession,
  getBrainDumpSessions,
  updateBrainDumpSession,
  organizeBrainDumpSession,
} from './braindump';

const mockSession = {
  session_id: 'sess-1',
  project_id: 'proj-1',
  title: null,
  raw_text: 'Raw brain dump text',
  state: 'active' as const,
  created_at: null,
  updated_at: '2026-01-01T00:00:00Z',
};

describe('braindump service', () => {
  describe('createBrainDumpSession', () => {
    it('creates a brain dump session (201)', async () => {
      server.use(
        http.post('/v1/story-development/braindump/sessions', () => {
          return HttpResponse.json({ ...mockSession, raw_text: 'My thoughts...' }, { status: 201 });
        }),
      );

      const result = await createBrainDumpSession({
        project_id: 'proj-1',
        raw_text: 'My thoughts...',
      });

      expect(result.raw_text).toBe('My thoughts...');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/braindump/sessions', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createBrainDumpSession({ project_id: 'proj-1' })).rejects.toThrow();
    });
  });

  describe('getBrainDumpSessions', () => {
    it('returns list of brain dump sessions for a project', async () => {
      server.use(
        http.get('/v1/story-development/braindump/sessions', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            sessions: [mockSession],
            meta: {},
          });
        }),
      );

      const result = await getBrainDumpSessions('proj-1');

      expect(result).toHaveLength(1);
      expect(result[0].session_id).toBe('sess-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/braindump/sessions', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getBrainDumpSessions('proj-missing')).rejects.toThrow();
    });
  });

  describe('updateBrainDumpSession', () => {
    it('updates a brain dump session (200)', async () => {
      server.use(
        http.patch('/v1/story-development/braindump/sessions/sess-1', () => {
          return HttpResponse.json({ ...mockSession, raw_text: 'Updated text' });
        }),
      );

      const result = await updateBrainDumpSession('sess-1', 'proj-1', {
        raw_text: 'Updated text',
      });

      expect(result.raw_text).toBe('Updated text');
    });

    it('throws on error response', async () => {
      server.use(
        http.patch('/v1/story-development/braindump/sessions/sess-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(updateBrainDumpSession('sess-missing', 'proj-1', {})).rejects.toThrow();
    });
  });

  describe('organizeBrainDumpSession', () => {
    it('organizes a brain dump session (201)', async () => {
      server.use(
        http.post('/v1/story-development/braindump/sessions/sess-1/organize', () =>
          HttpResponse.json({
            session_id: 'sess-1',
            categorized_items: {},
            total_items: 0,
          }, { status: 201 }),
        ),
      );

      const result = await organizeBrainDumpSession('sess-1', 'proj-1');
      expect(result.session_id).toBe('sess-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/braindump/sessions/sess-missing/organize', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(organizeBrainDumpSession('sess-missing', 'proj-1')).rejects.toThrow();
    });
  });
});
