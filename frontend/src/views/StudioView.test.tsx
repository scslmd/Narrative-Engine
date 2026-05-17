import { afterEach, describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { act, render, screen, userEvent, waitFor, within } from '../__tests__/test-utils';
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
  http.get('/v1/story-development/review/findings', () =>
    HttpResponse.json({ project_id: 'proj-1', items: [], meta: {} }),
  ),
  http.get('/v1/story-development/review/inspect-links', () =>
    HttpResponse.json({ project_id: 'proj-1', items: [], meta: {} }),
  ),
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
    act(() => {
      useStudioStore.setState({
        activePanel: 'suggestions',
        leftRailMode: 'expanded',
        contextPanelMode: 'docked',
        contextPanelPinned: true,
        leftRailWidth: 224,
        contextPanelWidth: 416,
      });
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

  it('renders grouped project map sections for the writing workflow', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);

    expect(screen.getByText('Develop')).toBeInTheDocument();
    expect(screen.getByText('Reference')).toBeInTheDocument();
    expect(screen.getByText('Utilities')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Ideas' }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('button', { name: 'Characters' }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('button', { name: 'Notes' }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('button', { name: 'Jobs' }).length).toBeGreaterThanOrEqual(1);
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
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: /generate/i }));

    await waitFor(() => {
      expect(screen.getAllByText('Generation').length).toBeGreaterThanOrEqual(1);
    });
    await waitFor(() => {
      expect(screen.getAllByText('No generation runs yet.').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('clicking "Review" opens the compact review panel with Findings', async () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    const user = userEvent.setup();

    await user.click(
      within(screen.getByRole('navigation', { name: 'Studio commands' })).getByRole('button', { name: 'Review' }),
    );

    expect(screen.getAllByText('Findings').length).toBeGreaterThanOrEqual(1);
  });

  it('clicking "Inspect" opens the compact inspect panel with guidance text', async () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: /inspect/i }));

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
    const user = userEvent.setup();

    await user.click(screen.getAllByRole('button', { name: /characters/i })[0]);

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
    const user = userEvent.setup();

    await user.click(screen.getAllByRole('button', { name: /characters/i })[0]);

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
    const user = userEvent.setup();

    await user.click(screen.getAllByRole('button', { name: /world/i })[0]);

    await waitFor(() => {
      expect(screen.getAllByText('World Bible').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders the primary context tab strip in desktop Studio', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);

    expect(screen.getByRole('tablist', { name: 'Studio context tabs' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Suggestions' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Ideas' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Characters' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'World' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Review' })).toBeInTheDocument();
  });

  it('clicking the World context tab opens the world bible panel', async () => {
    server.use(
      ...writingMocks,
      http.get('/v1/story-development/world-bible', () =>
        HttpResponse.json({ items: [] }),
      ),
    );
    renderWithRoute(<StudioView />);
    const user = userEvent.setup();

    await user.click(screen.getByRole('tab', { name: 'World' }));

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

  it('clicking Project sets leftRailMode to overlay', async () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    const user = userEvent.setup();
    await user.click(screen.getByText('Project'));
    expect(useStudioStore.getState().leftRailMode).toBe('overlay');
  });

  it('clicking Context sets contextPanelMode to overlay', async () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    const user = userEvent.setup();
    await user.click(screen.getByText('Context'));
    expect(useStudioStore.getState().contextPanelMode).toBe('overlay');
  });

  it('clicking "Close Studio drawers" sets collapsed/closed modes', async () => {
    server.use(...writingMocks);
    act(() => {
      useStudioStore.setState({ leftRailMode: 'overlay' });
    });
    renderWithRoute(<StudioView />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Close Studio drawers' }));
    expect(useStudioStore.getState().leftRailMode).toBe('collapsed');
    expect(useStudioStore.getState().contextPanelMode).toBe('closed');
  });

  it('collapsed rail mode still leaves project map accessible', () => {
    server.use(...writingMocks);
    act(() => {
      useStudioStore.setState({ leftRailMode: 'collapsed' });
    });
    renderWithRoute(<StudioView />);
    expect(
      screen.getAllByRole('navigation', { name: 'Studio project map' }).length,
    ).toBeGreaterThanOrEqual(1);
  });

  it('closed context mode reopens on Review click', async () => {
    server.use(...writingMocks);
    act(() => {
      useStudioStore.setState({ contextPanelMode: 'closed' });
    });
    renderWithRoute(<StudioView />);
    const user = userEvent.setup();

    await user.click(
      within(screen.getByRole('navigation', { name: 'Studio commands' })).getByRole('button', { name: 'Review' }),
    );

    expect(useStudioStore.getState().contextPanelMode).toBe('docked');
    expect(screen.getAllByText('Findings').length).toBeGreaterThanOrEqual(1);
  });

  it('closed context mode reopens on Inspect click', async () => {
    server.use(...writingMocks);
    act(() => {
      useStudioStore.setState({ contextPanelMode: 'closed' });
    });
    renderWithRoute(<StudioView />);
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: /inspect/i }));

    expect(useStudioStore.getState().contextPanelMode).toBe('docked');
    expect(
      screen.getAllByText(
        'Open a run from Review or the job tray to inspect steps, lineage, and attempts.',
      ).length,
    ).toBeGreaterThanOrEqual(1);
  });

  it('desktop Studio does not render legacy layout control buttons', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);

    expect(screen.queryByRole('button', { name: 'Rail' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Rail Width' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Panel Width' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Reset Studio layout' })).not.toBeInTheDocument();
  });

  it('desktop Studio does not render legacy context layout controls', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);

    expect(screen.queryByRole('button', { name: 'Pin' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Dock' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Overlay' })).not.toBeInTheDocument();
  });

  it('desktop Studio keeps the context pane mounted even when stored mode is closed', () => {
    server.use(...writingMocks);
    act(() => {
      useStudioStore.setState({ contextPanelMode: 'closed' });
    });
    renderWithRoute(<StudioView />);

    expect(screen.getAllByText('Suggestions').length).toBeGreaterThanOrEqual(1);
  });

  it('desktop Studio keeps the context pane mounted even when stored mode is overlay', () => {
    server.use(...writingMocks);
    act(() => {
      useStudioStore.setState({ contextPanelMode: 'overlay' });
    });
    renderWithRoute(<StudioView />);

    expect(screen.getAllByText('Suggestions').length).toBeGreaterThanOrEqual(1);
  });

  it('mobile context close button still closes the context drawer state', async () => {
    server.use(...writingMocks);
    act(() => {
      useStudioStore.setState({ contextPanelMode: 'overlay' });
    });
    renderWithRoute(<StudioView />);
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: 'Close' }));
    expect(useStudioStore.getState().contextPanelMode).toBe('closed');
  });
});
