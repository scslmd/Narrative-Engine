import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { AssistAction } from '../../lib/assistActions';
import { SelectionToolbar } from './SelectionToolbar';

const mockActions: AssistAction[] = [
  {
    kind: 'line_edit_selection',
    label: 'Tighten & polish',
    description: 'Remove redundancy, improve flow',
    instructionTemplate: () => 'Tighten and polish.',
  },
  {
    kind: 'expand_sensory_sight',
    label: 'Sight & color',
    description: 'Add visual detail',
    instructionTemplate: () => 'Expand with visual detail.',
  },
  {
    kind: 'continue_from_selection',
    label: 'Continue',
    description: 'Generate next passage',
    instructionTemplate: () => 'Continue from here.',
  },
];

describe('SelectionToolbar', () => {
  it('renders nothing when hidden', () => {
    const onClick = vi.fn();
    const { container } = render(
      <SelectionToolbar actions={mockActions} visible={false} position={{ x: 0, y: 0 }} onClick={onClick} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders action buttons when visible', () => {
    const onClick = vi.fn();
    render(
      <SelectionToolbar actions={mockActions} visible={true} position={{ x: 100, y: 200 }} onClick={onClick} />,
    );
    expect(screen.getByText('Tighten & polish')).toBeInTheDocument();
    expect(screen.getByText('Sensory detail')).toBeInTheDocument();
  });

  it('renders sensory detail submenu toggle', () => {
    const onClick = vi.fn();
    render(
      <SelectionToolbar actions={mockActions} visible={true} position={{ x: 100, y: 200 }} onClick={onClick} />,
    );
    expect(screen.getByText('Sensory detail')).toBeInTheDocument();
  });

  it('calls onClick with selected action kind and instruction', async () => {
    const onClick = vi.fn();
    render(
      <SelectionToolbar actions={mockActions} visible={true} position={{ x: 100, y: 200 }} onClick={onClick} />,
    );
    await userEvent.click(screen.getByText('Tighten & polish'));
    expect(onClick).toHaveBeenCalledWith('line_edit_selection', 'Tighten and polish.');
  });

  it('positions toolbar at specified coordinates', () => {
    const onClick = vi.fn();
    render(
      <SelectionToolbar actions={mockActions} visible={true} position={{ x: 100, y: 200 }} onClick={onClick} />,
    );
    const toolbar = screen.getByRole('toolbar');
    expect(toolbar).toHaveStyle({ left: '100px', top: '200px' });
  });

  it('toggles sensory submenu on click', async () => {
    const onClick = vi.fn();
    render(
      <SelectionToolbar actions={mockActions} visible={true} position={{ x: 100, y: 200 }} onClick={onClick} />,
    );
    const toggle = screen.getByText('Sensory detail');
    await userEvent.click(toggle);
    // Submenu items should be visible after toggle
    expect(screen.getByText('Sight & color')).toBeInTheDocument();
  });

  it('renders all action buttons', () => {
    const onClick = vi.fn();
    render(
      <SelectionToolbar actions={mockActions} visible={true} position={{ x: 100, y: 200 }} onClick={onClick} />,
    );
    expect(screen.getByText('Tighten & polish')).toBeInTheDocument();
    expect(screen.getByText('Continue')).toBeInTheDocument();
  });
});
