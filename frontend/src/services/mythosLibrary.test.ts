import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../__tests__/setup';
import {
  createMythosEntry,
  deleteMythosEntry,
  getMythosEntries,
  materializeMythosExtraction,
  updateMythosEntry,
} from './mythosLibrary';

describe('mythosLibrary service', () => {
  it('supports CRUD and materialization', async () => {
    server.use(
      http.get('/v1/mythos/entries', () => HttpResponse.json([])),
      http.post('/v1/mythos/entries', () =>
        HttpResponse.json(
          {
            mythos_id: 'mythos-1',
            project_id: 'project-1',
            entry_type: 'motif',
            name: 'Storm Crown',
            summary: '',
            canonical_facts: [],
            pattern_notes: [],
            generation_guidance: '',
            visibility_scope: 'project',
          },
          { status: 201 },
        ),
      ),
      http.patch('/v1/mythos/entries/mythos-1', () =>
        HttpResponse.json(
          {
            mythos_id: 'mythos-1',
            project_id: 'project-1',
            entry_type: 'motif',
            name: 'Storm Crown Updated',
            summary: '',
            canonical_facts: [],
            pattern_notes: [],
            generation_guidance: '',
            visibility_scope: 'project',
          },
        ),
      ),
      http.delete('/v1/mythos/entries/mythos-1', () => new HttpResponse(null, { status: 200 })),
      http.post('/v1/mythos/materialize-extraction', () => HttpResponse.json([])),
    );

    expect((await getMythosEntries('project-1')).length).toBe(0);
    expect((await createMythosEntry({
      project_id: 'project-1',
      entry_type: 'motif',
      name: 'Storm Crown',
    })).mythos_id).toBe('mythos-1');
    expect((await updateMythosEntry('mythos-1', 'project-1', { name: 'Storm Crown Updated' })).name).toBe(
      'Storm Crown Updated',
    );
    await deleteMythosEntry('project-1', 'mythos-1');
    expect(await materializeMythosExtraction('project-1', 'extract-1')).toEqual([]);
  });
});
