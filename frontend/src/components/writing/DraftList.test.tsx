import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { DraftList } from './DraftList';

function createProps(overrides = {}) {
  return {
    artifacts: [],
    expandedDraft: null,
    draftForm: null,
    isPending: false,
    promotePending: false,
    continuePending: false,
    alternatePending: false,
    isLoading: false,
    isDark: false,
    onCreateDraft: vi.fn(),
    onSubmitDraft: vi.fn(),
    onCancelDraft: vi.fn(),
    onTitleChange: vi.fn(),
    onContentChange: vi.fn(),
    onToggleDraft: vi.fn(),
    onPromoteDraft: vi.fn(),
    onContinueDraft: vi.fn(),
    onAlternateVariant: vi.fn(),
    onGenerateAIDraft: vi.fn(),
    ...overrides,
  };
}

describe('DraftList', () => {
  let props: ReturnType<typeof createProps>;

  beforeEach(() => {
    props = createProps();
  });

  it('shows split button with manual and AI options in empty state', () => {
    render(<DraftList {...props} />);
    expect(screen.getByText('+ New Draft')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Generate with AI/i })).toBeInTheDocument();
  });

  it('calls onCreateDraft when manual button is clicked', () => {
    render(<DraftList {...props} />);
    const manualBtn = screen.getByText('+ New Draft');
    fireEvent.click(manualBtn);
    expect(props.onCreateDraft).toHaveBeenCalledTimes(1);
    expect(props.onGenerateAIDraft).not.toHaveBeenCalled();
  });

  it('calls onGenerateAIDraft when AI button is clicked', () => {
    render(<DraftList {...props} />);
    const aiBtn = screen.getByRole('button', { name: /Generate with AI/i });
    fireEvent.click(aiBtn);
    expect(props.onGenerateAIDraft).toHaveBeenCalledTimes(1);
    expect(props.onCreateDraft).not.toHaveBeenCalled();
  });

  it('shows split button at bottom when drafts exist', () => {
    render(<DraftList {...props} artifacts={[{
      artifact_id: 'art-1',
      project_id: 'proj-1',
      title: 'Existing Draft',
      content: 'Some content',
      source_plan_ids: [],
      source_context: [],
      provenance_note: null,
      status: 'DRAFT',
    }]} />);
    expect(screen.getByText('Existing Draft')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Generate with AI/i })).toBeInTheDocument();
  });
});
