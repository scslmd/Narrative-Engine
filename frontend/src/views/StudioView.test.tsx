import { afterEach, describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { act, render, screen, userEvent } from '../__tests__/test-utils';
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
    expect(screen.getAllByRole('button', { name: 'Ideas' }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('button', { name: 'Characters' }).length).toBeGreaterThanOrEqual(1);
  });

  it('renders Nav drawer button', () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    expect(screen.getByText('Nav')).toBeInTheDocument();
  });

  it('clicking Nav toggles rail to overlay', async () => {
    server.use(...writingMocks);
    renderWithRoute(<StudioView />);
    const user = userEvent.setup();
    await user.click(screen.getByText('Nav'));
    expect(useStudioStore.getState().leftRailMode).toBe('overlay');
  });

  it('clicking "Close left rail drawer" sets collapsed mode', async () => {
    server.use(...writingMocks);
    act(() => {
      useStudioStore.setState({ leftRailMode: 'overlay' });
    });
    renderWithRoute(<StudioView />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Close left rail drawer' }));
    expect(useStudioStore.getState().leftRailMode).toBe('collapsed');
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

  });
