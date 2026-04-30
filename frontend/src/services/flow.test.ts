import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { flowService } from './flow';

const mockStage = {
  stage_id: 'stage-1',
  project_id: 'proj-1',
  stage_kind: 'architect' as any,
  display_name: 'Architect',
  description: null,
};

describe('flow service', () => {
  describe('getStages', () => {
    it('returns list of flow stages for a project', async () => {
      server.use(
        http.get('/story-development/flow/stages', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockStage],
            meta: {},
          });
        }),
      );

      const result = await flowService.getStages('proj-1');

      expect(result).toHaveLength(1);
      expect(result[0].stage_id).toBe('stage-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/flow/stages', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(flowService.getStages('proj-missing')).rejects.toThrow();
    });
  });

  describe('addStage', () => {
    it('creates a new flow stage (201)', async () => {
      server.use(
        http.post('/story-development/flow/stages', () => {
          return HttpResponse.json({ ...mockStage, stage_kind: 'drafting' }, { status: 201 });
        }),
      );

      const result = await flowService.addStage('proj-1', 'drafting', 'Custom Drafter');

      expect(result.stage_kind).toBe('drafting');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/flow/stages', () => {
          return HttpResponse.json({ detail: 'Bad request' }, { status: 400 });
        }),
      );

      await expect(flowService.addStage('proj-1', 'drafting')).rejects.toThrow();
    });
  });

  describe('updateStageWithProject', () => {
    it('updates a flow stage (200)', async () => {
      server.use(
        http.patch('/story-development/flow/stages/stage-1', () => {
          return HttpResponse.json({ ...mockStage, display_name: 'Updated Name' });
        }),
      );

      const result = await flowService.updateStageWithProject('proj-1', 'stage-1', {
        display_name: 'Updated Name',
      });

      expect(result.display_name).toBe('Updated Name');
    });

    it('throws on error response', async () => {
      server.use(
        http.patch('/story-development/flow/stages/stage-bad', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(flowService.updateStageWithProject('proj-1', 'stage-bad', {})).rejects.toThrow();
    });
  });

  describe('deleteStage', () => {
    it('deletes a flow stage (200)', async () => {
      server.use(
        http.delete('/story-development/flow/stages/stage-1', () => {
          return HttpResponse.json(null);
        }),
      );

      await expect(flowService.deleteStage('proj-1', 'stage-1')).resolves.toBeUndefined();
    });

    it('throws on error response', async () => {
      server.use(
        http.delete('/story-development/flow/stages/stage-bad', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(flowService.deleteStage('proj-1', 'stage-bad')).rejects.toThrow();
    });
  });

  describe('archiveStage', () => {
    it('archives a stage by updating state to ARCHIVED', async () => {
      server.use(
        http.patch('/story-development/flow/stages/stage-1', () => {
          return HttpResponse.json({ ...mockStage, stage_configuration_state: 'ARCHIVED' });
        }),
      );

      const result = await flowService.archiveStage('proj-1', 'stage-1');

      expect(result.stage_configuration_state).toBe('ARCHIVED');
    });
  });

  describe('renameStage', () => {
    it('renames a stage by updating display_name', async () => {
      server.use(
        http.patch('/story-development/flow/stages/stage-1', () => {
          return HttpResponse.json({ ...mockStage, display_name: 'New Name' });
        }),
      );

      const result = await flowService.renameStage('proj-1', 'stage-1', 'New Name');

      expect(result.display_name).toBe('New Name');
    });
  });
});
