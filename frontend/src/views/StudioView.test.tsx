import { afterEach, describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { fireEvent, render, screen, waitFor } from '../__tests__/test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../__tests__/setup';
import { useStudioStore } from '../stores/studioStore';
import { StudioView } from './StudioView';

function renderWithRoute(ui: JSX.Element) {
  return render(
    <Routes>
      <Route path="/workspace/:projectId/studio" element={ui} />
    </Routes>,
    { route: '/workspace/proj-1/studio' },
  );
}

const writingMocks = [
  http.get('/v1/story-development/drafting/manuscript-documents', () =>
    HttpResponse.json({ project_id: 'proj-1', items: [], meta: {} }),
  ),
  http.get('/v1/story-development/drafting/draft-artifacts', () =>
    HttpResponse.json({ project_id: 'proj-1', items: [], meta: {} }),
  ),
  http.get('/v1/story-development/drafting/revision-suggestions', () =>
    HttpResponse.json({ project_id: 'proj-1', items: [], meta: {} }),
  ),
  http.get('/v1/canon/annotations', ({ request }) => {
    const url = new URL(request.url);
    const targetKind = url.searchParams.get('target_kind');
    return HttpResponse.json({ target_kind: targetKind, items: [] });
  }),
  http.post('/v1/canon/annotations', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      annotation_id: 'ann-1',
      project_id: (body as any).project_id,
      target_kind: (body as any).target_kind,
      target_id: (body as any).target_id,
      field_path: (body as any).field_path,
      annotation_kind: (body as any).annotation_kind,
      note: (body as any).note,
    });
  }),
];

describe('StudioView integration', () => {
  afterEach(() => {
    useStudioStore.setState({
      activePanel: 'suggestions',
      leftRailOpen: true,
      contextPanelOpen: true,
    });
  });

  it('renders "Studio Desk" heading', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    expect(screen.getByText('Studio Desk')).toBeInTheDocument();
  });

  it('renders studio commands navigation', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    expect(
      screen.getByRole('navigation', { name: 'Studio commands' }),
    ).toBeInTheDocument();
  });

  it('renders studio project map navigation', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    expect(
      screen.getByRole('navigation', { name: 'Studio project map' }),
    ).toBeInTheDocument();
  });

  it('clicking "Generate" opens the compact generation panel', async () => {
    server.use(
      ...writingMocks,
      http.get('/v1/story-development/characters', () =>
        HttpResponse.json({ items: [] }),
      ),
      http.get('/v1/story-development/world-bible', () =>
        HttpResponse.json({ items: [] }),
      ),
      http.get('/v1/story-generation/runs', () => HttpResponse.json([])),
    );
    renderWithRoute(<StudioView />);

    fireEvent.click(screen.getByRole('button', { name: /generate/i }));

    await waitFor(() => {
      expect(screen.getAllByText('Generation').length).toBeGreaterThanOrEqual(1);
    });
    await waitFor(() => {
      expect(screen.getByText('No generation runs yet.')).toBeInTheDocument();
    });
  });

  it('clicking "Review" opens the compact review panel with Findings', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);

    fireEvent.click(screen.getByRole('button', { name: /review/i }));

    expect(screen.getAllByText('Findings').length).toBeGreaterThanOrEqual(1);
  });

  it('clicking "Inspect" opens the compact inspect panel with guidance text', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);

    fireEvent.click(screen.getByRole('button', { name: /inspect/i }));

    expect(
      screen.getByText(
        'Open a run from Review or the job tray to inspect steps, lineage, and attempts.',
      ),
    ).toBeInTheDocument();
  });

  it('clicking "Characters" opens the characters panel and shows "0 profiles"', async () => {
    server.use(
      ...writingMocks,
      http.get('/v1/story-development/characters', () =>
        HttpResponse.json({ items: [] }),
      ),
    );
    renderWithRoute(<StudioView />);

    fireEvent.click(screen.getByRole('button', { name: /characters/i }));

    await waitFor(() => {
      expect(screen.getAllByText('Characters').length).toBeGreaterThanOrEqual(2);
    });

    await waitFor(() => {
      expect(screen.getByText('0 profiles')).toBeInTheDocument();
    });
  });

  it('opening Characters panel loads without annotation errors', async () => {
    server.use(
      ...writingMocks,
      http.get('/v1/story-development/characters', () =>
        HttpResponse.json({ items: [] }),
      ),
    );
    renderWithRoute(<StudioView />);

    fireEvent.click(screen.getByRole('button', { name: /characters/i }));

    await waitFor(() => {
      expect(screen.getByText('0 profiles')).toBeInTheDocument();
    });
  });

  it('opening World Bible panel loads without annotation errors', async () => {
    server.use(
      ...writingMocks,
      http.get('/v1/story-development/world-bible', () =>
        HttpResponse.json({ items: [] }),
      ),
    );
    renderWithRoute(<StudioView />);

    fireEvent.click(screen.getByRole('button', { name: /world/i }));

    await waitFor(() => {
      expect(screen.getAllByText('World Bible').length).toBeGreaterThanOrEqual(1);
    });
  });
});
