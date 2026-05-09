import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { submitMythosExtraction, getExtractionStatus } from './mythosExtraction';

describe('mythosExtraction service', () => {
  describe('submitMythosExtraction', () => {
    it('submits mythos extraction request', async () => {
      server.use(
        http.post('/v1/projects/import-mythos', () => {
          return HttpResponse.json({
            extraction_id: 'mythos-1',
            status: 'submitted',
          });
        }),
      );

      const result = await submitMythosExtraction({
        text: 'Cosmic horror text...',
        generation_mode: 'same_world',
      });

      expect(result.extraction_id).toBe('mythos-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/projects/import-mythos', () => {
          return HttpResponse.json({ detail: 'Bad request' }, { status: 400 });
        }),
      );

      await expect(submitMythosExtraction({ text: '', generation_mode: 'same_world' })).rejects.toThrow();
    });
  });

  describe('getExtractionStatus', () => {
    it('re-exports getExtractionStatus from patternExtraction', async () => {
      server.use(
        http.get('/v1/projects/extraction/mythos-1', () => {
          return HttpResponse.json({
            extraction_id: 'mythos-1',
            status: 'completed',
          });
        }),
      );

      const result = await getExtractionStatus('mythos-1');

      expect(result.status).toBe('completed');
    });
  });
});

