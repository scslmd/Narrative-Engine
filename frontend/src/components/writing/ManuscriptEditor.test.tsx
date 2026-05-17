import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { ManuscriptEditor } from './ManuscriptEditor';

const baseDocument = {
  document_id: 'doc-1',
  project_id: 'proj-1',
  title: 'Chapter 1',
  display_title: null,
  content: 'Hello world',
  chapter_id: null,
  scene_id: null,
  current_draft_artifact_id: null,
  version: 1,
} as const;

describe('ManuscriptEditor', () => {
  it('hides assist dropdown when no range is selected', () => {
    const onAssistRequest = vi.fn();
    render(
      <ManuscriptEditor
        document={baseDocument}
        isEditing
        editContent="Hello world"
        wordCount={2}
        charCount={11}
        openSuggestions={[]}
        onEdit={() => {}}
        onSave={() => {}}
        onCancel={() => {}}
        onContentChange={() => {}}
        onAssistRequest={onAssistRequest}
        selectedRange={null}
        scrollTarget={null}
        isDark={false}
      />,
    );

    // Dropdown actions should not be visible
    expect(screen.queryByText('Tighten & polish')).toBeNull();
    expect(screen.queryAllByText('Rewrite')).toHaveLength(0);
  });

  it('opens assist dropdown on click with selected range', () => {
    const onSelectionChange = vi.fn();
    const onAssistRequest = vi.fn();
    render(
      <ManuscriptEditor
        document={baseDocument}
        isEditing
        editContent="Hello world"
        wordCount={2}
        charCount={11}
        openSuggestions={[]}
        onEdit={() => {}}
        onSave={() => {}}
        onCancel={() => {}}
        onContentChange={() => {}}
        onSelectionChange={onSelectionChange}
        onAssistRequest={onAssistRequest}
        selectedRange={{
          start_offset: 0,
          end_offset: 5,
          selected_text: 'Hello',
          anchor_before: '',
          anchor_after: ' world',
        }}
        scrollTarget={null}
        isDark={false}
      />,
    );

    const textarea = screen.getByPlaceholderText('Start writing or paste your content here...') as HTMLTextAreaElement;
    fireEvent.select(textarea, { target: { selectionStart: 0, selectionEnd: 5, value: 'Hello world' } });
    expect(onSelectionChange).toHaveBeenCalledWith(0, 5, 'Hello world');

    // Find the Assist button (not "Assist: Review")
    const buttons = screen.getAllByRole('button');
    const assistButton = buttons.find((btn) => btn.textContent?.includes('Assist') && !btn.textContent?.includes('Review'))!;
    expect(assistButton).not.toBeDisabled();

    // Click to open dropdown
    fireEvent.click(assistButton);

    // Actions should be visible after clicking
    const tightenElements = screen.getAllByText('Tighten & polish');
    expect(tightenElements.length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Sensory detail').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Continue from here').length).toBeGreaterThanOrEqual(1);

    // Click "Fork as draft" action
    fireEvent.click(screen.getAllByText('Fork as draft')[0]);
    expect(onAssistRequest).toHaveBeenCalledWith(
      'fork_from_selection',
      'Fork a new variant from this selected passage.',
    );
  });
});
