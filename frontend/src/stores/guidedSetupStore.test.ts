import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { act } from '@testing-library/react';
import { useGuidedSetupStore } from './guidedSetupStore';
import * as guidedSetup from '../services/guidedSetup';

describe('guidedSetupStore', () => {
  beforeEach(() => {
    useGuidedSetupStore.getState().reset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('starts with readyToCreate false', () => {
    const state = useGuidedSetupStore.getState();
    expect(state.readyToCreate).toBe(false);
  });

  it('sets readyToCreate when LLM returns true', async () => {
    const mockResponse = {
      extracted_fields: guidedSetup.emptyExtractedFields(),
      next_question: 'Any more details?',
      confidence: 0.9,
      progress: 85,
      ready_to_create: true,
      category_progress: [],
    };

    vi.spyOn(guidedSetup, 'analyzeTurn').mockResolvedValue(mockResponse);

    await act(async () => {
      await useGuidedSetupStore.getState().handleAnalyze('test answer');
    });

    const state = useGuidedSetupStore.getState();
    expect(state.readyToCreate).toBe(true);
  });

  it('injects readiness notification when ready flips from false to true', async () => {
    const mockResponse = {
      extracted_fields: guidedSetup.emptyExtractedFields(),
      next_question: 'Any more details?',
      confidence: 0.9,
      progress: 85,
      ready_to_create: true,
      category_progress: [],
    };

    vi.spyOn(guidedSetup, 'analyzeTurn').mockResolvedValue(mockResponse);

    await act(async () => {
      await useGuidedSetupStore.getState().handleAnalyze('first answer');
    });

    const state = useGuidedSetupStore.getState();
    const systemMessages = state.conversationHistory.filter(m => m.role === 'system');
    const readinessMessage = systemMessages.find(m =>
      m.content.includes('enough to create') || m.content.includes('ready')
    );
    expect(readinessMessage).toBeDefined();
  });

  it('does not re-inject notification when already ready', async () => {
    const mockResponse = {
      extracted_fields: guidedSetup.emptyExtractedFields(),
      next_question: 'Any more details?',
      confidence: 0.9,
      progress: 90,
      ready_to_create: true,
      category_progress: [],
    };

    vi.spyOn(guidedSetup, 'analyzeTurn').mockResolvedValue(mockResponse);

    await act(async () => {
      await useGuidedSetupStore.getState().handleAnalyze('first answer');
    });

    const notificationsAfterFirst = useGuidedSetupStore.getState()
      .conversationHistory.filter(m =>
        m.role === 'system' && (m.content.includes('enough to create') || m.content.includes('ready'))
      ).length;

    await act(async () => {
      await useGuidedSetupStore.getState().handleAnalyze('second answer');
    });

    const notificationsAfterSecond = useGuidedSetupStore.getState()
      .conversationHistory.filter(m =>
        m.role === 'system' && (m.content.includes('enough to create') || m.content.includes('ready'))
      ).length;

    expect(notificationsAfterSecond).toBe(notificationsAfterFirst);
  });

  it('reset clears readyToCreate', () => {
    act(() => {
      useGuidedSetupStore.getState().setProgress(80, 0.9, true, []);
    });
    useGuidedSetupStore.getState().reset();
    const state = useGuidedSetupStore.getState();
    expect(state.readyToCreate).toBe(false);
  });
});
