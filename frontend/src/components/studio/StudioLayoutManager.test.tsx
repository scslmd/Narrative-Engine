import { describe, it, expect, beforeEach } from 'vitest';
import { act, render, screen } from '../../__tests__/test-utils';
import { userEvent } from '@testing-library/user-event';
import { StudioLayoutManager } from './StudioLayoutManager';
import { useStudioStore } from '../../stores/studioStore';
import { listUserLayouts, saveUserLayout, deleteUserLayout } from '../../stores/layoutPresets';

beforeEach(() => {
  act(() => {
    useStudioStore.getState().resetLayout();
  });
  const layouts = listUserLayouts();
  layouts.forEach((l) => deleteUserLayout(l.id));
});

describe('StudioLayoutManager', () => {
  it('renders Layout button', () => {
    render(<StudioLayoutManager />);
    expect(screen.getByText(/Layout/)).toBeInTheDocument();
  });

  it('shows 9 preset buttons when opened', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await userEvent.click(btn);
    expect(screen.getByText('Idea-First (Pantser)')).toBeInTheDocument();
    expect(screen.getByText('Beat-Sheet')).toBeInTheDocument();
    expect(screen.getByText('World-Builder+')).toBeInTheDocument();
  });

  it('shows My Layouts section', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await userEvent.click(btn);
    expect(screen.getByText('My Layouts')).toBeInTheDocument();
  });

  it('shows Save Current Layout button', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await userEvent.click(btn);
    expect(screen.getByText('Save Current Layout')).toBeInTheDocument();
  });

  it('shows Reset to Factory Default button', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await userEvent.click(btn);
    expect(screen.getByText(/Reset to Factory Default/)).toBeInTheDocument();
  });

  it('shows Export and Import buttons', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await userEvent.click(btn);
    expect(screen.getByText('Export Layout (clipboard)')).toBeInTheDocument();
    expect(screen.getByText('Import Layout (paste JSON)')).toBeInTheDocument();
  });

  it('shows "No saved layouts" when empty', async () => {
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await userEvent.click(btn);
    expect(screen.getByText('No saved layouts')).toBeInTheDocument();
  });

  it('shows saved user layout in menu', async () => {
    saveUserLayout('Test Layout', {
      panels: {},
      v1State: {
        leftRailMode: 'expanded',
        contextPanelMode: 'closed',
        contextPanelPinned: true,
        leftRailWidth: 224,
        contextPanelWidth: 416,
      },
    });
    render(<StudioLayoutManager />);
    const btn = screen.getByText(/Layout/);
    await userEvent.click(btn);
    expect(screen.getByText('Test Layout')).toBeInTheDocument();
  });
});
