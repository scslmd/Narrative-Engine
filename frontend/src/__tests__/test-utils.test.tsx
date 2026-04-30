import { describe, it, expect } from 'vitest';
import { render, screen } from './test-utils';

describe('test-utils', () => {
  it('renders component with providers', () => {
    render(<div data-testid="test">Hello</div>);
    expect(screen.getByTestId('test')).toBeTruthy();
    expect(screen.getByText('Hello')).toBeTruthy();
  });

  it('provides QueryClient through context', () => {
    const { queryClient } = render(<div>Test</div>);
    expect(queryClient).toBeDefined();
  });

  it('supports route configuration', () => {
    render(<div>Test</div>, { route: '/workspace/test/plan' });
    expect(screen.getByText('Test')).toBeTruthy();
  });
});
