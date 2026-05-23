import { describe, test } from 'vitest';

describe('planning slice modules', () => {
  test('slice hooks are importable', async () => {
    await import('./usePlanningRetries');
    await import('./useSequencePlanning');
    await import('./useChapterPlanning');
    await import('./useScenePlanning');
    await import('./useBeatPlanning');
    await import('./useChapterPackets');
    await import('./useStoryboardPlanning');
    await import('./useArcPlanning');
  });

  test('form hooks are importable', async () => {
    await import('./forms/useSequenceForm');
    await import('./forms/useChapterForm');
    await import('./forms/useSceneForm');
    await import('./forms/useBeatForm');
    await import('./forms/usePacketForm');
    await import('./forms/useStoryboardForm');
    await import('./forms/useArcCandidateForm');
    await import('./forms/useStageMapForm');
  });
});
