import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { submitImport, getImportStatus, importStory } from './storyImport';

describe('storyImport service', () => {
  describe('submitImport', () => {
    it('submits an import and returns submission response (202)', async () => {
      server.use(
        http.post('/projects/import-story', () => {
          return HttpResponse.json({
            import_id: 'import-1',
            status: 'submitted',
          }, { status: 202 });
        }),
      );

      const formData = new FormData();
      formData.append('story_text', 'Once upon a time...');
      formData.append('project_name', 'Test Project');

      const result = await submitImport(formData);

      expect(result.import_id).toBe('import-1');
      expect(result.status).toBe('submitted');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/projects/import-story', () => {
          return HttpResponse.json({ detail: 'Bad request' }, { status: 400 });
        }),
      );

      const formData = new FormData();
      formData.append('story_text', '');
      await expect(submitImport(formData)).rejects.toThrow();
    });
  });

  describe('getImportStatus', () => {
    it('returns import progress', async () => {
      server.use(
        http.get('/projects/import/import-1', () => {
          return HttpResponse.json({
            import_id: 'import-1',
            status: 'in_progress',
            progress: 0.5,
          });
        }),
      );

      const result = await getImportStatus('import-1');

      expect(result.status).toBe('in_progress');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/projects/import/import-missing', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getImportStatus('import-missing')).rejects.toThrow();
    });
  });

  describe('importStory', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('submits and polls until completed', async () => {
      let pollCount = 0;

      server.use(
        http.post('/projects/import-story', () => {
          return HttpResponse.json({
            import_id: 'import-1',
            status: 'submitted',
          }, { status: 202 });
        }),
        http.get('/projects/import/import-1', () => {
          pollCount++;
          if (pollCount < 3) {
            return HttpResponse.json({
              import_id: 'import-1',
              status: 'in_progress',
              progress: pollCount / 3,
            });
          }
          return HttpResponse.json({
            import_id: 'import-1',
            status: 'completed',
            result: { project_id: 'proj-imported', status: 'completed' },
          });
        }),
      );

      const promise = importStory({
        story_text: 'Once upon a time...',
        project_name: 'Test Project',
      });

      await vi.advanceTimersByTimeAsync(4000);

      const result = await promise;

      expect(result.status).toBe('completed');
    });

    it('throws when import fails', async () => {
      server.use(
        http.post('/projects/import-story', () => {
          return HttpResponse.json({
            import_id: 'import-fail',
            status: 'submitted',
          }, { status: 202 });
        }),
        http.get('/projects/import/import-fail', () => {
          return HttpResponse.json({
            import_id: 'import-fail',
            status: 'failed',
            error: 'Parsing failed',
          });
        }),
      );

      await expect(
        importStory({ story_text: 'Bad text', project_name: 'Test Project' }),
      ).rejects.toThrow('Parsing failed');
    });
  });
});
