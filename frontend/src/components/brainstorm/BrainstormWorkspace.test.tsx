import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../../__tests__/test-utils';
import userEvent from '@testing-library/user-event';
import { server } from '../../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { BrainstormWorkspace } from './BrainstormWorkspace';
import type { BrainstormItem } from '../../types/brainstorm';

const mockItem: BrainstormItem = {
  item_id: 'item-1',
  project_id: 'proj-1',
  content: 'Test idea',
  status: 'keep',
  tags: [],
  source_notes: null,
  item_type: 'character',
  promoted_to: null,
  promoted_at: null,
};

const mockPromotedItem: BrainstormItem = {
  ...mockItem,
  item_id: 'item-2',
  content: 'Already promoted idea',
  promoted_to: 'character',
  promoted_at: '2025-01-01T00:00:00Z',
};

function renderWorkspace(props?: Partial<React.ComponentProps<typeof BrainstormWorkspace>>) {
  return render(
    <BrainstormWorkspace
      projectId="proj-1"
      items={[mockItem]}
      onItemAdd={vi.fn()}
      onClusterCreate={vi.fn()}
      onPromote={vi.fn()}
      {...props}
    />,
  );
}

describe('BrainstormWorkspace promote', () => {
  describe('promote button visibility', () => {
    it('shows promote button on unpromoted items', () => {
      renderWorkspace();
      expect(screen.getByRole('button', { name: 'Promote' })).toBeInTheDocument();
    });

    it('hides promote button on already promoted items', () => {
      renderWorkspace({ items: [mockPromotedItem] });
      expect(screen.queryByRole('button', { name: 'Promote' })).not.toBeInTheDocument();
    });

    it('shows promoted badge with target type for promoted items', () => {
      renderWorkspace({ items: [mockPromotedItem] });
      expect(screen.getByText(/Promoted:/i)).toBeInTheDocument();
    });
  });

  describe('promotion dialog', () => {
    it('opens promotion dialog when promote button is clicked', async () => {
      const user = userEvent.setup();
      renderWorkspace();

      await user.click(screen.getByRole('button', { name: 'Promote' }));

      expect(screen.getByText(/promote to/i)).toBeInTheDocument();
    });

    it('renders target type options', async () => {
      const user = userEvent.setup();
      renderWorkspace();

      await user.click(screen.getByRole('button', { name: 'Promote' }));

      // Use getAllByText since "Character" also appears in the card badge
      const characterTexts = screen.getAllByText(/Character/i);
      expect(characterTexts.length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/World Bible/i)).toBeInTheDocument();
      expect(screen.getByText(/Arc/i)).toBeInTheDocument();
    });

    it('submits promotion on confirm', async () => {
      const user = userEvent.setup();
      const onPromote = vi.fn();
      renderWorkspace({ onPromote });

      await user.click(screen.getByRole('button', { name: 'Promote' }));
      // There are two comboboxes: status selector and target type. Pick the one in dialog.
      const comboboxes = screen.getAllByRole('combobox');
      const targetKindSelect = comboboxes[1];
      await user.selectOptions(targetKindSelect, 'character');
      fireEvent.change(screen.getByPlaceholderText(/target id/i), {
        target: { value: 'char-abc' },
      });
      await user.click(screen.getByRole('button', { name: /confirm/i }));

      expect(onPromote).toHaveBeenCalledWith(
        expect.objectContaining({
          item_id: 'item-1',
          project_id: 'proj-1',
          target_object_kind: 'character',
          target_object_id: 'char-abc',
        }),
      );
    });

    it('disables confirm button when target ID is empty', async () => {
      const user = userEvent.setup();
      renderWorkspace({ onPromote: vi.fn() });

      await user.click(screen.getByRole('button', { name: 'Promote' }));
      const comboboxes = screen.getAllByRole('combobox');
      await user.selectOptions(comboboxes[1], 'character');

      const confirmBtn = screen.getByRole('button', { name: /confirm/i });
      expect(confirmBtn).toBeDisabled();
    });

    it('enables confirm button when target ID is provided', async () => {
      const user = userEvent.setup();
      renderWorkspace({ onPromote: vi.fn() });

      await user.click(screen.getByRole('button', { name: 'Promote' }));
      fireEvent.change(screen.getByPlaceholderText(/target id/i), {
        target: { value: 'char-abc' },
      });

      const confirmBtn = screen.getByRole('button', { name: /confirm/i });
      expect(confirmBtn).not.toBeDisabled();
    });

    it('closes dialog on cancel', async () => {
      const user = userEvent.setup();
      renderWorkspace();

      await user.click(screen.getByRole('button', { name: 'Promote' }));
      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(screen.queryByText(/promote to/i)).not.toBeInTheDocument();
    });
  });

  describe('API error handling', () => {
    it('already promoted items do not show promote button', async () => {
      server.use(
        http.post('/story-development/brainstorm/items/promote', () =>
          HttpResponse.json({ detail: 'Already promoted' }, { status: 409 }),
        ),
      );

      renderWorkspace({ items: [mockPromotedItem] });
      expect(screen.queryByRole('button', { name: 'Promote' })).not.toBeInTheDocument();
    });

    it('displays 400 validation error in dialog', async () => {
      const user = userEvent.setup();
      const onPromote = vi.fn().mockRejectedValue(
        Object.assign(new Error('Invalid target type'), { response: { status: 400 } }),
      );
      renderWorkspace({ onPromote });

      await user.click(screen.getByRole('button', { name: 'Promote' }));
      fireEvent.change(screen.getByPlaceholderText(/target id/i), {
        target: { value: 'char-abc' },
      });
      await user.click(screen.getByRole('button', { name: /confirm/i }));

      // Dialog should remain open and show error
      await waitFor(() => {
        expect(screen.getByText(/Invalid target type/i)).toBeInTheDocument();
      });
    });
  });
});
