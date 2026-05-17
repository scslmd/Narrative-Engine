import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import { render, screen } from '../__tests__/test-utils';
import userEvent from '@testing-library/user-event';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { Layout } from './Layout';
import { useProjects } from '../hooks/useProjects';
import { useUIStore } from '../stores/uiStore';

vi.mock('../hooks/useRouteSync', () => ({
  useRouteSync: vi.fn(),
}));

vi.mock('../hooks/useProjects', () => ({
  useProjects: vi.fn(),
}));

const mockProjects = [
  {
    project_id: 'test-project',
    project_name: 'Test Project',
    genre: 'Sci-Fi',
    tone_profile: 'Dark',
    story_structure: 'THREE_ACT',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
];

function renderLayout(route = '/workspace/test-project/plan') {
  return render(<Layout><div data-testid="main-content">Page Content</div></Layout>, {
    route,
  });
}

// Both desktop and mobile stage navs render in jsdom (no CSS media queries).
// Each label appears twice; pick the first button containing the text.
function getStageButton(label: string) {
  const els = screen.getAllByText(label);
  const btn = els.find((el) => el.parentElement?.tagName === 'BUTTON');
  expect(btn).toBeDefined();
  return btn as Element;
}

describe('Layout', () => {
  beforeEach(() => {
    vi.mocked(useProjects).mockReturnValue({
      data: mockProjects,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useProjects>);
    act(() => {
      useUIStore.setState({ mode: 'plan', projectId: null, chapterId: null, jobId: null, inspectContext: null });
    });
    server.use(
      http.get('/v1/backup/list', () => HttpResponse.json([])),
      http.get('/v1/auth/keys', () => HttpResponse.json([])),
      http.get('/health/ready', () =>
        HttpResponse.json({ components: { inference: { backend: 'llama.cpp' } } }),
      ),
    );
  });

  it('renders header with app title', async () => {
    renderLayout();

    await vi.waitFor(() => {
      expect(screen.getByText('Narrative Engine')).toBeInTheDocument();
    });
  });

  it('renders main content area', async () => {
    renderLayout();

    await vi.waitFor(() => {
      expect(screen.getByTestId('main-content')).toBeInTheDocument();
    });
  });

  it('renders theme toggle button', async () => {
    renderLayout();

    await vi.waitFor(() => {
      expect(screen.getByRole('button', { name: 'Toggle theme' })).toBeInTheDocument();
    });
  });

  it('renders settings button', async () => {
    renderLayout();

    await vi.waitFor(() => {
      expect(screen.getByRole('button', { name: 'Settings' })).toBeInTheDocument();
    });
  });

  it('shows project name and genre in workspace route', async () => {
    act(() => {
      useUIStore.getState().setProjectId('test-project');
    });
    renderLayout('/workspace/test-project/plan');

    await vi.waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });
  });

  it('does not show project name outside workspace route', async () => {
    act(() => {
      useUIStore.getState().setProjectId(null);
    });
    renderLayout('/');

    await vi.waitFor(() => {
      expect(screen.queryByText('Test Project')).not.toBeInTheDocument();
    });
  });

  it('renders 3 stage buttons in header within workspace', async () => {
    act(() => {
      useUIStore.getState().setProjectId('test-project');
    });
    renderLayout('/workspace/test-project/plan');

    await vi.waitFor(() => {
      expect(screen.getAllByRole('group', { name: 'Workflow stages' })).toHaveLength(2);
      expect(screen.getAllByText('Planning')).toHaveLength(2);
      expect(screen.getAllByText('Writing')).toHaveLength(2);
      expect(screen.getAllByText('Review')).toHaveLength(2);
    });
  });

  it('does not render stage buttons outside workspace', async () => {
    act(() => {
      useUIStore.getState().setProjectId(null);
    });
    renderLayout('/');

    await vi.waitFor(() => {
      expect(screen.queryByText('Planning')).not.toBeInTheDocument();
    });
  });

  it('clicking Planning stage button navigates to plan mode', async () => {
    const user = userEvent.setup();
    act(() => {
      useUIStore.getState().setProjectId('test-project');
      useUIStore.getState().setMode('write');
    });
    renderLayout('/workspace/test-project/write');

    await vi.waitFor(() => {
      expect(screen.getAllByText('Planning').length).toBeGreaterThanOrEqual(1);
    });

    await user.click(getStageButton('Planning'));

    expect(useUIStore.getState().mode).toBe('plan');
  });

  it('clicking Writing stage button navigates to write mode', async () => {
    const user = userEvent.setup();
    act(() => {
      useUIStore.getState().setProjectId('test-project');
      useUIStore.getState().setMode('plan');
    });
    renderLayout('/workspace/test-project/plan');

    await vi.waitFor(() => {
      expect(screen.getAllByText('Writing').length).toBeGreaterThanOrEqual(1);
    });

    await user.click(getStageButton('Writing'));

    expect(useUIStore.getState().mode).toBe('write');
  });

  it('clicking Review stage button navigates to review mode', async () => {
    const user = userEvent.setup();
    act(() => {
      useUIStore.getState().setProjectId('test-project');
      useUIStore.getState().setMode('plan');
    });
    renderLayout('/workspace/test-project/plan');

    await vi.waitFor(() => {
      expect(screen.getAllByText('Review').length).toBeGreaterThanOrEqual(1);
    });

    await user.click(getStageButton('Review'));

    expect(useUIStore.getState().mode).toBe('review');
  });

  it('highlights active stage button with distinct styling', async () => {
    act(() => {
      useUIStore.getState().setProjectId('test-project');
      useUIStore.getState().setMode('write');
    });
    renderLayout('/workspace/test-project/write');

    await vi.waitFor(() => {
      const writingEls = screen.getAllByText('Writing');
      expect(writingEls.length).toBeGreaterThanOrEqual(1);

      const planningEls = screen.getAllByText('Planning');
      expect(planningEls.length).toBeGreaterThanOrEqual(1);

      // Find button parents for each label
      const writingBtns = writingEls.filter(
        (el) => el.parentElement?.tagName === 'BUTTON',
      );
      const planningBtns = planningEls.filter(
        (el) => el.parentElement?.tagName === 'BUTTON',
      );

      // Active Writing button should have bg-white (desktop) or border-b-2 (mobile)
      const activeWriting = writingBtns.some((btn) => {
        const parent = btn.parentElement;
        return parent?.classList.contains('bg-white') || parent?.classList.contains('border-b-2');
      });

      // Inactive Planning button should NOT have active styling
      const inactivePlanning = planningBtns.every((btn) => {
        const parent = btn.parentElement;
        return !(parent?.classList.contains('bg-white') && parent?.classList.contains('text-gray-900'))
          && !parent?.classList.contains('border-b-2');
      });

      expect(activeWriting).toBe(true);
      expect(inactivePlanning).toBe(true);
    });
  });

  it('opens settings panel when settings button is clicked', async () => {
    const user = userEvent.setup();
    renderLayout();

    await vi.waitFor(() => {
      expect(screen.getByRole('button', { name: 'Settings' })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Settings' }));

    // SettingsPanel renders with a "Settings" h3 heading inside the modal overlay
    await vi.waitFor(() => {
      const settingsHeading = screen.getByText((content, element) =>
        content === 'Settings' && element?.tagName === 'H3',
      );
      expect(settingsHeading).toBeInTheDocument();
    });
  });
});
