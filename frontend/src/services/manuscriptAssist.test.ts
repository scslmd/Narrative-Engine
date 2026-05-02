import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../__tests__/setup';
import {
  applyLLMSuggestion,
  getLLMSuggestions,
  listManuscriptAssists,
  submitManuscriptAssist,
} from './manuscriptAssist';

describe('manuscriptAssist service', () => {
  it('submit and list runs', async () => {
    server.use(
      http.post('/v1/manuscript-assist/runs', () =>
        HttpResponse.json({
          assist_id: 'assist-1',
          project_id: 'proj-1',
          document_id: 'doc-1',
          assist_kind: 'line_edit_selection',
          status: 'queued',
          summary: '',
          suggestions: [],
          gate_results: [],
          job_ids: [],
          warnings: [],
        }, { status: 202 }),
      ),
      http.get('/v1/manuscript-assist/runs', () =>
        HttpResponse.json([
          {
            assist_id: 'assist-1',
            project_id: 'proj-1',
            document_id: 'doc-1',
            assist_kind: 'line_edit_selection',
            status: 'queued',
            summary: '',
            suggestions: [],
            gate_results: [],
            job_ids: [],
            warnings: [],
          },
        ]),
      ),
    );
    const created = await submitManuscriptAssist({
      project_id: 'proj-1',
      document_id: 'doc-1',
      assist_kind: 'line_edit_selection',
      instruction: 'Tighten prose',
      text_range: {
        start_offset: 0,
        end_offset: 5,
        selected_text: 'Hello',
        anchor_before: '',
        anchor_after: ' world',
      },
    });
    const listed = await listManuscriptAssists('proj-1', 'doc-1');
    expect(created.assist_id).toBe('assist-1');
    expect(listed.length).toBe(1);
  });

  it('get suggestions and apply suggestion', async () => {
    server.use(
      http.get('/v1/manuscript-assist/suggestions', () =>
        HttpResponse.json({
          project_id: 'proj-1',
          document_id: 'doc-1',
          items: [
            {
              suggestion_id: 'sug-1',
              assist_id: 'assist-1',
              project_id: 'proj-1',
              target_document_id: 'doc-1',
              source_text: 'Hello',
              proposed_text: 'Hi',
              rationale: 'Shorter',
              suggestion_kind: 'line_edit_selection',
              range: null,
              canon_risk: 'none',
              confidence_score: 0.9,
              status: 'PENDING',
              source_context: [],
            },
          ],
        }),
      ),
      http.post('/v1/manuscript-assist/suggestions/sug-1/apply', () =>
        HttpResponse.json({
          suggestion: {
            suggestion_id: 'sug-1',
            assist_id: 'assist-1',
            project_id: 'proj-1',
            target_document_id: 'doc-1',
            source_text: 'Hello',
            proposed_text: 'Hi',
            rationale: 'Shorter',
            suggestion_kind: 'line_edit_selection',
            range: null,
            canon_risk: 'none',
            confidence_score: 0.9,
            status: 'ACCEPTED',
            source_context: [],
          },
          manuscript: {
            document_id: 'doc-1',
            project_id: 'proj-1',
            title: 'Chapter 1',
            content: 'Hi world',
            chapter_id: null,
            scene_id: null,
            current_draft_artifact_id: null,
            version: 2,
          },
        }),
      ),
    );
    const suggestions = await getLLMSuggestions('proj-1', 'doc-1');
    const applied = await applyLLMSuggestion({
      project_id: 'proj-1',
      document_id: 'doc-1',
      suggestion_id: 'sug-1',
      expected_document_version: 1,
      apply_mode: 'replace_range',
    });
    expect(suggestions[0].suggestion_id).toBe('sug-1');
    expect(applied.manuscript.version).toBe(2);
  });
});
