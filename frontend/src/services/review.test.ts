import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { getFindings, getDecisionsForFinding, createDecision, getFinding, getDecision } from './review';

const mockFinding = {
  finding_id: 'finding-1',
  project_id: 'proj-1',
  source_object_id: 'char-1',
  source_object_kind: 'character',
  severity: 'high' as const,
  summary: 'Test finding',
  details: 'Detailed info',
};

const mockDecision = {
  decision_id: 'decision-1',
  project_id: 'proj-1',
  target_kind: 'finding',
  target_id: 'finding-1',
  decision: 'accept' as const,
  notes: null,
  source_context: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

describe('review service', () => {
  describe('getFindings', () => {
    it('returns findings with basic filter', async () => {
      server.use(
        http.get('/story-development/review/findings', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockFinding],
            meta: {},
          });
        }),
      );

      const result = await getFindings({ project_id: 'proj-1' });

      expect(result).toHaveLength(1);
      expect(result[0].finding_id).toBe('finding-1');
    });

    it('passes severity filter when provided', async () => {
      server.use(
        http.get('/story-development/review/findings', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('severity')).toBe('high,medium');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockFinding],
            meta: {},
          });
        }),
      );

      await getFindings({
        project_id: 'proj-1',
        severity: ['high', 'medium'],
      });
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/review/findings', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getFindings({ project_id: 'proj-missing' })).rejects.toThrow();
    });
  });

  describe('getDecisionsForFinding', () => {
    it('returns decisions for a finding', async () => {
      server.use(
        http.get('/story-development/review/decisions', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          expect(url.searchParams.get('target_id')).toBe('finding-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockDecision],
            meta: {},
          });
        }),
      );

      const result = await getDecisionsForFinding('proj-1', 'finding-1');

      expect(result).toHaveLength(1);
      expect(result[0].decision_id).toBe('decision-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/review/decisions', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getDecisionsForFinding('proj-1', 'finding-missing')).rejects.toThrow();
    });
  });

  describe('createDecision', () => {
    it('creates a review decision (201)', async () => {
      server.use(
        http.post('/story-development/review/decisions', () => {
          return HttpResponse.json({ ...mockDecision, decision: 'accept' }, { status: 201 });
        }),
      );

      const result = await createDecision({
        decision_id: 'dec-new',
        project_id: 'proj-1',
        target_kind: 'finding',
        target_id: 'finding-1',
        decision: 'accept',
      });

      expect(result.decision).toBe('accept');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/review/decisions', () => {
          return HttpResponse.json({ detail: 'Bad request' }, { status: 400 });
        }),
      );

      await expect(createDecision({
        decision_id: 'dec-bad',
        project_id: 'proj-1',
        target_kind: 'finding',
        target_id: 'x',
        decision: 'accept',
      })).rejects.toThrow();
    });
  });

  describe('getFinding', () => {
    it('returns a single finding by id', async () => {
      server.use(
        http.get('/story-development/review/findings/finding-1', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json(mockFinding);
        }),
      );

      const result = await getFinding('finding-1', 'proj-1');

      expect(result.finding_id).toBe('finding-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/review/findings/finding-missing', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getFinding('finding-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('getDecision', () => {
    it('returns a single decision by id', async () => {
      server.use(
        http.get('/story-development/review/decisions/decision-1', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json(mockDecision);
        }),
      );

      const result = await getDecision('decision-1', 'proj-1');

      expect(result.decision_id).toBe('decision-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/review/decisions/decision-missing', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getDecision('decision-missing', 'proj-1')).rejects.toThrow();
    });
  });
});
