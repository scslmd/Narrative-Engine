import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '../../__tests__/test-utils';
import { GenerationRunCard } from './GenerationRunCard';
import type { GenerationRunResponse } from '../../types/storyGeneration';

const baseRun: GenerationRunResponse = {
  generation_id: 'gen-1',
  source_project_id: 'source-project',
  target_project_id: 'target-project',
  job_ids: ['job-1'],
  status: 'completed',
  warnings: [],
  created_artifacts: [],
};

describe('GenerationRunCard', () => {
  it('renders run details', () => {
    render(<GenerationRunCard run={baseRun} />);
    expect(screen.getByText('gen-1')).toBeTruthy();
    expect(screen.getByText('Status: completed')).toBeTruthy();
  });

  it('does not show retry button for non-failed runs', () => {
    render(<GenerationRunCard run={baseRun} onRetry={() => {}} />);
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
  });

  it.each(['failed'] as const)('shows retry button for %s status', (status) => {
    render(
      <GenerationRunCard
        run={{ ...baseRun, status }}
        onRetry={vi.fn()}
      />,
    );
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', () => {
    const onRetry = vi.fn();
    render(
      <GenerationRunCard
        run={{ ...baseRun, status: 'failed' }}
        onRetry={onRetry}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('disables retry button while retrying', () => {
    render(
      <GenerationRunCard
        run={{ ...baseRun, status: 'failed' }}
        onRetry={() => {}}
        isRetrying
      />,
    );
    expect(screen.getByRole('button', { name: /retry/i })).toBeDisabled();
  });
});
