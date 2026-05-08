import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '../__tests__/test-utils';
import { GuidedSetupView } from './GuidedSetupView';
import type { CategoryProgress } from '../services/guidedSetup';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

vi.mock('../hooks/useGuidedSetup', () => ({
  useGuidedSetup: () => ({
    isAnalyzing: false,
    createMutation: { isPending: false },
    handleAnalyze: vi.fn(),
    handleSubmitCreate: vi.fn(),
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
  it('shows "Save What You Have" when readyToCreate is false', () => {
    setStore({
      ...withProjectName(),
      readyToCreate: false,
    });

    render(<GuidedSetupView />);
    expect(screen.getByRole('button', { name: 'Save What You Have' })).toBeInTheDocument();
  });

  it('shows "Save Project" with checkmark when readyToCreate is true', () => {
    setStore({
      ...withProjectName(),
      readyToCreate: true,
    });

    render(<GuidedSetupView />);
    expect(screen.getByRole('button', { name: 'Save Project' })).toBeInTheDocument();
  });

  it('uses emerald gradient when ready', () => {
    setStore({
      ...withProjectName(),
      readyToCreate: true,
    });

    render(<GuidedSetupView />);
    const btn = screen.getByRole('button', { name: 'Save Project' });
    expect(btn.className).toContain('from-emerald-500');
    expect(btn.className).toContain('to-teal-500');
  });

  it('uses violet gradient when not ready', () => {
    setStore({
      ...withProjectName(),
      readyToCreate: false,
    });

    render(<GuidedSetupView />);
    const btn = screen.getByRole('button', { name: 'Save What You Have' });
    expect(btn.className).toContain('from-violet-500');
    expect(btn.className).toContain('to-purple-500');
  });

  it('hides button when hasContent is false', () => {
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
    expect(screen.queryByRole('button', { name: 'Save What You Have' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save Project' })).not.toBeInTheDocument();
  });

  it('passes categoryProgress to FieldPreview', () => {
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
    const preview = screen.getByTestId('field-preview');
    expect(preview.textContent).toContain('config');
    expect(preview.textContent).toContain('foundation');
  });
});
