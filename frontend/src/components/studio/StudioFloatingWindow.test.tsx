import { render } from '@testing-library/react';
import { vi } from 'vitest';
import { describe, it, expect } from 'vitest';
import { StudioFloatingWindow } from './StudioFloatingWindow';

vi.mock('react-dom', async () => {
  const actual = await vi.importActual<typeof import('react-dom')>('react-dom');
  return {
    ...actual,
    createPortal: (children: React.ReactNode) => children,
  };
});

describe('StudioFloatingWindow', () => {
  it('renders children content', () => {
    const { container } = render(
      <StudioFloatingWindow
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 100, y: 100 }}
        size={{ width: 300, height: 400 }}
        zIndex={10}
      >
        <div data-testid="window-content">Floating content</div>
      </StudioFloatingWindow>
    );
    const el = container.querySelector('[data-floating-window]');
    expect(el).toBeInTheDocument();
  });

  it('shows reattach button', () => {
    const { container } = render(
      <StudioFloatingWindow
        panelId="test-1"
        panelKey="characters"
        projectId="proj-1"
        position={{ x: 100, y: 100 }}
        size={{ width: 300, height: 400 }}
        zIndex={10}
      >
        <div>Content</div>
      </StudioFloatingWindow>
    );
    const btn = container.querySelector('[title="Reattach"]');
    expect(btn).toBeInTheDocument();
  });
});
