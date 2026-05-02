import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../__tests__/setup';
import {
  createPatternEntry,
  deletePatternEntry,
  getPatternEntries,
  materializePatternExtraction,
  updatePatternEntry,
} from './patternLibrary';

describe('patternLibrary service', () => {
  it('supports CRUD and materialization', async () => {
    server.use(
      http.get('/v1/patterns/entries', () => HttpResponse.json([])),
      http.post('/v1/patterns/entries', () =>
        HttpResponse.json(
          {
            pattern_id: 'pattern-1',
            project_id: 'project-1',
            pattern_type: 'plot',
            name: 'Hero Return',
            summary: '',
            source_type: 'manual',
            generation_modes: [],
            beats: [],
            constraints: [],
            transposition_notes: '',
          },
          { status: 201 },
        ),
      ),
      http.patch('/v1/patterns/entries/pattern-1', () =>
        HttpResponse.json(
          {
            pattern_id: 'pattern-1',
            project_id: 'project-1',
            pattern_type: 'plot',
            name: 'Hero Return Updated',
            summary: '',
            source_type: 'manual',
            generation_modes: [],
            beats: [],
            constraints: [],
            transposition_notes: '',
          },
        ),
      ),
      http.delete('/v1/patterns/entries/pattern-1', () => new HttpResponse(null, { status: 200 })),
      http.post('/v1/patterns/materialize-extraction', () => HttpResponse.json([])),
    );

    expect((await getPatternEntries('project-1')).length).toBe(0);
    expect((await createPatternEntry({
      project_id: 'project-1',
      pattern_type: 'plot',
      name: 'Hero Return',
    })).pattern_id).toBe('pattern-1');
    expect((await updatePatternEntry('pattern-1', 'project-1', { name: 'Hero Return Updated' })).name).toBe(
      'Hero Return Updated',
    );
    await deletePatternEntry('project-1', 'pattern-1');
    expect(await materializePatternExtraction('project-1', 'extract-1')).toEqual([]);
  });
});
