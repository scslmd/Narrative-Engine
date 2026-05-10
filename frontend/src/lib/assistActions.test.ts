import { describe, expect, it } from 'vitest';
import type { TextRange } from '../types/manuscriptAssist';
import {
  ASSIST_ACTIONS,
  ASSIST_CATEGORIES,
  buildAssistInstruction,
  getActionByKind,
  groupActionsByCategory,
} from './assistActions';

const sampleRange: TextRange = {
  start_offset: 0,
  end_offset: 10,
  selected_text: 'Hello world',
  anchor_before: '',
  anchor_after: ' This is the rest of the passage that continues onward.',
};

describe('assistActions config', () => {
  it('defines all required fields for each action', () => {
    for (const action of ASSIST_ACTIONS) {
      expect(action.kind).toBeDefined();
      expect(action.label).toBeTruthy();
      expect(action.description).toBeTruthy();
      expect(typeof action.instructionTemplate).toBe('function');
    }
  });

  it('includes rewrite actions for selection editing', () => {
    const kinds = ASSIST_ACTIONS.map((a) => a.kind);
    expect(kinds).toContain('line_edit_selection');
    expect(kinds).toContain('expand_sensory_sight');
    expect(kinds).toContain('expand_sensory_sound');
    expect(kinds).toContain('expand_sensory_smell');
    expect(kinds).toContain('expand_sensory_texture');
    expect(kinds).toContain('expand_sensory_taste');
    expect(kinds).toContain('expand_metaphor');
    expect(kinds).toContain('expand_show_dont_tell');
    expect(kinds).toContain('compress_selection');
    expect(kinds).toContain('rewrite_selection_same_voice');
    expect(kinds).toContain('alternate_selection');
  });

  it('includes continue actions for extending text', () => {
    const kinds = ASSIST_ACTIONS.map((a) => a.kind);
    expect(kinds).toContain('continue_from_selection');
    expect(kinds).toContain('fork_from_selection');
  });

  it('instruction templates produce non-empty strings', () => {
    for (const action of ASSIST_ACTIONS) {
      const instruction = action.instructionTemplate(sampleRange);
      expect(instruction.length).toBeGreaterThan(0);
    }
  });

  it('getActionByKind finds matching action', () => {
    const action = getActionByKind('line_edit_selection');
    expect(action).toBeDefined();
    expect(action?.kind).toBe('line_edit_selection');
  });

  it('getActionByKind returns undefined for unknown kind', () => {
    const action = getActionByKind('canon_check');
    expect(action).toBeUndefined();
  });

  it('groupActionsByCategory groups actions correctly', () => {
    const groups = groupActionsByCategory();
    expect(Object.keys(groups).length).toBe(ASSIST_CATEGORIES.length);
    for (const category of ASSIST_CATEGORIES) {
      expect(groups[category.label]).toBeDefined();
      expect(groups[category.label].length).toBe(category.actions.length);
    }
  });

  it('buildAssistInstruction delegates to action template', () => {
    const action = getActionByKind('line_edit_selection')!;
    const instruction = buildAssistInstruction(action, sampleRange);
    expect(instruction).toBeTruthy();
    expect(instruction.length).toBeGreaterThan(0);
  });

  it('continue_from_selection instruction includes context', () => {
    const action = getActionByKind('continue_from_selection')!;
    const instruction = buildAssistInstruction(action, sampleRange);
    expect(instruction).toContain('Continue');
    expect(instruction).toContain(sampleRange.anchor_after.slice(0, 50));
  });

  it('all actions have unique kinds', () => {
    const kinds = ASSIST_ACTIONS.map((a) => a.kind);
    const uniqueKinds = new Set(kinds);
    expect(kinds.length).toBe(uniqueKinds.size);
  });
});
