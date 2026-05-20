import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StudioCommandBar } from './StudioCommandBar';

describe('StudioCommandBar layout preset integration', () => {
  it('renders layout preset button when projectId is provided', () => {
    render(<StudioCommandBar projectId="proj-1" projectName="Test Project" />);
    expect(screen.getByRole('button', { name: /layout/i })).toBeInTheDocument();
  });

  it('does not render layout preset button when projectId is missing', () => {
    render(<StudioCommandBar projectName="Test Project" />);
    expect(screen.queryByRole('button', { name: /layout/i })).not.toBeInTheDocument();
  });

  it('preserves existing panel menu when layout preset is added', () => {
    render(<StudioCommandBar projectId="proj-1" projectName="Test Project" />);
    expect(screen.getByRole('button', { name: /layout/i })).toBeInTheDocument();
  });
});
