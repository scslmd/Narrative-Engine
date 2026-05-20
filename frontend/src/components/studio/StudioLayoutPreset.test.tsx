import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StudioLayoutPreset } from './StudioLayoutPreset';

describe('StudioLayoutPreset', () => {
  it('renders layout button', () => {
    render(<StudioLayoutPreset />);
    expect(screen.getByRole('button', { name: /layout/i })).toBeInTheDocument();
  });

  it('opens preset menu', () => {
    render(<StudioLayoutPreset />);
    fireEvent.click(screen.getByRole('button', { name: /layout/i }));
    expect(screen.getByText(/Idea-First/)).toBeInTheDocument();
    expect(screen.getByText(/Outline-First/)).toBeInTheDocument();
  });

  it('shows import textarea when import button clicked', () => {
    render(<StudioLayoutPreset />);
    fireEvent.click(screen.getByRole('button', { name: /layout/i }));
    fireEvent.click(screen.getByText(/Import Layout/));
    const textarea = screen.getByPlaceholderText(/Paste layout JSON/);
    expect(textarea).toBeInTheDocument();
  });
});
