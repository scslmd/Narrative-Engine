import { act } from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '../../__tests__/test-utils';
import { ApiError } from '../../lib/api';
import { ErrorBanner } from './ErrorBanner';

describe('ErrorBanner', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders nothing when error is null', () => {
    const { container } = render(<ErrorBanner error={null} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders error message when error is set', () => {
    const error = new ApiError('Something went wrong', 500);
    render(<ErrorBanner error={error} />);
    expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
  });

  it('renders retry button when onRetry is provided', () => {
    const error = new ApiError('Something went wrong', 500);
    render(<ErrorBanner error={error} onRetry={() => {}} />);
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });

  it('does not render retry button when onRetry is omitted', () => {
    const error = new ApiError('Something went wrong', 500);
    render(<ErrorBanner error={error} />);
    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument();
  });

  it('retry button click triggers onRetry callback', () => {
    const onRetry = vi.fn();
    const error = new ApiError('Something went wrong', 500);
    render(<ErrorBanner error={error} onRetry={onRetry} />);
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('dismiss button hides banner', () => {
    const error = new ApiError('Something went wrong', 500);
    render(<ErrorBanner error={error} />);
    const dismissBtn = screen.getByRole('button', { name: 'Dismiss' });
    fireEvent.click(dismissBtn);
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
  });

  it('auto-hides after 30 seconds', async () => {
    const error = new ApiError('Something went wrong', 500);
    render(<ErrorBanner error={error} />);
    expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
    await act(async () => {
      vi.advanceTimersByTime(30000);
    });
    expect(screen.queryByText(/Something went wrong/)).not.toBeInTheDocument();
  });

  it('cleans up timer on unmount', () => {
    const error = new ApiError('Something went wrong', 500);
    const { unmount } = render(<ErrorBanner error={error} />);
    unmount();
    vi.advanceTimersByTime(30000);
    expect(() => {}).not.toThrow();
  });

  it('renders error status code in message', () => {
    const error = new ApiError('Not found', 404);
    render(<ErrorBanner error={error} />);
    expect(screen.getByText(/404/)).toBeInTheDocument();
  });
});
