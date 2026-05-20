import { render, screen, waitFor } from '../../__tests__/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { StudioStructurePanel } from './StudioStructurePanel';

vi.mock('../../services/planning', () => ({
  getSequencePlans: vi.fn(() => Promise.resolve([])),
  getBeatPlans: vi.fn(() => Promise.resolve([])),
}));

describe('StudioStructurePanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders panel header', async () => {
    render(<StudioStructurePanel projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText(/Structure/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no beats', async () => {
    render(<StudioStructurePanel projectId="proj-1" />);
    await waitFor(() => {
      expect(document.querySelector('[data-structure-panel]')).toBeInTheDocument();
    });
  });
});
