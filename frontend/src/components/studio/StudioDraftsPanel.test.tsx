import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { StudioDraftsPanel } from './StudioDraftsPanel';

vi.mock('../../hooks/useWritingView', () => ({
  useWritingView: () => ({
    draftArtifacts: [],
    draftForm: null,
    expandedDraft: null,
    createDraftPending: false,
    promotePending: false,
    continuePending: false,
    alternatePending: false,
    draftsQueryLoading: false,
    handleCreateDraft: vi.fn(),
    handleSubmitDraft: vi.fn(),
    handleCancelDraft: vi.fn(),
    handleToggleDraft: vi.fn(),
    promoteDraft: vi.fn(),
    continueDraftAction: vi.fn(),
    alternateVariantAction: vi.fn(),
    setDraftForm: vi.fn(),
  }),
}));

vi.mock('../../domains/writing/useAssistController', () => ({
  useAssistController: () => ({
    draftFormAI: null,
    pendingDrafts: {},
    setDraftFormAI: vi.fn(),
    handleGenerateDraftForm: vi.fn(),
    handleGenerateDraft: vi.fn(),
    generateDraftPending: false,
  }),
}));

vi.mock('../../stores/themeStore', () => ({
  useThemeStore: () => ({ mode: 'system' }),
}));

vi.mock('../../theme/theme', () => ({
  resolveEffectiveMode: () => 'light',
}));

describe('StudioDraftsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with projectId prop', () => {
    render(<StudioDraftsPanel projectId="test-proj" />);
    expect(screen.getByRole('heading', { name: /drafts/i })).toBeInTheDocument();
  });
});
