import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../__tests__/test-utils';
import { EmptyState } from './EmptyState';

describe('EmptyState', () => {
  it('renders title', () => {
    render(<EmptyState title="No items found" />);
    expect(screen.getByText('No items found')).toBeInTheDocument();
  });

  it('renders description when provided', () => {
    render(
      <EmptyState
        title="No items found"
        description="Get started by creating your first item."
      />,
    );
    expect(screen.getByText('Get started by creating your first item.')).toBeInTheDocument();
  });

  it('does not render description when omitted', () => {
    render(<EmptyState title="No items found" />);
    expect(screen.queryByText(/Get started/)).not.toBeInTheDocument();
  });

  it('renders button with actionLabel and onAction', () => {
    const onAction = vi.fn();
    render(
      <EmptyState
        title="No items found"
        description="Create one now."
        actionLabel="Create Item"
        onAction={onAction}
      />,
    );
    expect(screen.getByRole('button', { name: 'Create Item' })).toBeInTheDocument();
  });

  it('does not render button when actionLabel or onAction omitted', () => {
    render(
      <EmptyState
        title="No items found"
        description="There is nothing to do."
        actionLabel="Create Item"
      />,
    );
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('button click triggers onAction callback', () => {
    const onAction = vi.fn();
    render(
      <EmptyState
        title="No items found"
        actionLabel="Create Item"
        onAction={onAction}
      />,
    );
    screen.getByRole('button', { name: 'Create Item' }).click();
    expect(onAction).toHaveBeenCalledTimes(1);
  });
});
