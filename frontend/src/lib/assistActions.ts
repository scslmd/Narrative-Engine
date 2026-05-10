import type { ManuscriptAssistKind, TextRange } from '../types/manuscriptAssist';

export interface AssistAction {
  kind: ManuscriptAssistKind;
  label: string;
  description: string;
  instructionTemplate: (range: TextRange) => string;
}

export interface AssistGroup {
  label: string;
  actions: AssistAction[];
}

const SENSORY_ACTIONS: AssistAction[] = [
  {
    kind: 'expand_sensory_sight',
    label: 'Sight & color',
    description: 'Add visual detail, lighting, color, spatial awareness',
    instructionTemplate: () => 'Expand this passage with vivid visual detail. Focus on sight: lighting, color, shapes, movement, and spatial relationships.',
  },
  {
    kind: 'expand_sensory_sound',
    label: 'Sound & rhythm',
    description: 'Add auditory detail, ambient noise, silence, cadence',
    instructionTemplate: () => 'Expand this passage with auditory detail. Focus on sound: ambient noise, tones, silence, rhythm, and the cadence of speech.',
  },
  {
    kind: 'expand_sensory_smell',
    label: 'Smell & atmosphere',
    description: 'Add olfactory detail, scent memory, environmental mood',
    instructionTemplate: () => 'Expand this passage with olfactory detail. Focus on smell: scents, odors, and the atmospheric qualities that shape mood.',
  },
  {
    kind: 'expand_sensory_texture',
    label: 'Touch & texture',
    description: 'Add tactile detail, temperature, physical sensation',
    instructionTemplate: () => 'Expand this passage with tactile detail. Focus on touch: textures, temperature, weight, and physical sensations.',
  },
  {
    kind: 'expand_sensory_taste',
    label: 'Taste & flavor',
    description: 'Add gustatory detail, flavor memory, palate',
    instructionTemplate: () => 'Expand this passage with gustatory detail. Focus on taste: flavors, palate sensations, and the memories they evoke.',
  },
  {
    kind: 'expand_metaphor',
    label: 'Metaphor & simile',
    description: 'Add figurative language, comparisons, symbolic imagery',
    instructionTemplate: () => 'Expand this passage with figurative language. Add metaphors and similes that illuminate meaning without overwriting.',
  },
  {
    kind: 'expand_show_dont_tell',
    label: 'Show don\'t tell',
    description: 'Convert abstract statements into concrete action and observation',
    instructionTemplate: () => 'Rewrite this passage using show-don\'t-tell. Replace abstract statements with concrete actions, observations, and behavior.',
  },
];

const REWRITE_ACTIONS: AssistAction[] = [
  {
    kind: 'line_edit_selection',
    label: 'Tighten & polish',
    description: 'Remove redundancy, improve flow and clarity',
    instructionTemplate: () => 'Tighten and polish this selected passage.',
  },
  {
    kind: 'compress_selection',
    label: 'Compress',
    description: 'Reduce word count while preserving meaning',
    instructionTemplate: () => 'Condense this passage to roughly half its length while preserving the core meaning, tone, and character voice.',
  },
  {
    kind: 'rewrite_selection_same_voice',
    label: 'Rewrite in different voice',
    description: 'Match a specified tone or style',
    instructionTemplate: () => 'Rewrite this passage with fresh phrasing while maintaining the same character voice and narrative tone.',
  },
  {
    kind: 'alternate_selection',
    label: 'Alternate version',
    description: 'Generate a different take on the same idea',
    instructionTemplate: () => 'Produce an alternate version of this passage that conveys the same narrative beat but approaches it from a different angle.',
  },
];

const CONTINUE_ACTIONS: AssistAction[] = [
  {
    kind: 'continue_from_selection',
    label: 'Continue from here',
    description: 'Generate next passage in current voice',
    instructionTemplate: (range) => `Continue the narrative from this point. Maintain the established character voice, tone, and pacing.\n\nContext: ${range.anchor_after.slice(0, 120)}`,
  },
  {
    kind: 'fork_from_selection',
    label: 'Fork as draft',
    description: 'Create a new branch or alternate version',
    instructionTemplate: () => 'Fork a new variant from this selected passage.',
  },
];

export const ASSIST_CATEGORIES: AssistGroup[] = [
  {
    label: 'Rewrite',
    actions: [...REWRITE_ACTIONS, ...SENSORY_ACTIONS],
  },
  {
    label: 'Continue',
    actions: CONTINUE_ACTIONS,
  },
];

// Flatten for backward compatibility
export const ASSIST_ACTIONS: AssistAction[] = ASSIST_CATEGORIES.flatMap((c) => c.actions);

export { REWRITE_ACTIONS, SENSORY_ACTIONS, CONTINUE_ACTIONS };

export function getActionByKind(kind: ManuscriptAssistKind): AssistAction | undefined {
  return ASSIST_ACTIONS.find((action) => action.kind === kind);
}

export function groupActionsByCategory(): Record<string, AssistAction[]> {
  const groups: Record<string, AssistAction[]> = {};
  for (const category of ASSIST_CATEGORIES) {
    groups[category.label] = category.actions;
  }
  return groups;
}

export function buildAssistInstruction(action: AssistAction, range: TextRange): string {
  return action.instructionTemplate(range);
}
