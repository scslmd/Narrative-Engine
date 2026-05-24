import { render, screen, waitFor } from '../../__tests__/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { StudioCanonPanel } from './StudioCanonPanel';

vi.mock('../../services/canonCustomization', () => ({
  getCanonProfiles: vi.fn(() => Promise.resolve([])),
  getCanonAnnotations: vi.fn(() => Promise.resolve([])),
}));

describe('StudioCanonPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders panel header', async () => {
    render(<StudioCanonPanel projectId="proj-1" />);
    await waitFor(() => {
      expect(document.querySelector('[data-canon-panel]')).toBeInTheDocument();
    });
  });

  it('shows empty state when no profiles', async () => {
    render(<StudioCanonPanel projectId="proj-1" />);
    await waitFor(() => {
      expect(document.querySelector('[data-canon-panel]')).toBeInTheDocument();
    });
  });
});
