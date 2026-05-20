import { render } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { StudioLayoutState } from '../../stores/studioStore';
import { StudioStatusBar } from './StudioStatusBar';

const { mockUseStudioStore } = vi.hoisted(() => {
  const fn = vi.fn();
  return { mockUseStudioStore: fn };
});

vi.mock('../../stores/studioStore', () => ({
  useStudioStore: mockUseStudioStore,
}));

describe('StudioStatusBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseStudioStore.mockImplementation(
      (selector: (state: { layout: StudioLayoutState }) => StudioLayoutState) =>
        selector({ layout: { panels: {}, nextZIndex: 1, layoutPreset: null } }),
    );
  });

  it('renders status bar', () => {
    render(<StudioStatusBar projectId="proj-1" />);
    const bar = document.querySelector('[data-status-bar]');
    expect(bar).toBeInTheDocument();
  });

  it('shows panel count from store', () => {
    const { container } = render(<StudioStatusBar projectId="proj-1" />);
    const panelCount = container.querySelector('[data-panel-count]');
    expect(panelCount).toBeInTheDocument();
    expect(panelCount?.textContent).toContain('0');
  });
});
