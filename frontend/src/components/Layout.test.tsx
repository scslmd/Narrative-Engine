import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '../__tests__/test-utils';
import userEvent from '@testing-library/user-event';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { Layout } from './Layout';
import { useUIStore } from '../stores/uiStore';
import { useThemeStore } from '../stores/themeStore';
import { useSettingsStore } from '../stores/settingsStore';

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

describe('Layout', () => {
  beforeEach(() => {
    useUIStore.setState({ mode: 'plan', projectId: null, chapterId: null, jobId: null, inspectContext: null });
    server.use(
      http.get('/projects', () => HttpResponse.json(mockProjects)),
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
    useUIStore.getState().setProjectId('test-project');
    renderLayout('/workspace/test-project/plan');

    await vi.waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });
  });

  it('does not show project name outside workspace route', async () => {
    useUIStore.getState().setProjectId(null);
    renderLayout('/');

    await vi.waitFor(() => {
      expect(screen.queryByText('Test Project')).not.toBeInTheDocument();
    });
  });

  it('renders mode navigation buttons in workspace', async () => {
    useUIStore.getState().setProjectId('test-project');
    useSettingsStore.getState().setIconMode('labels');
    renderLayout('/workspace/test-project/plan');

    await vi.waitFor(() => {
      expect(screen.getByText('Planning')).toBeInTheDocument();
      expect(screen.getByText('Writing')).toBeInTheDocument();
      expect(screen.getByText('Review')).toBeInTheDocument();
      expect(screen.getByText('Inspect')).toBeInTheDocument();
    });
  });

  it('does not render mode navigation outside workspace', async () => {
    useUIStore.getState().setProjectId(null);
    renderLayout('/');

    await vi.waitFor(() => {
      expect(screen.queryByText('Planning')).not.toBeInTheDocument();
    });
  });

  it('highlights active mode in sidebar', async () => {
    useUIStore.getState().setProjectId('test-project');
    useUIStore.getState().setMode('write');
    useSettingsStore.getState().setIconMode('labels');
    renderLayout('/workspace/test-project/write');

    await vi.waitFor(() => {
      // Desktop nav uses bg-[var(--bg-elevated)], mobile nav uses border-b-2
      const writeBtns = screen.getAllByRole('button', { name: /Writing/ });
      const isActive = writeBtns.some(
        (btn) =>
          btn.classList.contains('bg-[var(--bg-elevated)]') ||
          btn.classList.contains('border-b-2'),
      );
      expect(isActive).toBe(true);
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
