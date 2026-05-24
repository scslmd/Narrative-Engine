import { describe, expect, it } from 'vitest';
import { StudioPanelKey } from '../../../stores/studioStore';
import { railSections } from '../StudioProjectRail';

describe('Studio Workflow Routing', () => {
  const allKeys: StudioPanelKey[] = [
    'suggestions',
    'ideas',
    'drafts',
    'manuscripts',
    'characters',
    'worldBible',
    'relationships',
    'arcs',
    'structure',
    'chapters',
    'canon',
    'generation',
    'review',
    'inspect',
    'notes',
    'jobs',
    'research',
    'revision',
    'polish',
  ];

  it('has exactly 19 panel keys', () => {
    expect(allKeys.length).toBe(19);
  });

  it('includes research, revision, and polish keys', () => {
    expect(allKeys).toContain('research');
    expect(allKeys).toContain('revision');
    expect(allKeys).toContain('polish');
  });

  it('rail sections have correct stage labels', () => {
    const labels = railSections.map((s: { label: string }) => s.label);
    expect(labels).toContain('Ideation');
    expect(labels).toContain('Planning');
    expect(labels).toContain('Drafting');
    expect(labels).toContain('Revision');
    expect(labels).toContain('Polish');
  });

  it('rail items map to valid panel keys', () => {
    const panels = railSections.flatMap((section: { items: { panel: StudioPanelKey }[] }) => section.items.map((item: { panel: StudioPanelKey }) => item.panel));
    for (const panel of panels) {
      expect(allKeys).toContain(panel);
    }
  });

  it('research is in Ideation stage', () => {
    const ideation = railSections.find((section: { label: string }) => section.label === 'Ideation');
    expect(ideation).toBeDefined();
    expect(ideation!.items.some((item: { panel: StudioPanelKey }) => item.panel === 'research')).toBe(true);
  });

  it('revision is in Revision stage', () => {
    const revision = railSections.find((section: { label: string }) => section.label === 'Revision');
    expect(revision).toBeDefined();
    expect(revision!.items.some((item: { panel: StudioPanelKey }) => item.panel === 'revision')).toBe(true);
  });

  it('polish is in Polish stage', () => {
    const polish = railSections.find((section: { label: string }) => section.label === 'Polish');
    expect(polish).toBeDefined();
    expect(polish!.items.some((item: { panel: StudioPanelKey }) => item.panel === 'polish')).toBe(true);
  });

  it('all rail items have non-empty labels', () => {
    for (const section of railSections) {
      for (const item of section.items) {
        expect(item.label.length).toBeGreaterThan(0);
      }
    }
  });

  it('no duplicate panel keys in rail', () => {
    const panels = railSections.flatMap((section: { items: { panel: StudioPanelKey }[] }) => section.items.map((item: { panel: StudioPanelKey }) => item.panel));
    expect(panels.length).toBe(new Set(panels).size);
  });
});
