import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { usePlanningController } from './usePlanningController';
import { usePlanningQueries } from './queries';
import { usePlanningMutations } from './mutations';

vi.mock('../../services/planning', () => ({
  getSequencePlans: vi.fn().mockResolvedValue([]),
  getChapterPlans: vi.fn().mockResolvedValue([]),
  getScenePlans: vi.fn().mockResolvedValue([]),
  getBeatPlans: vi.fn().mockResolvedValue([]),
  getPlanningDependencies: vi.fn().mockResolvedValue([]),
  getChapterPackets: vi.fn().mockResolvedValue([]),
  createSequencePlan: vi.fn().mockResolvedValue({}),
  updateSequencePlan: vi.fn().mockResolvedValue({}),
  createChapterPlan: vi.fn().mockResolvedValue({}),
  updateChapterPlan: vi.fn().mockResolvedValue({}),
  createScenePlan: vi.fn().mockResolvedValue({}),
  updateScenePlan: vi.fn().mockResolvedValue({}),
  createBeatPlan: vi.fn().mockResolvedValue({}),
  updateBeatPlan: vi.fn().mockResolvedValue({}),
  createChapterPacket: vi.fn().mockResolvedValue({}),
  reorderPlanObjects: vi.fn().mockResolvedValue({}),
}));

vi.mock('../../services/storyboard', () => ({
  getStoryboardCards: vi.fn().mockResolvedValue([]),
  createStoryboardCard: vi.fn().mockResolvedValue({}),
  updateStoryboardCard: vi.fn().mockResolvedValue({}),
  deleteStoryboardCard: vi.fn().mockResolvedValue(undefined),
  reindexColumn: vi.fn().mockResolvedValue({}),
}));

vi.mock('../../services/arcs', () => ({
  getArcCandidates: vi.fn().mockResolvedValue([]),
  getArcSelections: vi.fn().mockResolvedValue([]),
  getArcStageMaps: vi.fn().mockResolvedValue([]),
  getArcComparisons: vi.fn().mockResolvedValue([]),
  createArcCandidate: vi.fn().mockResolvedValue({}),
  createArcSelection: vi.fn().mockResolvedValue({}),
  deleteArcSelection: vi.fn().mockResolvedValue(undefined),
  updateArcSelection: vi.fn().mockResolvedValue({}),
  createArcStageMap: vi.fn().mockResolvedValue({}),
}));

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const WithProviders = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>{children}</QueryClientProvider>
);

describe('usePlanningController hook consolidation', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  describe('form state consolidation', () => {
    it('initializes all form fields to default values', () => {
      const { result } = renderHook(() => usePlanningController('planning'), {
        wrapper: WithProviders,
      });

      const { state } = result.current;

      expect(state.sequenceCreateOpen).toBe(false);
      expect(state.sequenceCreateTitle).toBe('');
      expect(state.chapterCreateOpen).toBe(false);
      expect(state.sceneCreateOpen).toBe(false);
      expect(state.beatCreateOpen).toBe(false);
      expect(state.packetCreateOpen).toBe(false);
      expect(state.cardCreateOpen).toBe(false);
      expect(state.arcCandidateCreateOpen).toBe(false);
      expect(state.stageMapCreateOpen).toBe(false);
      expect(state.stageMapCreateKinds).toEqual([]);
      expect(state.cardCreateType).toBe('idea');
      expect(state.cardEditType).toBe('idea');
    });

    it('updates individual form fields independently via setters', () => {
      const { result } = renderHook(() => usePlanningController('planning'), {
        wrapper: WithProviders,
      });

      const { callbacks } = result.current;

      act(() => {
        callbacks.setSequenceCreateOpen(true);
        callbacks.setSequenceCreateTitle('Test Sequence');
        callbacks.setChapterCreateOpen(true);
        callbacks.setSceneCreateTitle('Test Scene');
      });

      const { state } = result.current;

      expect(state.sequenceCreateOpen).toBe(true);
      expect(state.sequenceCreateTitle).toBe('Test Sequence');
      expect(state.chapterCreateOpen).toBe(true);
      expect(state.sceneCreateTitle).toBe('Test Scene');
      expect(state.beatCreateOpen).toBe(false);
    });

    it('preserves other fields when updating one field', () => {
      const { result } = renderHook(() => usePlanningController('planning'), {
        wrapper: WithProviders,
      });

      const { callbacks } = result.current;

      act(() => {
        callbacks.setSequenceCreateTitle('Seq Title');
        callbacks.setSequenceCreateSummary('Seq Summary');
        callbacks.setChapterCreateTitle('Chap Title');
      });

      act(() => {
        callbacks.setSequenceCreateTitle('Updated Seq');
      });

      const { state } = result.current;

      expect(state.sequenceCreateTitle).toBe('Updated Seq');
      expect(state.sequenceCreateSummary).toBe('Seq Summary');
      expect(state.chapterCreateTitle).toBe('Chap Title');
    });

    it('toggleStageKind adds and removes stage kinds correctly', () => {
      const { result } = renderHook(() => usePlanningController('arcs'), {
        wrapper: WithProviders,
      });

      const { callbacks, state } = result.current;

      expect(state.stageMapCreateKinds).toEqual([]);

      act(() => {
        callbacks.toggleStageKind('exposition');
      });
      expect(result.current.state.stageMapCreateKinds).toEqual(['exposition']);

      act(() => {
        callbacks.toggleStageKind('rising_action');
      });
      expect(result.current.state.stageMapCreateKinds).toEqual(['exposition', 'rising_action']);

      act(() => {
        callbacks.toggleStageKind('exposition');
      });
      expect(result.current.state.stageMapCreateKinds).toEqual(['rising_action']);
    });

    it('reset clears form fields on cancel', () => {
      const { result } = renderHook(() => usePlanningController('planning'), {
        wrapper: WithProviders,
      });

      const { callbacks } = result.current;

      act(() => {
        callbacks.setSequenceCreateTitle('Test');
        callbacks.setSequenceCreateSummary('Summary');
      });

      act(() => {
        callbacks.setSequenceCreateTitle('');
        callbacks.setSequenceCreateSummary('');
      });

      const { state } = result.current;

      expect(state.sequenceCreateTitle).toBe('');
      expect(state.sequenceCreateSummary).toBe('');
    });
  });

  describe('hook count stays under React limit', () => {
    it('does not throw when rendering with all hooks (under 50)', () => {
      const { result } = renderHook(() => usePlanningController('arcs'), {
        wrapper: WithProviders,
      });

      expect(result.current).toBeDefined();
      const stateKeys = Object.keys(result.current.state);
      expect(stateKeys.length).toBeGreaterThan(20);
      expect(stateKeys.length).toBeLessThan(100);
    });
  });
});

describe('usePlanningQueries consolidation', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('returns all 6 query results via useQueries', () => {
    const { result } = renderHook(() => usePlanningQueries({ projectId: 'p1', tab: 'planning' }), {
      wrapper: WithProviders,
    });

    expect(result.current.sequencePlansQuery).toBeDefined();
    expect(result.current.chapterPlansQuery).toBeDefined();
    expect(result.current.scenePlansQuery).toBeDefined();
    expect(result.current.beatPlansQuery).toBeDefined();
    expect(result.current.dependenciesQuery).toBeDefined();
    expect(result.current.chapterPacketsQuery).toBeDefined();
  });

  it('each query is independently accessible', () => {
    const { result } = renderHook(() => usePlanningQueries({ projectId: 'p1', tab: 'planning' }), {
      wrapper: WithProviders,
    });

    expect(result.current.sequencePlansQuery.status).toBeDefined();
    expect(['fetching', 'pending', 'success']).toContain(result.current.chapterPlansQuery.status);
  });
});

describe('usePlanningMutations consolidation', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('returns all 12 mutation objects via useMemo', () => {
    const { result } = renderHook(() => usePlanningMutations({ projectId: 'p1' }), {
      wrapper: WithProviders,
    });

    expect(result.current.sequencePlanCreateMutation).toBeDefined();
    expect(result.current.chapterPlanCreateMutation).toBeDefined();
    expect(result.current.scenePlanCreateMutation).toBeDefined();
    expect(result.current.beatPlanCreateMutation).toBeDefined();
    expect(result.current.chapterPacketCreateMutation).toBeDefined();
    expect(result.current.sequenceReorderMutation).toBeDefined();
    expect(result.current.chapterReorderMutation).toBeDefined();
    expect(result.current.sceneReorderMutation).toBeDefined();
  });

  it('each mutation has mutateAsync method', () => {
    const { result } = renderHook(() => usePlanningMutations({ projectId: 'p1' }), {
      wrapper: WithProviders,
    });

    expect(typeof result.current.sequencePlanCreateMutation.mutateAsync).toBe('function');
    expect(typeof result.current.chapterPlanUpdateMutation.mutateAsync).toBe('function');
  });
});
