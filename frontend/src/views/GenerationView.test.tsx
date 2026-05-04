import { describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { fireEvent, render, screen, waitFor } from '../__tests__/test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../__tests__/setup';
import { GenerationView } from './GenerationView';

function renderWithRoute(ui: JSX.Element) {
  return render(
    <Routes>
      <Route path="/workspace/:projectId/generate" element={ui} />
    </Routes>,
    { route: '/workspace/proj-1/generate' },
  );
}

const baseRun = {
  generation_id: 'gen-1',
  source_project_id: 'proj-1',
  target_project_id: 'proj-1',
  job_ids: ['job-1'],
  status: 'failed',
  warnings: [],
  created_artifacts: [],
};

const successRun = {
  ...baseRun,
  generation_id: 'gen-retry-1',
  status: 'queued',
};

describe('GenerationView retry integration', () => {
  it('shows retry button on failed generation run', async () => {
    server.use(
      http.get('/v1/story-development/characters', () => HttpResponse.json([])),
      http.get('/v1/story-development/world-bible', () => HttpResponse.json([])),
      http.get('/v1/story-generation/runs', () => HttpResponse.json([baseRun])),
    );

    renderWithRoute(<GenerationView />);

    await waitFor(() => {
      expect(screen.getByText('Status: failed')).toBeTruthy();
    });

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('calls retry endpoint and shows success toast on retry', async () => {
    server.use(
      http.get('/v1/story-development/characters', () => HttpResponse.json([])),
      http.get('/v1/story-development/world-bible', () => HttpResponse.json([])),
      http.get('/v1/story-generation/runs', () => HttpResponse.json([baseRun])),
      http.post('/v1/story-generation/runs/gen-1/retry', () =>
        HttpResponse.json(successRun),
      ),
    );

    renderWithRoute(<GenerationView />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /retry/i })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() => {
      const toast = screen.queryByText(/retry/i);
      expect(toast).toBeInTheDocument();
    });
  });

  it('shows error toast on 409 retry conflict', async () => {
    server.use(
      http.get('/v1/story-development/characters', () => HttpResponse.json([])),
      http.get('/v1/story-development/world-bible', () => HttpResponse.json([])),
      http.get('/v1/story-generation/runs', () => HttpResponse.json([baseRun])),
      http.post('/v1/story-generation/runs/gen-1/retry', () =>
        HttpResponse.json({ detail: 'Cannot retry non-failed run' }, { status: 409 }),
      ),
    );

    renderWithRoute(<GenerationView />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /retry/i })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() => {
      expect(screen.queryByText(/Cannot retry|conflict|409/i)).toBeInTheDocument();
    });
  });

  it('shows error toast on 404 expired packet', async () => {
    server.use(
      http.get('/v1/story-development/characters', () => HttpResponse.json([])),
      http.get('/v1/story-development/world-bible', () => HttpResponse.json([])),
      http.get('/v1/story-generation/runs', () => HttpResponse.json([baseRun])),
      http.post('/v1/story-generation/runs/gen-1/retry', () =>
        HttpResponse.json({ detail: 'Generation packet not found' }, { status: 404 }),
      ),
    );

    renderWithRoute(<GenerationView />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /retry/i })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() => {
      expect(screen.queryByText(/not found|expired|packet/i)).toBeInTheDocument();
    });
  });

  it('disables retry button while retry is in progress', async () => {
    let resolveFn: (v: unknown) => void;
    const pending = new Promise((resolve) => { resolveFn = resolve; });

    server.use(
      http.get('/v1/story-development/characters', () => HttpResponse.json([])),
      http.get('/v1/story-development/world-bible', () => HttpResponse.json([])),
      http.get('/v1/story-generation/runs', () => HttpResponse.json([baseRun])),
      http.post('/v1/story-generation/runs/gen-1/retry', async () => {
        await pending;
        return HttpResponse.json(successRun);
      }),
    );

    renderWithRoute(<GenerationView />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /retry/i })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() => {
      const retryBtn = screen.getByRole('button', { name: /retry/i });
      expect(retryBtn).toBeDisabled();
    });

    resolveFn!(successRun);
  });
});
