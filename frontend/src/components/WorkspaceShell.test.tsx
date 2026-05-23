import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import { render, screen } from '../__tests__/test-utils';
import userEvent from '@testing-library/user-event';
import { WorkspaceShell } from './WorkspaceShell';
import { useUIStore } from '../stores/uiStore';
import { useSettingsStore } from '../stores/settingsStore';
import type { WorkspaceMode } from '../routes';

const mockProjectId = 'test-project-123';

function renderShell(mode: WorkspaceMode, projectId = mockProjectId) {
  act(() => {
    useUIStore.setState({ mode, projectId, chapterId: null, jobId: null, inspectContext: null });
    useSettingsStore.setState({ iconMode: 'labels', showTooltips: true });
  });

  return render(
    <WorkspaceShell>
      <div data-testid="main-content">Page Content</div>
    </WorkspaceShell>,
    { route: `/workspace/${projectId}/${mode}` },
  );
}

describe('WorkspaceShell', () => {
  beforeEach(() => {
    act(() => {
      useUIStore.getState().reset();
      useSettingsStore.getState().reset();
    });
  });

  it('renders 4 nav items when mode is in planning stage (plan)', () => {
    renderShell('plan');

    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByText('Workspace sections')).toBeInTheDocument();
    const navItems = screen.getAllByRole('button', { hidden: false }).filter(
      (btn) => btn.parentElement?.tagName !== 'BUTTON' && btn.classList.contains('nav-item') && !btn.textContent?.includes('Studio Desk'),
    );
    expect(navItems).toHaveLength(4);
    expect(screen.getByText('Brain Dump')).toBeInTheDocument();
    expect(screen.getByText('Planning')).toBeInTheDocument();
    expect(screen.getByText('Canon')).toBeInTheDocument();
    expect(screen.getByText('Generate')).toBeInTheDocument();
  });

  it('renders 4 nav items when mode is canon (planning stage)', () => {
    renderShell('canon');

    const buttons = screen.getAllByRole('button', { hidden: false }).filter(
      (btn) => btn.classList.contains('nav-item') && !btn.textContent?.includes('Studio Desk'),
    );
    expect(buttons).toHaveLength(4);
  });

  it('renders writing nav items when mode is studio', () => {
    renderShell('studio');

    expect(screen.getByText('Workspace sections')).toBeInTheDocument();
    const nav = screen.getByRole('navigation');
    const navButtons = Array.from(nav.querySelectorAll('button.nav-item'));
    expect(navButtons).toHaveLength(1);
    expect(navButtons[0]?.textContent?.trim()).toBe('Studio');
    expect(screen.getByText('Studio')).toBeInTheDocument();
  });

  it('renders 2 nav items when mode is in review stage (review)', () => {
    renderShell('review');

    const buttons = screen.getAllByRole('button', { hidden: false }).filter(
      (btn) => btn.classList.contains('nav-item') && !btn.textContent?.includes('Studio Desk'),
    );
    expect(buttons).toHaveLength(2);
    expect(screen.getByText('Review')).toBeInTheDocument();
    expect(screen.getByText('Inspect')).toBeInTheDocument();
  });

  it('renders 2 nav items when mode is inspect (review stage)', () => {
    renderShell('inspect');

    const buttons = screen.getAllByRole('button', { hidden: false }).filter(
      (btn) => btn.classList.contains('nav-item') && !btn.textContent?.includes('Studio Desk'),
    );
    expect(buttons).toHaveLength(2);
  });

  it('active nav item has distinct styling with gradient icon and indicator dot', () => {
    renderShell('plan');

    const planningBtn = screen.getByText('Planning').closest('button');
    expect(planningBtn).toBeInTheDocument();

    // Active button should have the active class (contains --color-primary-subtle)
    expect(planningBtn?.className).toContain('bg-[var(--color-primary-subtle)]');

    // Active icon wrapper should have gradient classes
    const activeIconWrapper = planningBtn?.querySelector('.nav-icon-wrapper');
    expect(activeIconWrapper?.className).toContain('from-blue-500 to-blue-600');

    // Active item should have the indicator dot (small rounded div after label)
    const indicatorDots = planningBtn?.querySelectorAll(
      '.w-1\\.5.h-1\\.5.rounded-full',
    );
    expect(indicatorDots?.length).toBeGreaterThanOrEqual(1);
  });

  it('inactive nav item lacks active styling', () => {
    renderShell('plan');

    const braindumpBtn = screen.getByText('Brain Dump').closest('button');
    expect(braindumpBtn).toBeInTheDocument();

    // Inactive button should NOT have active bg class
    expect(braindumpBtn?.className).not.toContain('bg-[var(--color-primary-subtle)]');

    // Inactive icon wrapper should NOT have gradient classes
    const inactiveIconWrapper = braindumpBtn?.querySelector('.nav-icon-wrapper');
    expect(inactiveIconWrapper?.className).not.toContain('from-amber-500 to-amber-600');
  });

  it('clicking a nav item updates mode and navigates to the correct route', async () => {
    const user = userEvent.setup();
    renderShell('plan');

    await vi.waitFor(() => {
      expect(screen.getByText('Canon')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Canon'));

    expect(useUIStore.getState().mode).toBe('studio');
  });

  it('clicking Inspect nav item in review stage updates mode', async () => {
    const user = userEvent.setup();
    renderShell('review');

    await vi.waitFor(() => {
      expect(screen.getByText('Inspect')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Inspect'));

    expect(useUIStore.getState().mode).toBe('studio');
  });

  it('nav items show correct labels for all planning stage items', () => {
    renderShell('braindump');

    expect(screen.getByText('Brain Dump')).toBeInTheDocument();
    expect(screen.getByText('Planning')).toBeInTheDocument();
    expect(screen.getByText('Canon')).toBeInTheDocument();
    expect(screen.getByText('Generate')).toBeInTheDocument();
  });

  it('nav items show correct icons for all visible items', () => {
    renderShell('plan');

    // Each nav button should contain an SVG icon (from lucide-react)
    const buttons = screen.getAllByRole('button', { hidden: false }).filter(
      (btn) => btn.classList.contains('nav-item'),
    );

    buttons.forEach((btn) => {
      const svg = btn.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg?.classList.contains('w-4')).toBe(true);
      expect(svg?.classList.contains('h-4')).toBe(true);
    });
  });

  it('renders main content area', () => {
    renderShell('plan');

    expect(screen.getByTestId('main-content')).toBeInTheDocument();
    expect(screen.getByText('Page Content')).toBeInTheDocument();
  });

  it('does not show writing nav items in main nav when in planning stage', () => {
    renderShell('plan');

    const nav = screen.getByRole('navigation');
    const studioBtn = Array.from(nav.querySelectorAll('button')).find(
      (btn) => btn.textContent?.trim() === 'Studio',
    );
    expect(studioBtn).toBeUndefined();
  });

  it('does not show planning nav items when in review stage', () => {
    renderShell('review');

    expect(screen.queryByText('Brain Dump')).not.toBeInTheDocument();
    expect(screen.queryByText('Planning')).not.toBeInTheDocument();
    expect(screen.queryByText('Canon')).not.toBeInTheDocument();
    expect(screen.queryByText('Generate')).not.toBeInTheDocument();
  });
});
