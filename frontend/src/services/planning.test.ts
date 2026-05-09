import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import {
  getSequencePlans,
  getSequencePlan,
  getChapterPlans,
  getChapterPlan,
  getScenePlans,
  getScenePlan,
  getBeatPlans,
  getBeatPlan,
  getPlanningDependencies,
  getChapterPackets,
  getChapterPacket,
  createSequencePlan,
  updateSequencePlan,
  createChapterPlan,
  updateChapterPlan,
  createScenePlan,
  updateScenePlan,
  createBeatPlan,
  updateBeatPlan,
  createChapterPacket,
  reorderPlanObjects,
} from './planning';

describe('planning service', () => {
  describe('getSequencePlans', () => {
    it('returns list of sequence plans', async () => {
      server.use(
        http.get('/v1/story-development/planning/sequence-plans', () =>
          HttpResponse.json({ project_id: 'proj-1', items: [{ sequence_id: 'seq-1' }], meta: {} }),
        ),
      );

      const result = await getSequencePlans('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/planning/sequence-plans', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getSequencePlans('proj-missing')).rejects.toThrow();
    });
  });

  describe('getChapterPlans', () => {
    it('returns list of chapter plans', async () => {
      server.use(
        http.get('/v1/story-development/planning/chapter-plans', () =>
          HttpResponse.json({ project_id: 'proj-1', items: [{ chapter_id: 'ch-1' }], meta: {} }),
        ),
      );

      const result = await getChapterPlans('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/planning/chapter-plans', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getChapterPlans('proj-missing')).rejects.toThrow();
    });
  });

  describe('getScenePlans', () => {
    it('returns list of scene plans', async () => {
      server.use(
        http.get('/v1/story-development/planning/scene-plans', () =>
          HttpResponse.json({ project_id: 'proj-1', items: [{ scene_id: 'sc-1' }], meta: {} }),
        ),
      );

      const result = await getScenePlans('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/planning/scene-plans', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getScenePlans('proj-missing')).rejects.toThrow();
    });
  });

  describe('getBeatPlans', () => {
    it('returns list of beat plans', async () => {
      server.use(
        http.get('/v1/story-development/planning/beat-plans', () =>
          HttpResponse.json({ project_id: 'proj-1', items: [{ beat_id: 'bt-1' }], meta: {} }),
        ),
      );

      const result = await getBeatPlans('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/planning/beat-plans', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getBeatPlans('proj-missing')).rejects.toThrow();
    });
  });

  describe('getPlanningDependencies', () => {
    it('returns planning dependencies', async () => {
      server.use(
        http.get('/v1/story-development/planning/dependencies', () =>
          HttpResponse.json({ project_id: 'proj-1', items: [{ dependency_id: 'dep-1' }], meta: {} }),
        ),
      );

      const result = await getPlanningDependencies('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/planning/dependencies', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getPlanningDependencies('proj-missing')).rejects.toThrow();
    });
  });

  describe('getChapterPackets', () => {
    it('returns chapter packets', async () => {
      server.use(
        http.get('/v1/story-development/planning/chapter-packets', () =>
          HttpResponse.json({ project_id: 'proj-1', items: [{ packet_id: 'pkt-1' }], meta: {} }),
        ),
      );

      const result = await getChapterPackets('proj-1');
      expect(result).toHaveLength(1);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/planning/chapter-packets', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getChapterPackets('proj-missing')).rejects.toThrow();
    });
  });

  describe('getSequencePlan', () => {
    it('returns a single sequence plan', async () => {
      server.use(
        http.get('/v1/story-development/planning/sequence-plans/seq-1', () =>
          HttpResponse.json({ sequence_id: 'seq-1', title: 'Act One' }),
        ),
      );

      const result = await getSequencePlan('seq-1', 'proj-1');
      expect(result.sequence_id).toBe('seq-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/planning/sequence-plans/seq-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getSequencePlan('seq-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('getChapterPlan', () => {
    it('returns a single chapter plan', async () => {
      server.use(
        http.get('/v1/story-development/planning/chapter-plans/ch-1', () =>
          HttpResponse.json({ chapter_id: 'ch-1', title: 'Chapter One' }),
        ),
      );

      const result = await getChapterPlan('ch-1', 'proj-1');
      expect(result.chapter_id).toBe('ch-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/planning/chapter-plans/ch-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getChapterPlan('ch-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('getScenePlan', () => {
    it('returns a single scene plan', async () => {
      server.use(
        http.get('/v1/story-development/planning/scene-plans/sc-1', () =>
          HttpResponse.json({ scene_id: 'sc-1', title: 'Opening Scene' }),
        ),
      );

      const result = await getScenePlan('sc-1', 'proj-1');
      expect(result.scene_id).toBe('sc-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/planning/scene-plans/sc-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getScenePlan('sc-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('getBeatPlan', () => {
    it('returns a single beat plan', async () => {
      server.use(
        http.get('/v1/story-development/planning/beat-plans/bt-1', () =>
          HttpResponse.json({ beat_id: 'bt-1', objective: 'Inciting incident' }),
        ),
      );

      const result = await getBeatPlan('bt-1', 'proj-1');
      expect(result.beat_id).toBe('bt-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/planning/beat-plans/bt-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getBeatPlan('bt-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('getChapterPacket', () => {
    it('returns a single chapter packet', async () => {
      server.use(
        http.get('/v1/story-development/planning/chapter-packets/pkt-1', () =>
          HttpResponse.json({ packet_id: 'pkt-1', chapter_id: 'ch-1' }),
        ),
      );

      const result = await getChapterPacket('pkt-1', 'proj-1');
      expect(result.packet_id).toBe('pkt-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/planning/chapter-packets/pkt-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(getChapterPacket('pkt-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('createSequencePlan', () => {
    it('creates a sequence plan (201)', async () => {
      server.use(
        http.post('/v1/story-development/planning/sequence-plans', () =>
          HttpResponse.json({ sequence_id: 'seq-new' }, { status: 201 }),
        ),
      );

      const result = await createSequencePlan('proj-1', {
        project_id: 'proj-1',
        sequence_id: 'seq-new',
        title: 'New Sequence',
      });
      expect(result.sequence_id).toBe('seq-new');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/planning/sequence-plans', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createSequencePlan('proj-1', {
        project_id: 'proj-1',
        sequence_id: 'seq-bad',
        title: '',
      })).rejects.toThrow();
    });
  });

  describe('updateSequencePlan', () => {
    it('updates a sequence plan (200)', async () => {
      server.use(
        http.patch('/v1/story-development/planning/sequence-plans/seq-1', () =>
          HttpResponse.json({ sequence_id: 'seq-1', title: 'Updated' }),
        ),
      );

      const result = await updateSequencePlan('seq-1', 'proj-1', { title: 'Updated' });
      expect(result.title).toBe('Updated');
    });

    it('throws on error response', async () => {
      server.use(
        http.patch('/v1/story-development/planning/sequence-plans/seq-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(updateSequencePlan('seq-missing', 'proj-1', {})).rejects.toThrow();
    });
  });

  describe('createChapterPlan', () => {
    it('creates a chapter plan (201)', async () => {
      server.use(
        http.post('/v1/story-development/planning/chapter-plans', () =>
          HttpResponse.json({ chapter_id: 'ch-new' }, { status: 201 }),
        ),
      );

      const result = await createChapterPlan('proj-1', {
        project_id: 'proj-1',
        chapter_id: 'ch-new',
        title: 'New Chapter',
        objective: 'Goal',
        conflict: 'Conflict',
        stakes: 'Stakes',
      });
      expect(result.chapter_id).toBe('ch-new');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/planning/chapter-plans', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createChapterPlan('proj-1', {
        project_id: 'proj-1',
        chapter_id: 'ch-bad',
        title: '',
        objective: '',
        conflict: '',
        stakes: '',
      })).rejects.toThrow();
    });
  });

  describe('updateChapterPlan', () => {
    it('updates a chapter plan (200)', async () => {
      server.use(
        http.patch('/v1/story-development/planning/chapter-plans/ch-1', () =>
          HttpResponse.json({ chapter_id: 'ch-1', title: 'Updated' }),
        ),
      );

      const result = await updateChapterPlan('ch-1', 'proj-1', { title: 'Updated' });
      expect(result.title).toBe('Updated');
    });

    it('throws on error response', async () => {
      server.use(
        http.patch('/v1/story-development/planning/chapter-plans/ch-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(updateChapterPlan('ch-missing', 'proj-1', {})).rejects.toThrow();
    });
  });

  describe('createScenePlan', () => {
    it('creates a scene plan (201)', async () => {
      server.use(
        http.post('/v1/story-development/planning/scene-plans', () =>
          HttpResponse.json({ scene_id: 'sc-new' }, { status: 201 }),
        ),
      );

      const result = await createScenePlan('proj-1', {
        project_id: 'proj-1',
        scene_id: 'sc-new',
        title: 'New Scene',
        objective: 'Goal',
        conflict: 'Conflict',
        stakes: 'Stakes',
      });
      expect(result.scene_id).toBe('sc-new');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/planning/scene-plans', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createScenePlan('proj-1', {
        project_id: 'proj-1',
        scene_id: 'sc-bad',
        title: '',
        objective: '',
        conflict: '',
        stakes: '',
      })).rejects.toThrow();
    });
  });

  describe('updateScenePlan', () => {
    it('updates a scene plan (200)', async () => {
      server.use(
        http.patch('/v1/story-development/planning/scene-plans/sc-1', () =>
          HttpResponse.json({ scene_id: 'sc-1', title: 'Updated' }),
        ),
      );

      const result = await updateScenePlan('sc-1', 'proj-1', { title: 'Updated' });
      expect(result.title).toBe('Updated');
    });

    it('throws on error response', async () => {
      server.use(
        http.patch('/v1/story-development/planning/scene-plans/sc-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(updateScenePlan('sc-missing', 'proj-1', {})).rejects.toThrow();
    });
  });

  describe('createBeatPlan', () => {
    it('creates a beat plan (201)', async () => {
      server.use(
        http.post('/v1/story-development/planning/beat-plans', () =>
          HttpResponse.json({ beat_id: 'bt-new' }, { status: 201 }),
        ),
      );

      const result = await createBeatPlan('proj-1', {
        project_id: 'proj-1',
        beat_id: 'bt-new',
        objective: 'Goal',
        conflict: 'Conflict',
        stakes: 'Stakes',
      });
      expect(result.beat_id).toBe('bt-new');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/planning/beat-plans', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createBeatPlan('proj-1', {
        project_id: 'proj-1',
        beat_id: 'bt-bad',
        objective: '',
        conflict: '',
        stakes: '',
      })).rejects.toThrow();
    });
  });

  describe('updateBeatPlan', () => {
    it('updates a beat plan (200)', async () => {
      server.use(
        http.patch('/v1/story-development/planning/beat-plans/bt-1', () =>
          HttpResponse.json({ beat_id: 'bt-1', objective: 'Updated' }),
        ),
      );

      const result = await updateBeatPlan('bt-1', 'proj-1', { objective: 'Updated' });
      expect(result.objective).toBe('Updated');
    });

    it('throws on error response', async () => {
      server.use(
        http.patch('/v1/story-development/planning/beat-plans/bt-missing', () =>
          HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
        ),
      );

      await expect(updateBeatPlan('bt-missing', 'proj-1', {})).rejects.toThrow();
    });
  });

  describe('createChapterPacket', () => {
    it('creates a chapter packet (201)', async () => {
      server.use(
        http.post('/v1/story-development/planning/chapter-packets', () =>
          HttpResponse.json({ packet_id: 'pkt-new' }, { status: 201 }),
        ),
      );

      const result = await createChapterPacket('proj-1', {
        project_id: 'proj-1',
        packet_id: 'pkt-new',
        chapter_id: 'ch-1',
      });
      expect(result.packet_id).toBe('pkt-new');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/planning/chapter-packets', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(createChapterPacket('proj-1', {
        project_id: 'proj-1',
        packet_id: 'pkt-bad',
        chapter_id: '',
      })).rejects.toThrow();
    });
  });

  describe('reorderPlanObjects', () => {
    it('reorders plan objects (200)', async () => {
      server.use(
        http.post('/v1/story-development/planning/reorder', () => HttpResponse.json(null)),
      );

      await expect(reorderPlanObjects({
        project_id: 'proj-1',
        plan_kind: 'sequence',
        ordered_plan_ids: ['seq-1', 'seq-2'],
      })).resolves.toBeUndefined();
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/planning/reorder', () =>
          HttpResponse.json({ detail: 'Bad request' }, { status: 400 }),
        ),
      );

      await expect(reorderPlanObjects({
        project_id: 'proj-1',
        plan_kind: 'sequence',
        ordered_plan_ids: [],
      })).rejects.toThrow();
    });
  });
});

