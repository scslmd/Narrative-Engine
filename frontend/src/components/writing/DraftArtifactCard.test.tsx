import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { DraftArtifactCard } from './DraftArtifactCard';

const baseProps = {
  artifact: {
    artifact_id: 'art-1',
    project_id: 'proj-1',
    title: 'Test Chapter',
    content: 'Some draft content here.',
    source_plan_ids: [],
    source_context: [],
    provenance_note: null,
    status: 'DRAFT' as const,
  },
  isExpanded: false,
  onToggle: vi.fn(),
  onPromote: vi.fn(),
  promotePending: false,
  onContinue: vi.fn(),
  continuePending: false,
  onAlternateVariant: vi.fn(),
  alternatePending: false,
  isDark: false,
  onErrorDismiss: vi.fn(),
};

describe('DraftArtifactCard', () => {
  it('shows PENDING status with Generating text', () => {
    render(<DraftArtifactCard {...baseProps} artifact={{ ...baseProps.artifact, status: 'PENDING' }} />);
    expect(screen.getByText('Test Chapter')).toBeInTheDocument();
    expect(screen.getByText(/Generating/i)).toBeInTheDocument();
  });

  it('shows error banner and retry button on error', () => {
    render(
      <DraftArtifactCard
        {...baseProps}
        artifact={{ ...baseProps.artifact, status: 'PENDING' }}
        generationError="Generation timed out after 120s"
        onErrorDismiss={baseProps.onErrorDismiss}
      />,
    );
    expect(screen.getByText(/timed out/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', () => {
    const onRetry = vi.fn();
    render(
      <DraftArtifactCard
        {...baseProps}
        artifact={{ ...baseProps.artifact, status: 'PENDING' }}
        generationError="Failed"
        onRetry={onRetry}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /Retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('calls onErrorDismiss when dismiss button is clicked', () => {
    render(
      <DraftArtifactCard
        {...baseProps}
        artifact={{ ...baseProps.artifact, status: 'PENDING' }}
        generationError="Failed"
        onErrorDismiss={baseProps.onErrorDismiss}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /Dismiss/i }));
    expect(baseProps.onErrorDismiss).toHaveBeenCalledTimes(1);
  });

  it('renders normal DRAFT card without spinner or error', () => {
    render(<DraftArtifactCard {...baseProps} />);
    expect(screen.queryByText(/Generating/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/timed out/i)).not.toBeInTheDocument();
  });
});
