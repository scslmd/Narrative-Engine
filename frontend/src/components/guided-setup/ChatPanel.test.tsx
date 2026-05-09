import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../__tests__/test-utils';
import { ChatPanel } from './ChatPanel';
import type { CategoryProgress } from '../../services/guidedSetup';

const mockOnSend = vi.fn().mockResolvedValue(undefined);

const baseProps: React.ComponentProps<typeof ChatPanel> = {
  onSend: mockOnSend,
  isLoading: false,
  readyToCreate: false,
  progress: 45,
  categoryProgress: [],
};

function createCategory(category: string, completeness: number): CategoryProgress {
  return {
    category,
    completeness,
    confidence: 0.8,
    fields_collected: ['field1'],
    fields_missing: ['field2'],
  };
}

describe('ChatPanel', () => {
  it('shows "Ready to Save" badge when readyToCreate is true', () => {
    render(
      <ChatPanel
        {...baseProps}
        readyToCreate={true}
        progress={100}
        categoryProgress={[createCategory('premise', 1)]}
      />,
    );
    expect(screen.getByText('Ready to Save')).toBeInTheDocument();
  });

  it('shows "X/5 categories ready" when not ready but has categoryProgress', () => {
    const cats: CategoryProgress[] = [
      createCategory('premise', 0.9),
      createCategory('characters', 0.8),
      createCategory('world', 0.3),
      createCategory('arcs', 0.6),
      createCategory('outline', 0.2),
    ];
    render(<ChatPanel {...baseProps} categoryProgress={cats} />);
    expect(screen.getByText('2/5 categories ready')).toBeInTheDocument();
  });

  it('shows "% complete" fallback when no categoryProgress', () => {
    render(<ChatPanel {...baseProps} progress={45} categoryProgress={[]} />);
    expect(screen.getByText('45% complete')).toBeInTheDocument();
  });

  it('progress bar uses emerald gradient when ready', () => {
    render(
      <ChatPanel
        {...baseProps}
        readyToCreate={true}
        progress={100}
        categoryProgress={[createCategory('premise', 1)]}
      />,
    );
    const bar = document.querySelector('[style*="width: 100%"]');
    expect(bar).toHaveClass('bg-gradient-to-r', 'from-emerald-400', 'to-teal-500');
  });

  it('progress bar uses violet gradient when not ready', () => {
    render(<ChatPanel {...baseProps} progress={45} categoryProgress={[]} />);
    const bar = document.querySelector('[style*="width: 45%"]');
    expect(bar).toHaveClass('bg-gradient-to-r', 'from-violet-500', 'to-purple-500');
  });

  it('header has emerald border when readyToCreate', () => {
    render(
      <ChatPanel
        {...baseProps}
        readyToCreate={true}
        progress={100}
        categoryProgress={[createCategory('premise', 1)]}
      />,
    );
    const header = document.querySelector('.border-emerald-200');
    expect(header).toBeInTheDocument();
  });

  it('header does not have emerald border when not ready', () => {
    render(<ChatPanel {...baseProps} progress={45} categoryProgress={[]} />);
    const header = document.querySelector('.border-gray-200');
    expect(header).toBeInTheDocument();
  });
});
