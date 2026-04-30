import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { getInspectLinks, createInspectLink } from './inspectLinks';

const mockLink = {
  link_id: 'link-1',
  project_id: 'proj-1',
  object_kind: 'draft',
  object_id: 'draft-1',
  logical_run_id: 'run-1',
  run_id: 'run-1',
  run_kind: 'job',
  attempt_number: null,
  label: null,
};

describe('inspectLinks service', () => {
  describe('getInspectLinks', () => {
    it('returns inspect links with no filters', async () => {
      server.use(
        http.get('/story-development/review/inspect-links', () =>
          HttpResponse.json({ project_id: 'proj-1', items: [mockLink], meta: {} }),
        ),
      );

      const result = await getInspectLinks();
      expect(result).toHaveLength(1);
    });

    it('passes all filters when provided', async () => {
      server.use(
        http.get('/story-development/review/inspect-links', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          expect(url.searchParams.get('object_kind')).toBe('draft');
          expect(url.searchParams.get('object_id')).toBe('draft-1');
          expect(url.searchParams.get('run_id')).toBe('run-1');
          return HttpResponse.json({ project_id: 'proj-1', items: [mockLink], meta: {} });
        }),
      );

      const result = await getInspectLinks('proj-1', 'draft', 'draft-1', 'run-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/review/inspect-links', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getInspectLinks('proj-missing')).rejects.toThrow();
    });
  });

  describe('createInspectLink', () => {
    it('creates an inspect link (201)', async () => {
      server.use(
        http.post('/story-development/review/inspect-links', () => {
          return HttpResponse.json({ ...mockLink, run_id: 'run-new' }, { status: 201 });
        }),
      );

      const result = await createInspectLink({
        link_id: 'link-new',
        project_id: 'proj-1',
        object_kind: 'draft',
        object_id: 'draft-1',
        logical_run_id: 'run-new',
        run_id: 'run-new',
        run_kind: 'job',
      });

      expect(result.run_id).toBe('run-new');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/review/inspect-links', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createInspectLink({
        link_id: 'link-bad',
        project_id: 'proj-1',
        object_kind: 'draft',
        object_id: 'draft-1',
        logical_run_id: 'run-x',
        run_id: 'run-x',
        run_kind: 'job',
      })).rejects.toThrow();
    });
  });
});
