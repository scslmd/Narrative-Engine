import { render, screen, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StudioHoverPreview } from './StudioHoverPreview';

describe('StudioHoverPreview', () => {
  it('does not render when not hovering', () => {
    const { container } = render(
      <StudioHoverPreview
        panelKey="characters"
        isHovering={false}
        projectId="proj-1"
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders preview when hovering', () => {
    act(() => {
      render(
        <StudioHoverPreview
          panelKey="characters"
          isHovering={true}
          projectId="proj-1"
        />
      );
    });
    const preview = document.querySelector('[data-hover-preview]');
    expect(preview).toBeInTheDocument();
  });

  it('shows panel label in preview', () => {
    act(() => {
      render(
        <StudioHoverPreview
          panelKey="worldBible"
          isHovering={true}
          projectId="proj-1"
        />
      );
    });
    expect(screen.getByText(/World Bible/i)).toBeInTheDocument();
  });
});
