import { describe, expect, it, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMergedSuggestions } from './useMergedSuggestions';
import type { RevisionSuggestion } from '../types/aids';
import type { LLMRevisionSuggestion } from '../types/manuscriptAssist';

const revisionSuggestion: RevisionSuggestion = {
  suggestion_id: 'rev-1',
  project_id: 'proj-1',
  target_document_id: 'doc-1',
  source_text: 'old text',
  proposed_text: 'new text',
  rationale: 'test rationale',
  source_context: [],
  status: 'PENDING',
};

const llmSuggestion: LLMRevisionSuggestion = {
  suggestion_id: 'llm-1',
  assist_id: 'assist-1',
  project_id: 'proj-1',
  target_document_id: 'doc-1',
  source_text: 'old',
  proposed_text: 'new',
  rationale: 'llm rationale',
  suggestion_kind: 'line_edit_selection',
  canon_risk: 'none',
  confidence_score: 0.9,
  status: 'PENDING',
  source_context: [],
};

const baseArgs = {
  revisionSuggestions: [revisionSuggestion],
  llmSuggestions: [llmSuggestion],
  onRevisionAccept: vi.fn(),
  onRevisionReject: vi.fn(),
  onLlmAccept: vi.fn(),
  onLlmReject: vi.fn(),
  onLlmArchive: vi.fn(),
};

describe('useMergedSuggestions', () => {
  it('returns revision and LLM suggestions as one merged array', () => {
    const { result } = renderHook(() => useMergedSuggestions(baseArgs));

    expect(result.current.suggestions).toHaveLength(2);
    expect(result.current.suggestions[0].suggestion_id).toBe('rev-1');
    expect(result.current.suggestions[1].suggestion_id).toBe('llm-1');
  });

  it('maps LLM ARCHIVED status to REJECTED in merged output', () => {
    const archivedLlm: LLMRevisionSuggestion = {
      ...llmSuggestion,
      suggestion_id: 'llm-archived',
      status: 'ARCHIVED',
    };

    const { result } = renderHook(() =>
      useMergedSuggestions({
        ...baseArgs,
        llmSuggestions: [archivedLlm],
      }),
    );

    const merged = result.current.suggestions.find(
      (s) => s.suggestion_id === 'llm-archived',
    );
    expect(merged).toBeDefined();
    expect(merged!.status).toBe('REJECTED');
  });

  it('accepting an LLM suggestion calls onLlmAccept', async () => {
    const onLlmAccept = vi.fn().mockResolvedValue(undefined);
    const onRevisionAccept = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useMergedSuggestions({
        ...baseArgs,
        onLlmAccept,
        onRevisionAccept,
      }),
    );

    await act(async () => {
      await result.current.handleSuggestionAccept('llm-1');
    });

    expect(onLlmAccept).toHaveBeenCalledWith('llm-1');
    expect(onRevisionAccept).not.toHaveBeenCalled();
  });

  it('accepting a non-LLM suggestion calls onRevisionAccept', async () => {
    const onLlmAccept = vi.fn().mockResolvedValue(undefined);
    const onRevisionAccept = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useMergedSuggestions({
        ...baseArgs,
        onLlmAccept,
        onRevisionAccept,
      }),
    );

    await act(async () => {
      await result.current.handleSuggestionAccept('rev-1');
    });

    expect(onRevisionAccept).toHaveBeenCalledWith('rev-1');
    expect(onLlmAccept).not.toHaveBeenCalled();
  });
});
