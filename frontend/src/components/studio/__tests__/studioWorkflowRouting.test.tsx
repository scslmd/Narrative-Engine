import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { StudioPanelKey } from '../../../stores/studioStore';
import { railSections, StudioProjectRail } from '../StudioProjectRail';

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
    expect(labels).toContain('Research');
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

  it('research is in Research stage', () => {
    const research = railSections.find((section: { label: string }) => section.label === 'Research');
    expect(research).toBeDefined();
    expect(research!.items.some((item: { panel: StudioPanelKey }) => item.panel === 'research')).toBe(true);
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

describe('StudioProjectRail compact mode', () => {
  it('renders panel buttons in compact mode', () => {
    vi.mock('../../../stores/studioStore', async (importOriginal) => {
      const actual = await importOriginal<typeof import('../../../stores/studioStore')>();
      return {
        ...actual,
        useStudioStore: vi.fn((selector: Function) => {
          const state = {
            activePanel: null,
            visitedStages: new Set<number>(),
            collapsedSections: {},
            openPanel: vi.fn(),
            toggleSection: vi.fn(),
          };
          return selector(state);
        }),
      };
    });

    vi.mock('../../../hooks/useEntityCounts', () => ({
      useEntityCounts: vi.fn(() => ({})),
      getPanelCount: vi.fn(() => 0),
    }));

    vi.mock('../../../assets/icons/rail', () => {
      const MockIcon = vi.fn(() => null);
      const icons: Record<string, typeof MockIcon> = {};
      const keys = ['ideas', 'notes', 'characters', 'worldBible', 'relationships', 'arcs', 'structure', 'chapters', 'research', 'manuscripts', 'drafts', 'generation', 'revision', 'suggestions', 'review', 'inspect', 'polish', 'canon', 'jobs'];
      for (const key of keys) {
        icons[key] = MockIcon;
      }
      return { railIcons: icons };
    });

    render(<StudioProjectRail projectId="test-project" compact={true} />);

    expect(screen.getByLabelText('Ideas')).toBeTruthy();
    expect(screen.getByLabelText('Characters')).toBeTruthy();
    expect(screen.getByLabelText('Polish')).toBeTruthy();
  });
});
