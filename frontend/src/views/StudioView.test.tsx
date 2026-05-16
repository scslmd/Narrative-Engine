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

  it('clicking "Generate" opens the generation panel', () => {
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

    const generationElements = screen.getAllByText('Generation');
    expect(generationElements.length).toBeGreaterThanOrEqual(1);
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
});
