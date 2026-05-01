import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '../../__tests__/test-utils';
import userEvent from '@testing-library/user-event';
import { server } from '../../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { StoryImportModal } from './StoryImportModal';

const longText = 'A'.repeat(100);

function renderModal(isOpen = true, onClose = vi.fn()) {
  return render(<StoryImportModal isOpen={isOpen} onClose={onClose} />);
}

describe('StoryImportModal', () => {
  beforeEach(() => {
    server.use(
      http.get('/health/ready', () => {
        return HttpResponse.json({ components: { inference: { backend: 'llama.cpp' } } });
      }),
    );
  });

  it('does not render when closed', () => {
    renderModal(false);
    expect(screen.queryByText(/import existing story/i)).not.toBeInTheDocument();
  });

  it('renders form fields when open', () => {
    renderModal();
    expect(screen.getByText(/import existing story/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/enter project title/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/paste your completed story/i)).toBeInTheDocument();
  });

  it('shows validation error for short text', async () => {
    const user = userEvent.setup();
    const { container } = renderModal();

    await user.type(
      screen.getByPlaceholderText(/paste your completed story/i),
      'short',
    );
    fireEvent.submit(container.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText(/must be at least 50 characters/i)).toBeInTheDocument();
    });
  });

  it('shows validation error for missing project name in story mode', async () => {
    const user = userEvent.setup();
    const { container } = renderModal();

    await user.type(
      screen.getByPlaceholderText(/paste your completed story/i),
      longText,
    );
    fireEvent.submit(container.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText(/project name is required/i)).toBeInTheDocument();
    });
  });

  it('submits import and shows loading state', async () => {
    const user = userEvent.setup({ delay: 10 });
    server.use(
      http.post('/projects/import-story', () => {
        return HttpResponse.json({
          import_id: 'test-import-1',
          status: 'pending',
        });
      }),
      http.get('/projects/import/test-import-1', () => {
        return HttpResponse.json({
          import_id: 'test-import-1',
          status: 'running',
          phase: 'Analyzing story structure...',
          chapters_processed: 0,
          total_estimated_chapters: 3,
          result: null,
          error: null,
        });
      }),
    );

    const { container } = renderModal();

    await user.type(
      screen.getByPlaceholderText(/enter project title/i),
      'Test Project',
    );
    await user.type(
      screen.getByPlaceholderText(/paste your completed story/i),
      longText,
    );

    fireEvent.submit(container.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText(/processing/i)).toBeInTheDocument();
    });
  });

  it('displays error on failed import submission', async () => {
    const user = userEvent.setup();
    server.use(
      http.post('/projects/import-story', () => {
        return HttpResponse.json(
          { detail: 'Server error' },
          { status: 500 },
        );
      }),
    );

    const { container } = renderModal();

    await user.type(
      screen.getByPlaceholderText(/enter project title/i),
      'Test Project',
    );
    await user.type(
      screen.getByPlaceholderText(/paste your completed story/i),
      longText,
    );

    fireEvent.submit(container.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText(/server error occurred/i)).toBeInTheDocument();
    });
  });

  it('switches between import modes', async () => {
    const user = userEvent.setup();
    renderModal();

    expect(screen.getByPlaceholderText(/enter project title/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /extract mythos/i }));

    expect(
      screen.queryByPlaceholderText(/enter project title/i),
    ).not.toBeInTheDocument();
    expect(screen.getByPlaceholderText(/mythology or mythological texts/i))
      .toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /extract patterns/i }));

    expect(screen.getByPlaceholderText(/a story or mythological text here/i))
      .toBeInTheDocument();
  });

  it('closes modal when cancel is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderModal(true, onClose);

    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes modal when backdrop is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderModal(true, onClose);

    const backdrop = document.querySelector('.fixed.inset-0.bg-black\\/50');
    expect(backdrop).toBeInTheDocument();
    await user.click(backdrop!);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('shows character and word counts for story mode', async () => {
    const user = userEvent.setup();
    renderModal();

    const textInput = screen.getByPlaceholderText(/paste your completed story/i);
    await user.type(textInput, 'Hello world this is a test story with enough characters to show the count.');

    await waitFor(() => {
      expect(screen.getByText(/\d+ characters/i)).toBeInTheDocument();
      expect(screen.getByText(/\d+ words/i)).toBeInTheDocument();
    });
  });

  it('disables submit button during import', async () => {
    const user = userEvent.setup({ delay: 10 });
    server.use(
      http.post('/projects/import-story', () => {
        return HttpResponse.json({
          import_id: 'test-import-2',
          status: 'pending',
        });
      }),
      http.get('/projects/import/test-import-2', () => {
        return HttpResponse.json({
          import_id: 'test-import-2',
          status: 'running',
          phase: 'Analyzing...',
          chapters_processed: 0,
          total_estimated_chapters: 1,
          result: null,
          error: null,
        });
      }),
    );

    const { container } = renderModal();

    await user.type(
      screen.getByPlaceholderText(/enter project title/i),
      'Test Project',
    );
    await user.type(
      screen.getByPlaceholderText(/paste your completed story/i),
      longText,
    );

    fireEvent.submit(container.querySelector('form')!);

    await waitFor(() => {
      const submitBtn = screen.getByRole('button', { name: /processing/i });
      expect(submitBtn).toBeDisabled();
    });
  });

  it('does not require project name in mythos mode', async () => {
    const user = userEvent.setup({ delay: 10 });
    server.use(
      http.post('/projects/import-mythos', () => {
        return HttpResponse.json({ extraction_id: 'mythos-1' });
      }),
      http.get('/projects/extraction/mythos-1', () => {
        return HttpResponse.json({
          extraction_id: 'mythos-1',
          status: 'running',
          phase: 'Processing...',
          result: null,
          error: null,
        });
      }),
    );

    const { container } = renderModal();
    await user.click(screen.getByRole('button', { name: /extract mythos/i }));

    await user.type(
      screen.getByPlaceholderText(/mythology or mythological texts/i),
      longText,
    );

    fireEvent.submit(container.querySelector('form')!);

    await waitFor(() => {
      expect(screen.getByText(/processing/i)).toBeInTheDocument();
    });
  });
});
