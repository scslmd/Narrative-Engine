import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import {
  getArcCandidates,
  getArcComparisons,
  getArcSelections,
  getArcStageMaps,
  createArcCandidate,
  createArcSelection,
  deleteArcSelection,
  createArcStageMap,
} from './arcs';

const mockCandidate = {
  arc_id: 'arc-1',
  project_id: 'proj-1',
  name: 'Test Arc',
  summary: 'A test arc',
  stage_map_notes: [],
  fit_notes: [],
  tags: [],
};

describe('arcs service', () => {
  describe('getArcCandidates', () => {
    it('returns list of arc candidates for a project', async () => {
      server.use(
        http.get('/story-development/arcs/candidates', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockCandidate],
            meta: {},
          });
        }),
      );

      const result = await getArcCandidates('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/arcs/candidates', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getArcCandidates('proj-missing')).rejects.toThrow();
    });
  });

  describe('getArcComparisons', () => {
    it('returns list of arc comparisons for a project', async () => {
      server.use(
        http.get('/story-development/arcs/comparisons', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [{ comparison_id: 'comp-1' }],
            meta: {},
          });
        }),
      );

      const result = await getArcComparisons('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/arcs/comparisons', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getArcComparisons('proj-missing')).rejects.toThrow();
    });
  });

  describe('getArcSelections', () => {
    it('returns list of arc selections for a project', async () => {
      server.use(
        http.get('/story-development/arcs/selections', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [{ selection_id: 'sel-1' }],
            meta: {},
          });
        }),
      );

      const result = await getArcSelections('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/arcs/selections', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getArcSelections('proj-missing')).rejects.toThrow();
    });
  });

  describe('getArcStageMaps', () => {
    it('returns list of arc stage maps for a project', async () => {
      server.use(
        http.get('/story-development/arcs/stage-maps', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [{ arc_stage_map_id: 'map-1' }],
            meta: {},
          });
        }),
      );

      const result = await getArcStageMaps('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/arcs/stage-maps', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getArcStageMaps('proj-missing')).rejects.toThrow();
    });
  });

  describe('createArcCandidate', () => {
    it('creates an arc candidate (201)', async () => {
      server.use(
        http.post('/story-development/arcs/candidates', () => {
          return HttpResponse.json({ ...mockCandidate, arc_id: 'arc-new', name: 'New Arc' }, { status: 201 });
        }),
      );

      const result = await createArcCandidate({
        arc_id: 'arc-new',
        project_id: 'proj-1',
        name: 'New Arc',
        summary: 'A new arc',
      });

      expect(result.arc_id).toBe('arc-new');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/arcs/candidates', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createArcCandidate({
        arc_id: 'arc-bad',
        project_id: 'proj-1',
        name: '',
        summary: '',
      })).rejects.toThrow();
    });
  });

  describe('createArcSelection', () => {
    it('creates an arc selection (201)', async () => {
      server.use(
        http.post('/story-development/arcs/selections', () => {
          return HttpResponse.json({ selection_id: 'sel-new' }, { status: 201 });
        }),
      );

      const result = await createArcSelection({
        project_id: 'proj-1',
        selected_arc: mockCandidate,
      });

      expect(result.selection_id).toBe('sel-new');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/arcs/selections', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createArcSelection({
        project_id: 'proj-1',
        selected_arc: mockCandidate,
      })).rejects.toThrow();
    });
  });

  describe('deleteArcSelection', () => {
    it('deletes an arc selection (200)', async () => {
      server.use(
        http.delete('/story-development/arcs/selections/sel-1', () =>
          HttpResponse.json(null),
        ),
      );

      await expect(deleteArcSelection('sel-1', 'proj-1')).resolves.toBeUndefined();
    });

    it('throws on error response', async () => {
      server.use(
        http.delete('/story-development/arcs/selections/sel-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(deleteArcSelection('sel-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('createArcStageMap', () => {
    it('creates an arc stage map (201)', async () => {
      server.use(
        http.post('/story-development/arcs/stage-maps', () => {
          return HttpResponse.json({ arc_stage_map_id: 'map-new' }, { status: 201 });
        }),
      );

      const result = await createArcStageMap({
        project_id: 'proj-1',
        arc_id: 'arc-1',
        stage_kinds: ['drafting'],
      });

      expect(result.arc_stage_map_id).toBe('map-new');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/arcs/stage-maps', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createArcStageMap({
        project_id: 'proj-1',
        arc_id: 'arc-bad',
        stage_kinds: [],
      })).rejects.toThrow();
    });
  });
});
