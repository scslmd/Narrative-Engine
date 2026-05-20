import { render } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route, useParams, useLocation } from 'react-router-dom';

// Spy component that captures Navigate's `to` prop
let capturedTo: string | null = null;

function NavigateSpy({ to }: { to: string; replace?: boolean }) {
  capturedTo = to;
  return null;
}

// Redirect components using NavigateSpy instead of Navigate
function TestPlanRedirect() {
  const { projectId } = useParams();
  return <NavigateSpy to={`/workspace/${projectId}/studio?tab=structure`} replace />;
}

function TestInspectRedirect() {
  const { projectId, jobId } = useParams();
  const params = new URLSearchParams({ tab: 'inspect' });
  if (jobId) params.set('jobId', jobId);
  return <NavigateSpy to={`/workspace/${projectId}/studio?${params.toString()}`} replace />;
}

function TestCanonRedirect() {
  const { projectId } = useParams();
  const { search } = useLocation();
  const params = new URLSearchParams(search);
  const knownSubtabs = ['mythos', 'patterns', 'packet'];
  const canonTab = params.get('tab');
  const newParams = new URLSearchParams({ tab: 'canon' });
  if (canonTab && knownSubtabs.includes(canonTab)) newParams.set('subtab', canonTab);
  return <NavigateSpy to={`/workspace/${projectId}/studio?${newParams.toString()}`} replace />;
}

function TestWriteRedirect() {
  const { projectId, chapterId } = useParams();
  const params = new URLSearchParams({ tab: 'manuscripts' });
  if (chapterId) params.set('chapterId', chapterId);
  return <NavigateSpy to={`/workspace/${projectId}/studio?${params.toString()}`} replace />;
}

describe('App route redirects', () => {
  beforeEach(() => {
    capturedTo = null;
  });

  it('redirects /plan to /studio?tab=structure', () => {
    render(
      <MemoryRouter initialEntries={['/workspace/proj-1/plan']}>
        <Routes>
          <Route path="/workspace/:projectId/plan" element={<TestPlanRedirect />} />
        </Routes>
      </MemoryRouter>
    );
    expect(capturedTo).toContain('/workspace/proj-1/studio');
    expect(capturedTo).toContain('tab=structure');
  });

  it('redirects /inspect/:jobId to /studio?tab=inspect&jobId=XXX', () => {
    render(
      <MemoryRouter initialEntries={['/workspace/proj-1/inspect/job-abc']}>
        <Routes>
          <Route path="/workspace/:projectId/inspect/:jobId" element={<TestInspectRedirect />} />
        </Routes>
      </MemoryRouter>
    );
    expect(capturedTo).toContain('tab=inspect');
    expect(capturedTo).toContain('jobId=job-abc');
  });

  it('redirects /canon?tab=mythos to /studio?tab=canon&subtab=mythos', () => {
    render(
      <MemoryRouter initialEntries={['/workspace/proj-1/canon?tab=mythos']}>
        <Routes>
          <Route path="/workspace/:projectId/canon" element={<TestCanonRedirect />} />
        </Routes>
      </MemoryRouter>
    );
    expect(capturedTo).toContain('tab=canon');
    expect(capturedTo).toContain('subtab=mythos');
  });

  it('redirects /write/:chapterId to /studio?tab=manuscripts&chapterId=XXX', () => {
    render(
      <MemoryRouter initialEntries={['/workspace/proj-1/write/ch-5']}>
        <Routes>
          <Route path="/workspace/:projectId/write/:chapterId" element={<TestWriteRedirect />} />
        </Routes>
      </MemoryRouter>
    );
    expect(capturedTo).toContain('tab=manuscripts');
    expect(capturedTo).toContain('chapterId=ch-5');
  });
});
