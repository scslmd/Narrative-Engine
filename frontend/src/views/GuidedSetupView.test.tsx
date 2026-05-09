import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../__tests__/test-utils';
import userEvent from '@testing-library/user-event';
import { GuidedSetupView } from './GuidedSetupView';
import type { CategoryProgress } from '../services/guidedSetup';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

// Mock setInterval/clearInterval to prevent act() warnings from the health-check polling
vi.spyOn(global, 'setInterval').mockReturnValue(1 as unknown as ReturnType<typeof setInterval>);
vi.spyOn(global, 'clearInterval').mockImplementation(() => {});

const mockHandleAnalyze = vi.fn().mockResolvedValue(undefined);
const mockSubmitCreate = vi.fn();

const mockHookState = {
  isAnalyzing: false,
  isPending: false,
};

function setHook(overrides: Partial<typeof mockHookState>) {
  Object.assign(mockHookState, overrides);
}

vi.mock('../hooks/useGuidedSetup', () => ({
  useGuidedSetup: () => ({
    isAnalyzing: mockHookState.isAnalyzing,
    createMutation: { isPending: mockHookState.isPending },
    handleAnalyze: mockHandleAnalyze,
    handleSubmitCreate: mockSubmitCreate,
  }),
}));

vi.mock('../services/guidedSetup', () => ({
  checkLlmHealth: vi.fn().mockResolvedValue({ ok: true, backend: 'llama.cpp', model: 'test-model' }),
  emptyExtractedFields: vi.fn(() => ({
    config: { project_name: '', genre: '', tone_profile: '', pov: '', story_structure: '', primary_language: '', secondary_language: null, constraints: [] },
    foundation: { premise_text: '', logline: '', thematic_spine: '', emotional_promise: '', target_audience: '', complexity_level: '', success_definition: '', narrative_constraints: [] },
    characters: [],
    world_bible: [],
    arcs: [],
    sequences: [],
    chapters: [],
  })),
}));

vi.mock('../components/guided-setup/FieldPreview', () => ({
  FieldPreview: vi.fn(({ categoryProgress }) => (
    <div data-testid="field-preview">
      {categoryProgress && categoryProgress.length > 0
        ? `categories: ${categoryProgress.map((c: CategoryProgress) => c.category).join(', ')}`
        : 'no progress'}
    </div>
  )),
}));

vi.mock('../components/guided-setup/ChatPanel', () => ({
  ChatPanel: vi.fn(() => <div data-testid="chat-panel">Chat</div>),
}));

beforeEach(() => {
  vi.clearAllMocks();
  Object.assign(mockHookState, { isAnalyzing: false, isPending: false });
});

const mockStoreState = {
  accumulatedFields: {
    config: { project_name: '', genre: '', tone_profile: '', pov: '', story_structure: '', primary_language: '', secondary_language: null, constraints: [] as string[] },
    foundation: { premise_text: '', logline: '', thematic_spine: '', emotional_promise: '', target_audience: '', complexity_level: '', success_definition: '', narrative_constraints: [] as string[] },
    characters: [],
    world_bible: [],
    arcs: [],
    sequences: [],
    chapters: [],
  },
  conversationHistory: [{ role: 'system', content: 'Welcome', turn: 1 }],
  readyToCreate: false,
  progress: 0,
  categoryProgress: [] as CategoryProgress[],
  updateFields: vi.fn(),
};

vi.mock('../stores/guidedSetupStore', () => ({
  useGuidedSetupStore: () => mockStoreState,
}));

function setStore(overrides: Partial<typeof mockStoreState>) {
  Object.assign(mockStoreState, overrides);
}

const emptyConfig = { project_name: '', genre: '', tone_profile: '', pov: '', story_structure: '', primary_language: '', secondary_language: null, constraints: [] as string[] };
const emptyFoundation = { premise_text: '', logline: '', thematic_spine: '', emotional_promise: '', target_audience: '', complexity_level: '', success_definition: '', narrative_constraints: [] as string[] };
const emptyLists = { characters: [], world_bible: [], arcs: [], sequences: [], chapters: [] };

function withProjectName(name = 'My Story') {
  return {
    accumulatedFields: {
      config: { ...emptyConfig, project_name: name },
      foundation: { ...emptyFoundation },
      ...emptyLists,
    },
    conversationHistory: [{ role: 'system', content: 'Welcome', turn: 1 }],
  };
}

describe('GuidedSetupView save button', () => {
  it('shows "Save What You Have" when readyToCreate is false', async () => {
    setStore({
      ...withProjectName(),
      readyToCreate: false,
    });

    render(<GuidedSetupView />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Save What You Have' })).toBeInTheDocument();
    });
  });

  it('shows "Save Project" with checkmark when readyToCreate is true', async () => {
    setStore({
      ...withProjectName(),
      readyToCreate: true,
    });

    render(<GuidedSetupView />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Save Project' })).toBeInTheDocument();
    });
  });

  it('uses emerald gradient when ready', async () => {
    setStore({
      ...withProjectName(),
      readyToCreate: true,
    });

    render(<GuidedSetupView />);
    const btn = await waitFor(() => screen.getByRole('button', { name: 'Save Project' }));
    expect(btn.className).toContain('from-emerald-500');
    expect(btn.className).toContain('to-teal-500');
  });

  it('uses violet gradient when not ready', async () => {
    setStore({
      ...withProjectName(),
      readyToCreate: false,
    });

    render(<GuidedSetupView />);
    const btn = await waitFor(() => screen.getByRole('button', { name: 'Save What You Have' }));
    expect(btn.className).toContain('from-violet-500');
    expect(btn.className).toContain('to-purple-500');
  });

  it('hides button when hasContent is false', async () => {
    setStore({
      accumulatedFields: {
        config: { ...emptyConfig },
        foundation: { ...emptyFoundation },
        ...emptyLists,
      },
      conversationHistory: [{ role: 'system', content: 'Welcome', turn: 1 }],
      readyToCreate: false,
    });

    render(<GuidedSetupView />);
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: 'Save What You Have' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Save Project' })).not.toBeInTheDocument();
    });
  });

  it('passes categoryProgress to FieldPreview', async () => {
    const mockProgress: CategoryProgress[] = [
      { category: 'config', completeness: 0.5, confidence: 0.7, fields_collected: ['project_name'], fields_missing: ['genre'] },
      { category: 'foundation', completeness: 0.8, confidence: 0.9, fields_collected: ['premise_text', 'logline'], fields_missing: [] },
    ];

    setStore({
      ...withProjectName(),
      readyToCreate: false,
      categoryProgress: mockProgress,
    });

    render(<GuidedSetupView />);
    const preview = await waitFor(() => screen.getByTestId('field-preview'));
    expect(preview.textContent).toContain('config');
    expect(preview.textContent).toContain('foundation');
  });

  it('calls handleSubmitCreate when save button is clicked', async () => {
    setStore({
      ...withProjectName(),
      readyToCreate: false,
    });

    render(<GuidedSetupView />);
    const btn = await waitFor(() => screen.getByRole('button', { name: 'Save What You Have' }));
    await userEvent.click(btn);
    expect(mockSubmitCreate).toHaveBeenCalled();
  });

  it('shows creating indicator when isCreating is true', async () => {
    setHook({ isPending: true });
    setStore({
      ...withProjectName(),
      readyToCreate: false,
    });

    render(<GuidedSetupView />);
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /save/i })).not.toBeInTheDocument();
      expect(screen.getByText('Creating project...')).toBeInTheDocument();
    });
  });
});
