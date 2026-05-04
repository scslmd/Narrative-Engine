import { describe, it, expect } from 'vitest';
import { render, screen } from '../../__tests__/test-utils';
import { LoadingState } from './LoadingState';

describe('LoadingState', () => {
  it('renders children when not loading', () => {
    render(
      <LoadingState isLoading={false}>
        <div data-testid="content">Hello</div>
      </LoadingState>,
    );

    expect(screen.getByTestId('content')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('renders skeleton when loading', () => {
    render(
      <LoadingState isLoading={true}>
        <div data-testid="content">Hello</div>
      </LoadingState>,
    );

    expect(screen.queryByTestId('content')).not.toBeInTheDocument();
    const skeletons = document.querySelectorAll('[data-testid="skeleton-line"]');
    expect(skeletons.length).toBe(3);
  });

  it('renders custom fallback when provided', () => {
    render(
      <LoadingState isLoading={true} fallback={<div data-testid="custom-fallback">Loading...</div>}>
        <div data-testid="content">Hello</div>
      </LoadingState>,
    );

    expect(screen.queryByTestId('content')).not.toBeInTheDocument();
    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('does not render fallback when not loading', () => {
    render(
      <LoadingState isLoading={false} fallback={<div data-testid="custom-fallback">Loading...</div>}>
        <div data-testid="content">Hello</div>
      </LoadingState>,
    );

    expect(screen.getByTestId('content')).toBeInTheDocument();
    expect(screen.queryByTestId('custom-fallback')).not.toBeInTheDocument();
  });
});
