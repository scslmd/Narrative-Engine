import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { useStudioStore } from '../../stores/studioStore';
import { StudioPanelMenu } from './StudioPanelMenu';

describe('StudioPanelMenu', () => {
  beforeEach(() => {
    useStudioStore.setState({
      currentProjectId: null,
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
  });

  it('renders menu trigger button', () => {
    render(<StudioPanelMenu projectId="proj-1" />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('shows panel list when opened', () => {
    render(<StudioPanelMenu projectId="proj-1" />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByText('Characters')).toBeInTheDocument();
    expect(screen.getByText('World Bible')).toBeInTheDocument();
    expect(screen.getByText('Generation')).toBeInTheDocument();
  });
});
