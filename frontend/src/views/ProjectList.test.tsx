import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '../__tests__/test-utils';
import userEvent from '@testing-library/user-event';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { ProjectList } from './ProjectList';

const mockProjects = [
  {
    project_id: 'proj-1',
    project_name: 'Sci-Fi Adventure',
    genre: 'Sci-Fi',
    tone_profile: 'Dark and Gritty',
    story_structure: 'THREE_ACT',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-04-01T00:00:00Z',
  },
  {
    project_id: 'proj-2',
    project_name: 'Fantasy Epic',
    genre: 'Fantasy',
    tone_profile: 'Lighthearted',
    story_structure: 'HERO_JOURNEY',
    created_at: '2026-01-15T00:00:00Z',
    updated_at: '2026-04-15T00:00:00Z',
  },
];

describe('ProjectList', () => {
  beforeEach(() => {
    server.use(
      http.get('/health/ready', () =>
        HttpResponse.json({ components: { inference: { backend: 'llama.cpp' } } }),
      ),
    );
  });

  it('shows loading state initially', () => {
    render(<ProjectList />);

    // SkeletonList renders cards with animate-pulse class
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('displays projects when loaded', async () => {
    server.use(
      http.get('/projects', () => HttpResponse.json(mockProjects)),
    );

    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByText('Sci-Fi Adventure')).toBeInTheDocument();
      expect(screen.getByText('Fantasy Epic')).toBeInTheDocument();
    });
  });

  it('shows empty state when no projects exist', async () => {
    server.use(
      http.get('/projects', () => HttpResponse.json([])),
    );

    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByText(/No projects yet/i)).toBeInTheDocument();
    });
  });

  it('displays project genre and tone profile', async () => {
    server.use(
      http.get('/projects', () => HttpResponse.json(mockProjects)),
    );

    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByText('Sci-Fi')).toBeInTheDocument();
      expect(screen.getByText('Dark and Gritty')).toBeInTheDocument();
    });
  });

  it('renders navigation links for each project', async () => {
    server.use(
      http.get('/projects', () => HttpResponse.json(mockProjects)),
    );

    render(<ProjectList />);

    await waitFor(() => {
      const links = screen.getAllByRole('link');
      expect(links).toHaveLength(2);
      expect(links[0]).toHaveAttribute('href', '/workspace/proj-1');
      expect(links[1]).toHaveAttribute('href', '/workspace/proj-2');
    });
  });

  it('renders the new project form', async () => {
    server.use(
      http.get('/projects', () => HttpResponse.json([])),
    );

    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByText('New Project')).toBeInTheDocument();
    });

    expect(screen.getByPlaceholderText(/enter project title/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e\.g\., Science Fiction/i)).toBeInTheDocument();
  });

  it('renders the create project button', async () => {
    server.use(
      http.get('/projects', () => HttpResponse.json([])),
    );

    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /create project/i })).toBeInTheDocument();
    });
  });

  it('renders the import existing story button', async () => {
    server.use(
      http.get('/projects', () => HttpResponse.json([])),
    );

    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /import existing story/i })).toBeInTheDocument();
    });
  });

  it('opens import modal when import button is clicked', async () => {
    const user = userEvent.setup();
    server.use(
      http.get('/projects', () => HttpResponse.json([])),
    );

    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /import existing story/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /import existing story/i }));

    // StoryImportModal renders a fixed overlay with bg-black/50 backdrop
    await waitFor(() => {
      expect(document.querySelector('.fixed.inset-0.bg-black\\/50')).toBeInTheDocument();
    });
  });

  it('submits the new project form', async () => {
    const user = userEvent.setup({ delay: 10 });
    let receivedBody: { project_name: string; config: { genre: string; tone_profile: object; story_structure: string } } | null = null;
    server.use(
      http.get('/projects', () => HttpResponse.json([])),
      http.post('/projects/create', async ({ request }) => {
        const body = (await request.json()) as { project_name: string; config: { genre: string; tone_profile: object; story_structure: string } };
        receivedBody = body;
        return HttpResponse.json({
          project_id: 'new-proj',
          project_name: body.project_name,
          genre: body.config.genre,
          tone_profile: body.config.tone_profile,
          story_structure: body.config.story_structure,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          manifest: {},
          project_dir: '',
          database_exists: true,
          sequence_exists: false,
          chapter_exists: false,
          export_count: 0,
        });
      }),
    );

    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/enter project title/i)).toBeInTheDocument();
    });

    const form = document.querySelector('form')!;
    await user.type(screen.getByPlaceholderText(/enter project title/i), 'New Project');
    await user.type(screen.getByPlaceholderText(/e\.g\., Science Fiction/i), 'Sci-Fi');
    await user.type(
      screen.getByPlaceholderText(/e\.g\., Dark and Gritty/i),
      'Dark',
    );

    fireEvent.submit(form);

    await waitFor(() => {
      expect(receivedBody).not.toBeNull();
      expect(receivedBody!.project_name).toBe('New Project');
      expect(receivedBody!.config.genre).toBe('Sci-Fi');
    });
  });

  it('shows welcome header', async () => {
    server.use(
      http.get('/projects', () => HttpResponse.json([])),
    );

    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByText('Welcome to Narrative Engine')).toBeInTheDocument();
    });
  });

  it('displays your projects section header', async () => {
    server.use(
      http.get('/projects', () => HttpResponse.json(mockProjects)),
    );

    render(<ProjectList />);

    await waitFor(() => {
      expect(screen.getByText('Your Projects')).toBeInTheDocument();
    });
  });
});
