import { describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { render, screen, waitFor } from '../__tests__/test-utils';
import { server } from '../__tests__/setup';
import { CanonView } from './CanonView';

describe('CanonView', () => {
  it('loads canon workspace data and renders workshop', async () => {
    server.use(
      http.get('/v1/story-development/characters', () =>
        HttpResponse.json({ items: [] }),
      ),
      http.get('/v1/story-development/world-bible', () =>
        HttpResponse.json({ items: [] }),
      ),
      http.get('/v1/mythos/entries', () => HttpResponse.json([])),
      http.get('/v1/patterns/entries', () => HttpResponse.json([])),
      http.get('/v1/canon/annotations', () => HttpResponse.json([])),
      http.get('/v1/canon/profiles', () => HttpResponse.json([])),
    );

    render(
      <Routes>
        <Route path="/workspace/:projectId/canon" element={<CanonView />} />
      </Routes>,
      { route: '/workspace/project-1/canon?tab=mythos' },
    );

    await waitFor(() => {
      expect(screen.getByText('Mythos Library')).toBeInTheDocument();
    });
  });
});
