import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '../../__tests__/test-utils';
import { ApiError } from '../../lib/api';
import { SequencePlanSection } from './SequencePlanSection';
import { ChapterPlanSection } from './ChapterPlanSection';
import { ScenePlanSection } from './ScenePlanSection';
import { BeatPlanSection } from './BeatPlanSection';
import { DependenciesSection } from './DependenciesSection';
import { ChapterPacketsSection } from './ChapterPacketsSection';
import { StoryboardCardsSection } from './StoryboardCardsSection';

const mockOnRetry = vi.fn();

function baseSequenceProps() {
  return {
    plans: [],
    isLoading: false,
    createOpen: false,
    createTitle: '',
    createSummary: '',
    editOpenId: null,
    editTitle: '',
    editSummary: '',
    onCreateOpen: vi.fn(),
    onCreateClose: vi.fn(),
    onCreateTitleChange: vi.fn(),
    onCreateSummaryChange: vi.fn(),
    onCreate: vi.fn(),
    onEditOpen: vi.fn(),
    onEditClose: vi.fn(),
    onEditTitleChange: vi.fn(),
    onEditSummaryChange: vi.fn(),
    onUpdate: vi.fn(),
    onReorderUp: vi.fn(),
    onReorderDown: vi.fn(),
    onCreateButtonDisabled: true,
    onUpdateButtonDisabled: false,
    error: null,
    onRetry: mockOnRetry,
  };
}

function baseChapterProps() {
  return {
    plans: [],
    isLoading: false,
    createOpen: false,
    createTitle: '',
    createObjective: '',
    createConflict: '',
    createStakes: '',
    createSequenceId: '',
    editOpenId: null,
    editTitle: '',
    editObjective: '',
    editConflict: '',
    editStakes: '',
    onCreateOpen: vi.fn(),
    onCreateClose: vi.fn(),
    onCreateTitleChange: vi.fn(),
    onCreateObjectiveChange: vi.fn(),
    onCreateConflictChange: vi.fn(),
    onCreateStakesChange: vi.fn(),
    onCreateSequenceIdChange: vi.fn(),
    onCreate: vi.fn(),
    onEditOpen: vi.fn(),
    onEditClose: vi.fn(),
    onEditTitleChange: vi.fn(),
    onEditObjectiveChange: vi.fn(),
    onEditConflictChange: vi.fn(),
    onEditStakesChange: vi.fn(),
    onUpdate: vi.fn(),
    onReorderUp: vi.fn(),
    onReorderDown: vi.fn(),
    onCreateButtonDisabled: true,
    onUpdateButtonDisabled: false,
    error: null,
    onRetry: mockOnRetry,
  };
}

function baseSceneProps() {
  return {
    plans: [],
    isLoading: false,
    createOpen: false,
    createTitle: '',
    createObjective: '',
    createConflict: '',
    createStakes: '',
    createChapterId: '',
    editOpenId: null,
    editTitle: '',
    editObjective: '',
    editConflict: '',
    editStakes: '',
    onCreateOpen: vi.fn(),
    onCreateClose: vi.fn(),
    onCreateTitleChange: vi.fn(),
    onCreateObjectiveChange: vi.fn(),
    onCreateConflictChange: vi.fn(),
    onCreateStakesChange: vi.fn(),
    onCreateChapterIdChange: vi.fn(),
    onCreate: vi.fn(),
    onEditOpen: vi.fn(),
    onEditClose: vi.fn(),
    onEditTitleChange: vi.fn(),
    onEditObjectiveChange: vi.fn(),
    onEditConflictChange: vi.fn(),
    onEditStakesChange: vi.fn(),
    onUpdate: vi.fn(),
    onReorderUp: vi.fn(),
    onReorderDown: vi.fn(),
    onCreateButtonDisabled: true,
    onUpdateButtonDisabled: false,
    error: null,
    onRetry: mockOnRetry,
  };
}

function baseBeatProps() {
  return {
    plans: [],
    isLoading: false,
    createOpen: false,
    createObjective: '',
    createConflict: '',
    createStakes: '',
    editOpenId: null,
    editObjective: '',
    editConflict: '',
    editStakes: '',
    editArcStage: '',
    onCreateOpen: vi.fn(),
    onCreateClose: vi.fn(),
    onCreateObjectiveChange: vi.fn(),
    onCreateConflictChange: vi.fn(),
    onCreateStakesChange: vi.fn(),
    onCreate: vi.fn(),
    onEditOpen: vi.fn(),
    onEditClose: vi.fn(),
    onEditObjectiveChange: vi.fn(),
    onEditConflictChange: vi.fn(),
    onEditStakesChange: vi.fn(),
    onEditArcStageChange: vi.fn(),
    onUpdate: vi.fn(),
    onCreateButtonDisabled: true,
    onUpdateButtonDisabled: false,
    error: null,
    onRetry: mockOnRetry,
  };
}

function basePacketProps() {
  return {
    packets: [],
    isLoading: false,
    createOpen: false,
    createChapterId: '',
    onCreateOpen: vi.fn(),
    onCreateClose: vi.fn(),
    onCreateChapterIdChange: vi.fn(),
    onCreate: vi.fn(),
    onCreateButtonDisabled: true,
    error: null,
    onRetry: mockOnRetry,
  };
}

function baseCardProps() {
  return {
    cards: [],
    isLoading: false,
    createOpen: false,
    createTitle: '',
    createContent: '',
    createType: 'idea',
    onCreateOpen: vi.fn(),
    onCreateClose: vi.fn(),
    onCreateTitleChange: vi.fn(),
    onCreateContentChange: vi.fn(),
    onCreateTypeChange: vi.fn(),
    onCreate: vi.fn(),
    onCreateButtonDisabled: true,
    editOpenId: null,
    editTitle: '',
    editContent: '',
    editType: 'idea',
    onEditOpen: vi.fn(),
    onEditClose: vi.fn(),
    onEditTitleChange: vi.fn(),
    onEditContentChange: vi.fn(),
    onEditTypeChange: vi.fn(),
    onUpdate: vi.fn(),
    onDelete: vi.fn(),
    onReorder: vi.fn(),
    onUpdateButtonDisabled: false,
    error: null,
    onRetry: mockOnRetry,
  };
}

function baseDepProps() {
  return {
    dependencies: [],
    isLoading: false,
    error: null,
    onRetry: mockOnRetry,
  };
}

describe('Planning section error states', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('SequencePlanSection', () => {
    it('shows error banner when error is provided', () => {
      const props = baseSequenceProps();
      const error = new ApiError('Network error', 500);
      render(<SequencePlanSection {...props} error={error} />);
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });

    it('shows loading skeleton when isLoading is true', () => {
      const props = baseSequenceProps();
      render(<SequencePlanSection {...props} isLoading={true} />);
      expect(screen.getAllByTestId('skeleton-line').length).toBeGreaterThan(0);
    });

    it('shows empty state with CTA for sequences', () => {
      const props = baseSequenceProps();
      render(<SequencePlanSection {...props} />);
      expect(screen.getByText(/No sequences yet/i)).toBeInTheDocument();
    });

    it('renders data when plans are provided', () => {
      const props = baseSequenceProps();
      const plans = [{ sequence_id: 's1', project_id: 'p1', title: 'Act One', summary: 'Setup', beat_ids: [], chapter_ids: [], status: 'active' }];
      render(<SequencePlanSection {...props} plans={plans} />);
      expect(screen.getByText('Act One')).toBeInTheDocument();
    });
  });

  describe('ChapterPlanSection', () => {
    it('shows error banner when error is provided', () => {
      const props = baseChapterProps();
      const error = new ApiError('Server error', 500);
      render(<ChapterPlanSection {...props} error={error} />);
      expect(screen.getByText(/Server error/)).toBeInTheDocument();
    });

    it('shows loading skeleton when isLoading is true', () => {
      const props = baseChapterProps();
      render(<ChapterPlanSection {...props} isLoading={true} />);
      expect(screen.getAllByTestId('skeleton-line').length).toBeGreaterThan(0);
    });

    it('shows empty state with CTA for chapters', () => {
      const props = baseChapterProps();
      render(<ChapterPlanSection {...props} />);
      expect(screen.getByText(/No chapters yet/i)).toBeInTheDocument();
    });
  });

  describe('ScenePlanSection', () => {
    it('shows error banner when error is provided', () => {
      const props = baseSceneProps();
      const error = new ApiError('Bad request', 400);
      render(<ScenePlanSection {...props} error={error} />);
      expect(screen.getByText(/Bad request/)).toBeInTheDocument();
    });

    it('shows loading skeleton when isLoading is true', () => {
      const props = baseSceneProps();
      render(<ScenePlanSection {...props} isLoading={true} />);
      expect(screen.getAllByTestId('skeleton-line').length).toBeGreaterThan(0);
    });

    it('shows empty state with CTA for scenes', () => {
      const props = baseSceneProps();
      render(<ScenePlanSection {...props} />);
      expect(screen.getByText(/No scenes yet/i)).toBeInTheDocument();
    });
  });

  describe('BeatPlanSection', () => {
    it('shows error banner when error is provided', () => {
      const props = baseBeatProps();
      const error = new ApiError('Timeout', 504);
      render(<BeatPlanSection {...props} error={error} />);
      expect(screen.getByText(/Timeout/)).toBeInTheDocument();
    });

    it('shows loading skeleton when isLoading is true', () => {
      const props = baseBeatProps();
      render(<BeatPlanSection {...props} isLoading={true} />);
      expect(screen.getAllByTestId('skeleton-line').length).toBeGreaterThan(0);
    });

    it('shows empty state with CTA for beats', () => {
      const props = baseBeatProps();
      render(<BeatPlanSection {...props} />);
      expect(screen.getByText(/No beats yet/i)).toBeInTheDocument();
    });
  });

  describe('DependenciesSection', () => {
    it('shows error banner when error is provided', () => {
      const props = baseDepProps();
      const error = new ApiError('Forbidden', 403);
      render(<DependenciesSection {...props} error={error} />);
      expect(screen.getByText(/Forbidden/)).toBeInTheDocument();
    });

    it('shows loading skeleton when isLoading is true', () => {
      const props = baseDepProps();
      render(<DependenciesSection {...props} isLoading={true} />);
      expect(screen.getAllByTestId('skeleton-line').length).toBeGreaterThan(0);
    });

    it('shows empty state without CTA for dependencies', () => {
      const props = baseDepProps();
      render(<DependenciesSection {...props} />);
      expect(screen.getByText(/No dependencies/i)).toBeInTheDocument();
    });
  });

  describe('ChapterPacketsSection', () => {
    it('shows error banner when error is provided', () => {
      const props = basePacketProps();
      const error = new ApiError('Not found', 404);
      render(<ChapterPacketsSection {...props} error={error} />);
      expect(screen.getByText(/Not found/)).toBeInTheDocument();
    });

    it('shows loading skeleton when isLoading is true', () => {
      const props = basePacketProps();
      render(<ChapterPacketsSection {...props} isLoading={true} />);
      expect(screen.getAllByTestId('skeleton-line').length).toBeGreaterThan(0);
    });

    it('shows empty state with CTA for chapter packets', () => {
      const props = basePacketProps();
      render(<ChapterPacketsSection {...props} />);
      expect(screen.getByText(/No chapter packets/i)).toBeInTheDocument();
    });
  });

  describe('StoryboardCardsSection', () => {
    it('shows error banner when error is provided', () => {
      const props = baseCardProps();
      const error = new ApiError('Service unavailable', 503);
      render(<StoryboardCardsSection {...props} error={error} />);
      expect(screen.getByText(/Service unavailable/)).toBeInTheDocument();
    });

    it('shows loading skeleton when isLoading is true', () => {
      const props = baseCardProps();
      render(<StoryboardCardsSection {...props} isLoading={true} />);
      expect(screen.getAllByTestId('skeleton-line').length).toBeGreaterThan(0);
    });

    it('shows empty state with CTA for storyboard cards', () => {
      const props = baseCardProps();
      render(<StoryboardCardsSection {...props} />);
      expect(screen.getByText(/No storyboard cards/i)).toBeInTheDocument();
    });
  });

  describe('partial failure independence', () => {
    it('one section error does not prevent another from rendering data', () => {
      const error = new ApiError('Fail', 500);
      const { unmount } = render(
        <>
          <SequencePlanSection {...baseSequenceProps()} error={error} />
          <ChapterPlanSection
            {...baseChapterProps()}
            plans={[{ chapter_id: 'c1', project_id: 'p1', title: 'Chapter One', summary: '', sequence_id: null, objective: 'Test', conflict: '', stakes: '', active_character_ids: [], continuity_requirements: [], unresolved_questions: [], status: 'active' }]}
          />
        </>,
      );

      expect(screen.getByText(/Fail/)).toBeInTheDocument();
      expect(screen.getByText('Chapter One')).toBeInTheDocument();

      unmount();
    });
  });
});
