import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import {
  getDraftArtifacts,
  getDraftArtifact,
  getManuscriptDocuments,
  getManuscriptDocument,
  promoteDraftToManuscript,
  getRevisionSuggestions,
  getRevisionSuggestion,
  createRevisionSuggestion,
  updateManuscriptContent,
  triggerManuscriptReview,
  createDraftArtifact,
  continueDraft,
  createAlternateVariant,
} from './drafting';

describe('drafting service', () => {
  describe('getDraftArtifacts', () => {
    it('returns list of draft artifacts', async () => {
      server.use(
        http.get('/v1/story-development/drafting/draft-artifacts', () =>
          HttpResponse.json({ project_id: 'proj-1', items: [{ artifact_id: 'art-1' }], meta: {} }),
        ),
      );

      const result = await getDraftArtifacts('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/drafting/draft-artifacts', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getDraftArtifacts('proj-missing')).rejects.toThrow();
    });
  });

  describe('getManuscriptDocuments', () => {
    it('returns list of manuscript documents', async () => {
      server.use(
        http.get('/v1/story-development/drafting/manuscript-documents', () =>
          HttpResponse.json({ project_id: 'proj-1', items: [{ document_id: 'doc-1' }], meta: {} }),
        ),
      );

      const result = await getManuscriptDocuments('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/drafting/manuscript-documents', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getManuscriptDocuments('proj-missing')).rejects.toThrow();
    });
  });

  describe('promoteDraftToManuscript', () => {
    it('promotes a draft to manuscript (201)', async () => {
      server.use(
        http.post('/v1/story-development/drafting/promote-draft', () =>
          HttpResponse.json({ document_id: 'ms-1' }, { status: 201 }),
        ),
      );

      const result = await promoteDraftToManuscript({
        project_id: 'proj-1',
        document_id: 'doc-1',
        draft_artifact_id: 'art-1',
      });

      expect(result.document_id).toBe('ms-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/drafting/promote-draft', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(promoteDraftToManuscript({
        project_id: 'proj-1',
        document_id: 'doc-x',
        draft_artifact_id: 'art-x',
      })).rejects.toThrow();
    });
  });

  describe('getRevisionSuggestions', () => {
    it('returns revision suggestions', async () => {
      server.use(
        http.get('/v1/story-development/drafting/revision-suggestions', () =>
          HttpResponse.json({ project_id: 'proj-1', items: [{ suggestion_id: 'sug-1' }], meta: {} }),
        ),
      );

      const result = await getRevisionSuggestions('proj-1');
      expect(result).toHaveLength(1);
    });

    it('passes target document filter when provided', async () => {
      server.use(
        http.get('/v1/story-development/drafting/revision-suggestions', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('target_document_id')).toBe('doc-1');
          return HttpResponse.json({ project_id: 'proj-1', items: [], meta: {} });
        }),
      );

      await getRevisionSuggestions('proj-1', 'doc-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/drafting/revision-suggestions', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getRevisionSuggestions('proj-missing')).rejects.toThrow();
    });
  });

  describe('createRevisionSuggestion', () => {
    it('creates a revision suggestion (201)', async () => {
      server.use(
        http.post('/v1/story-development/drafting/revision-suggestions', () =>
          HttpResponse.json({ suggestion_id: 'sug-new' }, { status: 201 }),
        ),
      );

      const result = await createRevisionSuggestion({
        suggestion_id: 'sug-new',
        project_id: 'proj-1',
        target_document_id: 'doc-1',
        source_text: 'Original',
        proposed_text: 'Fixed',
        rationale: 'Better wording',
        source_context: [],
        status: 'PENDING',
      });

      expect(result.suggestion_id).toBe('sug-new');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/drafting/revision-suggestions', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createRevisionSuggestion({
        suggestion_id: 'sug-bad',
        project_id: 'proj-1',
        target_document_id: 'x',
        source_text: '',
        proposed_text: '',
        rationale: '',
        source_context: [],
        status: 'PENDING',
      })).rejects.toThrow();
    });
  });

  describe('updateManuscriptContent', () => {
    it('updates manuscript content (200)', async () => {
      server.use(
        http.patch('/v1/story-development/drafting/manuscript-documents/doc-1', () =>
          HttpResponse.json({ document_id: 'doc-1', content: 'Updated content' }),
        ),
      );

      const result = await updateManuscriptContent('doc-1', 'proj-1', 'Updated content');
      expect(result.content).toBe('Updated content');
    });

    it('throws on error response', async () => {
      server.use(
        http.patch('/v1/story-development/drafting/manuscript-documents/doc-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(updateManuscriptContent('doc-missing', 'proj-1', 'x')).rejects.toThrow();
    });
  });

  describe('triggerManuscriptReview', () => {
    it('triggers a manuscript review (202)', async () => {
      server.use(
        http.post('/v1/story-development/drafting/manuscript-documents/doc-1/review', () =>
          HttpResponse.json({ findings: [{ finding_id: 'f-1' }] }, { status: 202 }),
        ),
      );

      const result = await triggerManuscriptReview('doc-1', 'proj-1');
      expect(result).toHaveLength(1);
    });

    it('returns empty array when no findings', async () => {
      server.use(
        http.post('/v1/story-development/drafting/manuscript-documents/doc-1/review', () =>
          HttpResponse.json({ findings: [] }, { status: 202 }),
        ),
      );

      const result = await triggerManuscriptReview('doc-1', 'proj-1');
      expect(result).toEqual([]);
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/drafting/manuscript-documents/doc-missing/review', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(triggerManuscriptReview('doc-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('createDraftArtifact', () => {
    it('creates a draft artifact (201)', async () => {
      server.use(
        http.post('/v1/story-development/drafting/draft-artifacts', () =>
          HttpResponse.json({ artifact_id: 'art-new' }, { status: 201 }),
        ),
      );

      const result = await createDraftArtifact({
        artifact_id: 'art-new',
        project_id: 'proj-1',
        title: 'New Draft',
        content: 'Draft content',
      });

      expect(result.artifact_id).toBe('art-new');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/drafting/draft-artifacts', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createDraftArtifact({
        artifact_id: 'art-bad',
        project_id: 'proj-1',
        title: '',
        content: '',
      })).rejects.toThrow();
    });
  });

  describe('continueDraft', () => {
    it('continues a draft from a prior artifact (201)', async () => {
      server.use(
        http.post('/v1/story-development/drafting/draft-artifacts/continue', () =>
          HttpResponse.json(
            { artifact_id: 'art-continued', title: 'Continued Draft', status: 'DRAFT' },
            { status: 201 },
          ),
        ),
      );

      const result = await continueDraft('art-1', 'proj-1');
      expect(result.artifact_id).toBe('art-continued');
    });

    it('sends the correct request body', async () => {
      let capturedBody: unknown;
      server.use(
        http.post('/v1/story-development/drafting/draft-artifacts/continue', async ({ request }) => {
          capturedBody = await request.json();
          return HttpResponse.json(
            { artifact_id: 'art-continued' },
            { status: 201 },
          );
        }),
      );

      await continueDraft('art-base', 'proj-1');
      expect(capturedBody).toEqual(
        expect.objectContaining({
          artifact_id: expect.any(String),
          project_id: 'proj-1',
          prior_draft_artifact_id: 'art-base',
        }),
      );
    });

    it('throws 404 when prior draft not found', async () => {
      server.use(
        http.post('/v1/story-development/drafting/draft-artifacts/continue', () =>
          HttpResponse.json({ detail: 'Prior draft or manuscript not found.' }, { status: 404 }),
        ),
      );

      await expect(continueDraft('art-missing', 'proj-1')).rejects.toThrow();
    });

    it('throws 400 on validation error', async () => {
      server.use(
        http.post('/v1/story-development/drafting/draft-artifacts/continue', () =>
          HttpResponse.json({ detail: 'Validation error' }, { status: 400 }),
        ),
      );

      await expect(continueDraft('art-1', 'proj-1')).rejects.toThrow();
    });
  });

  describe('createAlternateVariant', () => {
    it('creates an alternate variant of a draft (201)', async () => {
      server.use(
        http.post('/v1/story-development/drafting/draft-artifacts/alternate-variant', () =>
          HttpResponse.json(
            { artifact_id: 'art-variant', title: 'Alternate Draft', status: 'PROPOSED' },
            { status: 201 },
          ),
        ),
      );

      const result = await createAlternateVariant('art-1', 'proj-1');
      expect(result.artifact_id).toBe('art-variant');
    });

    it('sends the correct request body', async () => {
      let capturedBody: unknown;
      server.use(
        http.post('/v1/story-development/drafting/draft-artifacts/alternate-variant', async ({ request }) => {
          capturedBody = await request.json();
          return HttpResponse.json(
            { artifact_id: 'art-variant' },
            { status: 201 },
          );
        }),
      );

      await createAlternateVariant('art-base', 'proj-1');
      expect(capturedBody).toEqual(
        expect.objectContaining({
          artifact_id: expect.any(String),
          project_id: 'proj-1',
          base_draft_artifact_id: 'art-base',
        }),
      );
    });

    it('throws 404 when base draft not found', async () => {
      server.use(
        http.post('/v1/story-development/drafting/draft-artifacts/alternate-variant', () =>
          HttpResponse.json({ detail: 'Base draft or manuscript not found.' }, { status: 404 }),
        ),
      );

      await expect(createAlternateVariant('art-missing', 'proj-1')).rejects.toThrow();
    });

    it('throws 400 on validation error', async () => {
      server.use(
        http.post('/v1/story-development/drafting/draft-artifacts/alternate-variant', () =>
          HttpResponse.json({ detail: 'Validation error' }, { status: 400 }),
        ),
      );

      await expect(createAlternateVariant('art-1', 'proj-1')).rejects.toThrow();
    });
  });

  describe('getDraftArtifact', () => {
    it('returns a single draft artifact by id', async () => {
      server.use(
        http.get('/v1/story-development/drafting/draft-artifacts/art-1', () =>
          HttpResponse.json({ artifact_id: 'art-1', title: 'Single Draft' }),
        ),
      );

      const result = await getDraftArtifact('art-1', 'proj-1');
      expect(result.artifact_id).toBe('art-1');
    });

    it('passes project_id as query parameter', async () => {
      server.use(
        http.get('/v1/story-development/drafting/draft-artifacts/art-1', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({ artifact_id: 'art-1' });
        }),
      );

      await getDraftArtifact('art-1', 'proj-1');
    });

    it('throws on 404 response', async () => {
      server.use(
        http.get('/v1/story-development/drafting/draft-artifacts/art-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getDraftArtifact('art-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('getManuscriptDocument', () => {
    it('returns a single manuscript document by id', async () => {
      server.use(
        http.get('/v1/story-development/drafting/manuscript-documents/doc-1', () =>
          HttpResponse.json({ document_id: 'doc-1', title: 'Single Document' }),
        ),
      );

      const result = await getManuscriptDocument('doc-1', 'proj-1');
      expect(result.document_id).toBe('doc-1');
    });

    it('passes project_id as query parameter', async () => {
      server.use(
        http.get('/v1/story-development/drafting/manuscript-documents/doc-1', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({ document_id: 'doc-1' });
        }),
      );

      await getManuscriptDocument('doc-1', 'proj-1');
    });

    it('throws on 404 response', async () => {
      server.use(
        http.get('/v1/story-development/drafting/manuscript-documents/doc-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getManuscriptDocument('doc-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('getRevisionSuggestion', () => {
    it('returns a single revision suggestion by id', async () => {
      server.use(
        http.get('/v1/story-development/drafting/revision-suggestions/sug-1', () =>
          HttpResponse.json({ suggestion_id: 'sug-1', rationale: 'Fix wording' }),
        ),
      );

      const result = await getRevisionSuggestion('sug-1', 'proj-1');
      expect(result.suggestion_id).toBe('sug-1');
    });

    it('passes project_id as query parameter', async () => {
      server.use(
        http.get('/v1/story-development/drafting/revision-suggestions/sug-1', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({ suggestion_id: 'sug-1' });
        }),
      );

      await getRevisionSuggestion('sug-1', 'proj-1');
    });

    it('throws on 404 response', async () => {
      server.use(
        http.get('/v1/story-development/drafting/revision-suggestions/sug-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getRevisionSuggestion('sug-missing', 'proj-1')).rejects.toThrow();
    });
  });
});

