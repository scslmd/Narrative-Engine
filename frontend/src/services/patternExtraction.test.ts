import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { submitPatternExtraction, submitProjectPatternExtraction, getExtractionStatus } from './patternExtraction';

describe('patternExtraction service', () => {
  describe('submitPatternExtraction', () => {
    it('submits pattern extraction request', async () => {
      server.use(
        http.post('/v1/projects/import-patterns', () => {
          return HttpResponse.json({
            extraction_id: 'extract-1',
            status: 'submitted',
          });
        }),
      );

      const result = await submitPatternExtraction({
        text: 'Once upon a time...',
        source_type: 'narrative',
      });

      expect(result.extraction_id).toBe('extract-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/projects/import-patterns', () => {
          return HttpResponse.json({ detail: 'Bad request' }, { status: 400 });
        }),
      );

      await expect(submitPatternExtraction({ text: '', source_type: 'narrative' })).rejects.toThrow();
    });
  });

  describe('submitProjectPatternExtraction', () => {
    it('submits project-specific pattern extraction', async () => {
      server.use(
        http.post('/v1/projects/proj-1/extract-patterns', () => {
          return HttpResponse.json({
            extraction_id: 'extract-2',
            status: 'submitted',
          });
        }),
      );

      const result = await submitProjectPatternExtraction('proj-1', {
        source_type: 'mythology',
      });

      expect(result.extraction_id).toBe('extract-2');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/projects/proj-missing/extract-patterns', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(submitProjectPatternExtraction('proj-missing', { source_type: 'narrative' })).rejects.toThrow();
    });
  });

  describe('getExtractionStatus', () => {
    it('returns extraction progress', async () => {
      server.use(
        http.get('/v1/projects/extraction/extract-1', () => {
          return HttpResponse.json({
            extraction_id: 'extract-1',
            status: 'completed',
          });
        }),
      );

      const result = await getExtractionStatus('extract-1');

      expect(result.status).toBe('completed');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/projects/extraction/extract-missing', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getExtractionStatus('extract-missing')).rejects.toThrow();
    });
  });
});

