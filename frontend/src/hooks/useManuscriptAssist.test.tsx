import { describe, expect, it, beforeEach, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import type {
  ApplyAssistSuggestionResponse,
  LLMRevisionSuggestion,
  ManuscriptAssistResult,
} from '../types/manuscriptAssist';
import { useManuscriptAssist } from './useManuscriptAssist';
import {
  applyLLMSuggestion,
  getLLMSuggestions,
  getManuscriptAssistGates,
  listManuscriptAssists,
  rejectLLMSuggestion,
  submitManuscriptAssist,
} from '../services/manuscriptAssist';

vi.mock('../services/manuscriptAssist', () => ({
  applyLLMSuggestion: vi.fn(),
  archiveLLMSuggestion: vi.fn(),
  getLLMSuggestions: vi.fn(),
  getManuscriptAssist: vi.fn(),
  getManuscriptAssistGates: vi.fn(),
  listManuscriptAssists: vi.fn(),
  rejectLLMSuggestion: vi.fn(),
  retryManuscriptAssist: vi.fn(),
  submitManuscriptAssist: vi.fn(),
}));

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const createWrapper = (queryClient: QueryClient) => (
  { children }: { children: ReactNode },
) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const assistRun: ManuscriptAssistResult = {
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
};

const suggestion: LLMRevisionSuggestion = {
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
};

const applyResponse: ApplyAssistSuggestionResponse = {
  suggestion: {
    ...suggestion,
    range: null,
    status: 'ACCEPTED',
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
};

describe('useManuscriptAssist', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(listManuscriptAssists).mockResolvedValue([assistRun]);
    vi.mocked(getLLMSuggestions).mockResolvedValue([suggestion]);
    vi.mocked(getManuscriptAssistGates).mockResolvedValue([]);
    vi.mocked(submitManuscriptAssist).mockResolvedValue(assistRun);
    vi.mocked(applyLLMSuggestion).mockResolvedValue(applyResponse);
    vi.mocked(rejectLLMSuggestion).mockResolvedValue({
      ...suggestion,
      range: null,
      status: 'REJECTED',
    });
  });

  it('builds selection range from editor offsets', () => {
    const queryClient = createQueryClient();
    const { result } = renderHook(
      () =>
        useManuscriptAssist({
          projectId: 'proj-1',
          documentId: 'doc-1',
          documentVersion: 1,
          content: 'Hello world',
        }),
      { wrapper: createWrapper(queryClient) },
    );

    act(() => {
      result.current.setSelectionFromEditor(0, 5, 'Hello world');
    });

    expect(result.current.selectedRange?.selected_text).toBe('Hello');
    expect(result.current.selectedRange?.anchor_after).toContain(' world');
  });

  it('submits assist and applies/rejects llm suggestion', async () => {
    const queryClient = createQueryClient();
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(
      () =>
        useManuscriptAssist({
          projectId: 'proj-1',
          documentId: 'doc-1',
          documentVersion: 1,
          content: 'Hello world',
        }),
      { wrapper: createWrapper(queryClient) },
    );

    await waitFor(() => {
      expect(result.current.llmSuggestions).toHaveLength(1);
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

    expect(submitManuscriptAssist).toHaveBeenCalledWith({
      project_id: 'proj-1',
      document_id: 'doc-1',
      assist_kind: 'line_edit_selection',
      instruction: 'Tighten this selection',
      text_range: null,
      create_branch: undefined,
      create_draft_artifact: undefined,
    });
    expect(applyLLMSuggestion).toHaveBeenCalledWith({
      project_id: 'proj-1',
      document_id: 'doc-1',
      suggestion_id: 'sug-1',
      expected_document_version: 1,
      apply_mode: 'replace_range',
    });
    expect(rejectLLMSuggestion).toHaveBeenCalledWith('proj-1', 'sug-1');
    expect(getManuscriptAssistGates).toHaveBeenCalledWith('assist-1');
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['manuscript-assist', 'runs', 'proj-1', 'doc-1'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['manuscript-assist', 'suggestions', 'proj-1', 'doc-1', 'open'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['manuscript-documents', 'proj-1'],
    });
  });
});
