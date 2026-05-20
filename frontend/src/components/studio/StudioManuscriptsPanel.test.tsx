import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { StudioManuscriptsPanel } from './StudioManuscriptsPanel';

vi.mock('../../hooks/useWritingView', () => ({
  useWritingView: () => ({
    manuscriptDocuments: [],
    selectedDocumentId: null,
    manuscriptQueryLoading: false,
    setSelectedDocumentId: vi.fn(),
    setIsEditing: vi.fn(),
    setEditContent: vi.fn(),
  }),
}));

vi.mock('../../stores/settingsStore', () => ({
  useSettingsStore: () => ({ outlineDetail: 'simple' }),
}));

vi.mock('../../stores/themeStore', () => ({
  useThemeStore: () => ({ mode: 'system' }),
}));

vi.mock('../../theme/theme', () => ({
  resolveEffectiveMode: () => 'light',
}));

describe('StudioManuscriptsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with onSelect prop', () => {
    render(<StudioManuscriptsPanel onSelect={vi.fn()} />);
    expect(screen.getByRole('heading', { name: /manuscripts/i })).toBeInTheDocument();
  });
});
