import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../__tests__/setup';
import {
  createForkProject,
  createGenerationRun,
  getGenerationGates,
  getGenerationPacket,
  getGenerationRun,
  listGenerationRuns,
  previewFork,
  retryGenerationRun,
} from './storyGeneration';

const baseResponse = {
  generation_id: 'gen-1',
  source_project_id: 'source-project',
  target_project_id: 'source-project',
  job_ids: ['job-1'],
  status: 'queued',
  warnings: [],
  created_artifacts: [],
};

describe('storyGeneration service', () => {
  it('createGenerationRun posts request', async () => {
    server.use(
      http.post('/v1/story-generation/runs', () => HttpResponse.json(baseResponse, { status: 201 })),
    );
    const result = await createGenerationRun({
      source_project_id: 'source-project',
      mode: 'same_project_side_story',
      destination: { destination_kind: 'same_project', target_project_id: 'source-project' },
      canon_scope: {
        source_project_id: 'source-project',
        character_ids: ['char-1'],
        world_bible_refs: [],
        continuity_thread_ids: [],
        arc_ids: [],
        include_relationships: true,
        include_unresolved_questions: true,
        include_contradictions_as_forbidden: true,
      },
      generation_brief: 'Generate side story.',
      target_chapter_count: 2,
    });
    expect(result.generation_id).toBe('gen-1');
  });

  it('get/list/retry run endpoints', async () => {
    server.use(
      http.get('/v1/story-generation/runs/gen-1', () => HttpResponse.json(baseResponse)),
      http.get('/v1/story-generation/runs', () => HttpResponse.json([baseResponse])),
      http.post('/v1/story-generation/runs/gen-1/retry', () => HttpResponse.json(baseResponse)),
    );
    expect((await getGenerationRun('gen-1')).generation_id).toBe('gen-1');
    expect((await listGenerationRuns('source-project')).length).toBe(1);
    expect((await retryGenerationRun('gen-1')).generation_id).toBe('gen-1');
  });

  it('packet and gates endpoints', async () => {
    server.use(
      http.get('/v1/story-generation/runs/gen-1/packet', () => HttpResponse.json({ packet_id: 'packet-1' })),
      http.get('/v1/story-generation/runs/gen-1/gates', () => HttpResponse.json({ generation_id: 'gen-1', items: [] })),
    );
    const packet = await getGenerationPacket('gen-1');
    const gates = await getGenerationGates('gen-1');
    expect(packet.packet_id).toBe('packet-1');
    expect(gates).toEqual([]);
  });

  it('previewFork and createForkProject endpoints', async () => {
    server.use(
      http.post('/v1/story-generation/fork-preview', () =>
        HttpResponse.json({
          source_project_id: 'source-project',
          mode: 'same_project_side_story',
          destination_kind: 'same_project',
          selected_character_ids: ['char-1'],
          selected_world_bible_refs: [],
          selected_continuity_thread_ids: [],
          selected_arc_ids: [],
          warnings: [],
        }),
      ),
      http.post('/v1/story-generation/fork-project', () => HttpResponse.json(baseResponse, { status: 201 })),
    );
    const preview = await previewFork({
      source_project_id: 'source-project',
      mode: 'same_project_side_story',
      destination: { destination_kind: 'same_project', target_project_id: 'source-project' },
      canon_scope: {
        source_project_id: 'source-project',
        character_ids: ['char-1'],
        world_bible_refs: [],
        continuity_thread_ids: [],
        arc_ids: [],
        include_relationships: true,
        include_unresolved_questions: true,
        include_contradictions_as_forbidden: true,
      },
      generation_brief: 'Generate side story.',
      target_chapter_count: 2,
    });
    const run = await createForkProject({
      source_project_id: 'source-project',
      mode: 'same_project_side_story',
      destination: { destination_kind: 'same_project', target_project_id: 'source-project' },
      canon_scope: {
        source_project_id: 'source-project',
        character_ids: ['char-1'],
        world_bible_refs: [],
        continuity_thread_ids: [],
        arc_ids: [],
        include_relationships: true,
        include_unresolved_questions: true,
        include_contradictions_as_forbidden: true,
      },
      generation_brief: 'Generate side story.',
      target_chapter_count: 2,
    });
    expect(preview.selected_character_ids).toEqual(['char-1']);
    expect(run.generation_id).toBe('gen-1');
  });
});
