import { afterEach, describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { fireEvent, render, screen, waitFor } from '../__tests__/test-utils';
import { http, HttpResponse } from 'msw';
import type { CanonAnnotationCreateRequest } from '../types/canonCustomization';
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
    const body = await request.json() as CanonAnnotationCreateRequest;
    return HttpResponse.json({
      annotation_id: 'ann-1',
      project_id: body.project_id,
      target_kind: body.target_kind,
      target_id: body.target_id,
      field_path: body.field_path,
      annotation_kind: body.annotation_kind,
      note: body.note,
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
      screen.getAllByRole('navigation', { name: 'Studio project map' }).length,
    ).toBeGreaterThanOrEqual(1);
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
      expect(screen.getAllByText('No generation runs yet.').length).toBeGreaterThanOrEqual(1);
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
      screen.getAllByText(
        'Open a run from Review or the job tray to inspect steps, lineage, and attempts.',
      ).length,
    ).toBeGreaterThanOrEqual(1);
  });

  it('clicking "Characters" opens the characters panel and shows "0 profiles"', async () => {
    server.use(
      ...writingMocks,
      http.get('/v1/story-development/characters', () =>
        HttpResponse.json({ items: [] }),
      ),
    );
    renderWithRoute(<StudioView />);

    fireEvent.click(screen.getAllByRole('button', { name: /characters/i })[0]);

    await waitFor(() => {
      expect(screen.getAllByText('Characters').length).toBeGreaterThanOrEqual(2);
    });

    await waitFor(() => {
      expect(screen.getAllByText('0 profiles').length).toBeGreaterThanOrEqual(1);
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

    fireEvent.click(screen.getAllByRole('button', { name: /characters/i })[0]);

    await waitFor(() => {
      expect(screen.getAllByText('0 profiles').length).toBeGreaterThanOrEqual(1);
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

    fireEvent.click(screen.getAllByRole('button', { name: /world/i })[0]);

    await waitFor(() => {
      expect(screen.getAllByText('World Bible').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders Project and Context drawer buttons', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    expect(screen.getByText('Project')).toBeInTheDocument();
    expect(screen.getByText('Context')).toBeInTheDocument();
  });

  it('clicking Project toggles the left rail drawer', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    fireEvent.click(screen.getByText('Project'));
    expect(useStudioStore.getState().leftRailOpen).toBe(false);
  });

  it('clicking Context toggles the context drawer', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    fireEvent.click(screen.getByText('Context'));
    expect(useStudioStore.getState().contextPanelOpen).toBe(false);
  });

  it('clicking "Close Studio drawers" closes both drawers', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    fireEvent.click(screen.getByRole('button', { name: 'Close Studio drawers' }));
    expect(useStudioStore.getState().leftRailOpen).toBe(false);
    expect(useStudioStore.getState().contextPanelOpen).toBe(false);
  });
});
