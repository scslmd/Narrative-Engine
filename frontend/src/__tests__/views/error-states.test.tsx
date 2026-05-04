import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test-utils';
import { userEvent } from '@testing-library/user-event';
import * as storyGenService from '../../services/storyGeneration';
import * as reviewService from '../../services/review';
import * as inspectLinksService from '../../services/inspectLinks';
import type { GenerationRunResponse } from '../../types/storyGeneration';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ projectId: 'test-project' }),
  };
});

vi.mock('../../services/storyGeneration', () => ({
  listGenerationRuns: vi.fn(),
  createGenerationRun: vi.fn(),
  previewFork: vi.fn(),
  retryGenerationRun: vi.fn(),
  getGenerationGates: vi.fn(),
}));

vi.mock('../../services/review', () => ({
  getFindings: vi.fn(),
  getDecisionsForFinding: vi.fn(),
  createDecision: vi.fn(),
}));

vi.mock('../../services/inspectLinks', () => ({
  getInspectLinks: vi.fn(),
  createInspectLink: vi.fn(),
}));

vi.mock('../../services/characters', () => ({
  getCharacters: vi.fn(() => Promise.resolve([])),
}));

vi.mock('../../services/worldBible', () => ({
  getWorldBibleEntries: vi.fn(() => Promise.resolve([])),
}));

describe('GenerationView error states', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading skeleton while runs query is pending', async () => {
    (storyGenService.listGenerationRuns as ReturnType<typeof vi.fn>).mockReturnValue(
      new Promise(() => {}), // never resolves
    );

    const { GenerationView } = await import('../../views/GenerationView');
    render(<GenerationView />);

    await waitFor(() => {
      expect(screen.getAllByTestId('skeleton-line').length).toBeGreaterThan(0);
    });
  });

  it('shows empty state with CTA when no runs exist', async () => {
    (storyGenService.listGenerationRuns as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    const { GenerationView } = await import('../../views/GenerationView');
    render(<GenerationView />);

    await waitFor(() => {
      expect(screen.getByText('No generation runs yet')).toBeTruthy();
    });
  });

  it('error banner renders when runs query fails', async () => {
    (storyGenService.listGenerationRuns as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error('Network error'),
    );

    const { GenerationView } = await import('../../views/GenerationView');
    render(<GenerationView />);

    await waitFor(() => {
      const banner = screen.getByText(/Network error/);
      expect(banner).toBeTruthy();
    });
  });

  it('displays runs when query succeeds with data', async () => {
    const mockRuns: GenerationRunResponse[] = [
      {
        generation_id: 'gen-1',
        source_project_id: 'proj-1',
        target_project_id: 'proj-2',
        job_ids: ['job-1'],
        status: 'completed',
        warnings: [],
        created_artifacts: [],
      },
    ];
    (storyGenService.listGenerationRuns as ReturnType<typeof vi.fn>).mockResolvedValue(mockRuns);

    const { GenerationView } = await import('../../views/GenerationView');
    render(<GenerationView />);

    await waitFor(() => {
      // The run card should be rendered, no skeleton
      expect(screen.queryByTestId('skeleton-line')).toBeNull();
    });
  });
});

describe('ReviewView error states', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state while findings query is pending', async () => {
    (reviewService.getFindings as ReturnType<typeof vi.fn>).mockReturnValue(
      new Promise(() => {}), // never resolves
    );

    const { ReviewView } = await import('../../views/ReviewView');
    render(<ReviewView />);

    await waitFor(() => {
      expect(screen.getAllByTestId('skeleton-line').length).toBeGreaterThan(0);
    });
  });

  it('shows empty state for findings when none exist', async () => {
    (reviewService.getFindings as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    const { ReviewView } = await import('../../views/ReviewView');
    render(<ReviewView />);

    await waitFor(() => {
      expect(screen.getByText('No review findings yet')).toBeTruthy();
    });
  });

  it('error banner renders when findings query fails', async () => {
    (reviewService.getFindings as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error('Server error'),
    );

    const { ReviewView } = await import('../../views/ReviewView');
    render(<ReviewView />);

    await waitFor(() => {
      const banner = screen.getByText(/Server error/);
      expect(banner).toBeTruthy();
    });
  });

  it('shows loading state while inspect links query is pending', async () => {
    (inspectLinksService.getInspectLinks as ReturnType<typeof vi.fn>).mockReturnValue(
      new Promise(() => {}), // never resolves
    );

    const { ReviewView } = await import('../../views/ReviewView');
    render(<ReviewView />);

    // Switch to links tab
    await waitFor(() => {
      const linksTab = screen.getByText('Inspect Run Links');
      userEvent.click(linksTab);
    });

    await waitFor(() => {
      expect(screen.getAllByTestId('skeleton-line').length).toBeGreaterThan(0);
    });
  });

  it('shows empty state for inspect links when none exist', async () => {
    (inspectLinksService.getInspectLinks as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    const { ReviewView } = await import('../../views/ReviewView');
    render(<ReviewView />);

    // Switch to links tab
    await waitFor(() => {
      const linksTab = screen.getByText('Inspect Run Links');
      userEvent.click(linksTab);
    });

    await waitFor(() => {
      expect(screen.getByText('No inspect run links yet')).toBeTruthy();
    });
  });

  it('error banner renders when inspect links query fails', async () => {
    (inspectLinksService.getInspectLinks as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error('Link fetch failed'),
    );

    const { ReviewView } = await import('../../views/ReviewView');
    render(<ReviewView />);

    // Switch to links tab
    await waitFor(() => {
      const linksTab = screen.getByText('Inspect Run Links');
      userEvent.click(linksTab);
    });

    await waitFor(() => {
      const banner = screen.getByText(/Link fetch failed/);
      expect(banner).toBeTruthy();
    });
  });
});
