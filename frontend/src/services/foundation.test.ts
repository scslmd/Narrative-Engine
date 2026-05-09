import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { getFoundation, createFoundation, updateFoundation, getReviewCues, getFoundationRevisions } from './foundation';

const mockProfile = {
  foundation_id: 'found-1',
  project_id: 'proj-1',
  premise: 'A test premise',
  logline: 'Test logline',
  thematic_spine: 'Test theme',
  emotional_promise: 'Test promise',
  tone_and_voice_direction: 'Test tone',
  target_audience: 'Test audience',
  narrative_constraints: [],
  complexity_level: 'medium',
  success_definition: 'Test definition',
  version: 1,
};

const mockRevision = {
  revision_id: 'rev-1',
  foundation_id: 'found-1',
  snapshot: mockProfile,
  change_summary: null,
};

const mockReviewCue = {
  impacted_area: 'character_arcs',
  reason: 'Premise changed significantly',
  triggering_revision_id: 'rev-1',
  triggering_fields: ['premise'],
};

describe('foundation service', () => {
  describe('getFoundation', () => {
    it('returns foundation profile for a project', async () => {
      server.use(
        http.get('/v1/story-development/foundation', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            foundation_id: 'found-1',
            active_profile: mockProfile,
            current_revision_id: 'rev-1',
            revision_history: [],
            downstream_review_cues: [],
          });
        }),
      );

      const result = await getFoundation('proj-1');

      expect(result.project_id).toBe('proj-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/foundation', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getFoundation('proj-missing')).rejects.toThrow();
    });
  });

  describe('createFoundation', () => {
    it('creates a foundation profile (201)', async () => {
      server.use(
        http.post('/v1/story-development/foundation', () => {
          return HttpResponse.json({
            project_id: 'proj-1',
            foundation_id: 'found-1',
            active_profile: mockProfile,
            current_revision_id: 'rev-1',
            revision_history: [],
            downstream_review_cues: [],
            created_revision: mockRevision,
          }, { status: 201 });
        }),
      );

      const result = await createFoundation({
        project_id: 'proj-1',
        premise: 'New premise',
        logline: 'New logline',
        thematic_spine: 'Theme',
        emotional_promise: 'Promise',
        tone_and_voice_direction: 'Tone',
        target_audience: 'Audience',
        complexity_level: 'medium',
        success_definition: 'Definition',
      });

      expect(result.foundation_id).toBe('found-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/foundation', () => {
          return HttpResponse.json({ detail: 'Bad request' }, { status: 400 });
        }),
      );

      await expect(createFoundation({
        project_id: 'proj-1',
        premise: '',
        logline: '',
        thematic_spine: '',
        emotional_promise: '',
        tone_and_voice_direction: '',
        target_audience: '',
        complexity_level: '',
        success_definition: '',
      })).rejects.toThrow();
    });
  });

  describe('updateFoundation', () => {
    it('updates a foundation profile (200)', async () => {
      server.use(
        http.patch('/v1/story-development/foundation', () => {
          return HttpResponse.json({
            project_id: 'proj-1',
            foundation_id: 'found-1',
            active_profile: { ...mockProfile, premise: 'Updated premise' },
            current_revision_id: 'rev-2',
            revision_history: [],
            downstream_review_cues: [],
            created_revision: mockRevision,
          });
        }),
      );

      const result = await updateFoundation('proj-1', { premise: 'Updated premise' });

      expect(result.active_profile?.premise).toBe('Updated premise');
    });

    it('throws on error response', async () => {
      server.use(
        http.patch('/v1/story-development/foundation', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(updateFoundation('proj-missing', {})).rejects.toThrow();
    });
  });

  describe('getReviewCues', () => {
    it('returns review cues for a project', async () => {
      server.use(
        http.get('/v1/story-development/foundation/review-cues', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockReviewCue],
            meta: {},
          });
        }),
      );

      const result = await getReviewCues('proj-1');

      expect(result).toHaveLength(1);
      expect(result[0].impacted_area).toBe('character_arcs');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/foundation/review-cues', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getReviewCues('proj-missing')).rejects.toThrow();
    });
  });

  describe('getFoundationRevisions', () => {
    it('returns foundation revisions for a project', async () => {
      server.use(
        http.get('/v1/story-development/foundation/revisions', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockRevision],
            meta: {},
          });
        }),
      );

      const result = await getFoundationRevisions('proj-1');

      expect(result).toHaveLength(1);
      expect(result[0].revision_id).toBe('rev-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/foundation/revisions', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getFoundationRevisions('proj-missing')).rejects.toThrow();
    });
  });
});

