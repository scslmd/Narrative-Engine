import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { ManuscriptEditor } from './ManuscriptEditor';

const baseDocument = {
  document_id: 'doc-1',
  project_id: 'proj-1',
  title: 'Chapter 1',
  content: 'Hello world',
  chapter_id: null,
  scene_id: null,
  current_draft_artifact_id: null,
  version: 1,
} as const;

describe('ManuscriptEditor', () => {
  it('disables selection actions when no range is selected', () => {
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
        isDark={false}
      />,
    );

    expect(screen.getByRole('button', { name: 'Assist: Selection' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Fork Selection' })).toBeDisabled();
  });

  it('captures selection and enables assist actions with selected range', () => {
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
        isDark={false}
      />,
    );

    const textarea = screen.getByPlaceholderText('Start writing or paste your content here...') as HTMLTextAreaElement;
    fireEvent.select(textarea, { target: { selectionStart: 0, selectionEnd: 5, value: 'Hello world' } });
    expect(onSelectionChange).toHaveBeenCalledWith(0, 5, 'Hello world');

    fireEvent.click(screen.getByRole('button', { name: 'Assist: Selection' }));
    fireEvent.click(screen.getByRole('button', { name: 'Fork Selection' }));

    expect(onAssistRequest).toHaveBeenCalledWith(
      'line_edit_selection',
      'Tighten and polish this selected passage.',
    );
    expect(onAssistRequest).toHaveBeenCalledWith(
      'fork_from_selection',
      'Fork a new variant from this selected passage.',
    );
  });
});
