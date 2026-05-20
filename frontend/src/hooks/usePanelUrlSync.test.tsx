import { renderHook } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { usePanelUrlSync } from './usePanelUrlSync';
import { useStudioStore } from '../stores/studioStore';

function Wrapper({ children, initialUrl }: { children: ReactNode; initialUrl: string }) {
  return (
    <MemoryRouter initialEntries={[initialUrl]}>
      <Routes>
        <Route path="*" element={<>{children}</>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('usePanelUrlSync', () => {
  beforeEach(() => {
    useStudioStore.setState({
      activePanel: 'suggestions',
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
  });

  it('reads tab param from URL on mount', () => {
    const { onJobId, onChapterId, onSubtab } = {
      onJobId: vi.fn(),
      onChapterId: vi.fn(),
      onSubtab: vi.fn(),
    };

    renderHook(
      () => usePanelUrlSync({ projectId: 'proj-1', onJobId, onChapterId, onSubtab }),
      { wrapper: (props) => <Wrapper {...props} initialUrl="/workspace/proj-1/studio?tab=inspect&jobId=abc-123" /> },
    );

    // Panel should have been added
    const panels = useStudioStore.getState().layout.panels;
    expect(Object.values(panels).some((p) => p.key === 'inspect')).toBe(true);
    expect(onJobId).toHaveBeenCalledWith('abc-123');
  });

  it('reads chapterId param from URL on mount', () => {
    const onChapterId = vi.fn();
    renderHook(
      () => usePanelUrlSync({ projectId: 'proj-1', onChapterId }),
      { wrapper: (props) => <Wrapper {...props} initialUrl="/workspace/proj-1/studio?tab=manuscripts&chapterId=ch-5" /> },
    );

    expect(onChapterId).toHaveBeenCalledWith('ch-5');
  });
});
