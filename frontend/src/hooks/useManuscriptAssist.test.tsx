import { describe, expect, it } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../__tests__/setup';
import { useManuscriptAssist } from './useManuscriptAssist';

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const WithProviders = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>{children}</QueryClientProvider>
);

describe('useManuscriptAssist', () => {
  it('builds selection range from editor offsets', () => {
    const { result } = renderHook(
      () =>
        useManuscriptAssist({
          projectId: 'proj-1',
          documentId: 'doc-1',
          documentVersion: 1,
          content: 'Hello world',
        }),
      { wrapper: WithProviders },
    );

    act(() => {
      result.current.setSelectionFromEditor(0, 5, 'Hello world');
    });

    expect(result.current.selectedRange?.selected_text).toBe('Hello');
    expect(result.current.selectedRange?.anchor_after).toContain(' world');
  });

  it('submits assist and applies/rejects llm suggestion', async () => {
    server.use(
      http.get('/v1/manuscript-assist/runs', () => HttpResponse.json([])),
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
              range: {
                start_offset: 0,
                end_offset: 5,
                selected_text: 'Hello',
                anchor_before: '',
                anchor_after: ' world',
              },
              canon_risk: 'none',
              confidence_score: 0.9,
              status: 'PENDING',
              source_context: [],
            },
          ],
        }),
      ),
      http.post('/v1/manuscript-assist/runs', () =>
        HttpResponse.json(
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
          { status: 202 },
        ),
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
      http.post('/v1/manuscript-assist/suggestions/sug-1/reject', () =>
        HttpResponse.json({
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
          status: 'REJECTED',
          source_context: [],
        }),
      ),
    );

    const { result } = renderHook(
      () =>
        useManuscriptAssist({
          projectId: 'proj-1',
          documentId: 'doc-1',
          documentVersion: 1,
          content: 'Hello world',
        }),
      { wrapper: WithProviders },
    );

    await waitFor(() => {
      expect(result.current.llmSuggestions.length).toBe(1);
    });

    await act(async () => {
      await result.current.submitAssist('line_edit_selection', 'Tighten this selection');
    });
    await act(async () => {
      await result.current.applySuggestion('sug-1');
    });
    await act(async () => {
      await result.current.rejectSuggestion('sug-1');
    });
  });
});
