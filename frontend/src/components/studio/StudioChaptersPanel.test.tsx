import { render, screen, waitFor } from '../../__tests__/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { StudioChaptersPanel } from './StudioChaptersPanel';

vi.mock('../../services/planning', () => ({
  getChapterPlans: vi.fn(() => Promise.resolve([])),
  getChapterPackets: vi.fn(() => Promise.resolve([])),
}));

describe('StudioChaptersPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders panel header', async () => {
    render(<StudioChaptersPanel projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText(/Chapters/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no chapters', async () => {
    render(<StudioChaptersPanel projectId="proj-1" />);
    await waitFor(() => {
      expect(document.querySelector('[data-chapters-panel]')).toBeInTheDocument();
    });
  });
});
