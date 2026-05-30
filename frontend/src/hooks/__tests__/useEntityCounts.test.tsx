import { describe, expect, it } from 'vitest';
import { getPanelCount } from '../useEntityCounts';
import type { EntityCounts } from '../useEntityCounts';

describe('getPanelCount', () => {
  it('returns count for supported panels', () => {
    const counts: EntityCounts = {
      ideas: 5,
      characters: 3,
      worldBible: 2,
      relationships: 1,
      arcs: 4,
      structure: 0,
      chapters: 6,
      manuscripts: 1,
      drafts: 2,
      generation: null,
      revision: 1,
      suggestions: 3,
      review: null,
      inspect: null,
      canon: null,
      jobs: 7,
      research: 2,
      notes: null,
      polish: null,
    };

    expect(getPanelCount('ideas', counts)).toBe(5);
    expect(getPanelCount('characters', counts)).toBe(3);
    expect(getPanelCount('research', counts)).toBe(2);
  });

  it('returns null for unsupported panels', () => {
    const counts: EntityCounts = {
      ideas: 0,
      characters: 0,
      worldBible: 0,
      relationships: 0,
      arcs: 0,
      structure: 0,
      chapters: 0,
      manuscripts: 0,
      drafts: 0,
      generation: null,
      revision: 0,
      suggestions: 0,
      review: null,
      inspect: null,
      canon: null,
      jobs: 0,
      research: 0,
      notes: null,
      polish: null,
    };

    expect(getPanelCount('notes', counts)).toBeNull();
    expect(getPanelCount('generation', counts)).toBeNull();
    expect(getPanelCount('review', counts)).toBeNull();
    expect(getPanelCount('inspect', counts)).toBeNull();
    expect(getPanelCount('canon', counts)).toBeNull();
    expect(getPanelCount('polish', counts)).toBeNull();
  });

  it('returns zero for supported panels with no data', () => {
    const counts: EntityCounts = {
      ideas: 0,
      characters: 0,
      worldBible: 0,
      relationships: 0,
      arcs: 0,
      structure: 0,
      chapters: 0,
      manuscripts: 0,
      drafts: 0,
      generation: null,
      revision: 0,
      suggestions: 0,
      review: null,
      inspect: null,
      canon: null,
      jobs: 0,
      research: 0,
      notes: null,
      polish: null,
    };

    expect(getPanelCount('ideas', counts)).toBe(0);
    expect(getPanelCount('structure', counts)).toBe(0);
  });
});
