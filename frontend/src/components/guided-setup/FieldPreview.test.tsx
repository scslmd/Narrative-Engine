import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, within } from '../../__tests__/test-utils';
import { FieldPreview } from './FieldPreview';
import { useGuidedSetupStore } from '../../stores/guidedSetupStore';
import type { CategoryProgress } from '../../services/guidedSetup';

const baseProgress: CategoryProgress[] = [
  { category: 'config', completeness: 1, confidence: 0.9, fields_collected: ['project_name', 'genre'], fields_missing: [] },
  { category: 'foundation', completeness: 0.5, confidence: 0.7, fields_collected: ['premise_text'], fields_missing: ['logline', 'thematic_spine'] },
  { category: 'characters', completeness: 0.2, confidence: 0.5, fields_collected: [], fields_missing: ['name', 'role'] },
  { category: 'world_bible', completeness: 0, confidence: 0.3, fields_collected: [], fields_missing: ['entry_type', 'title'] },
  { category: 'arcs', completeness: 0.8, confidence: 0.95, fields_collected: ['character_name'], fields_missing: [] },
];

beforeEach(() => {
  useGuidedSetupStore.getState().reset();
});

describe('FieldPreview completeness bars', () => {
  it('renders green completeness bar when completeness >= 0.7', () => {
    render(<FieldPreview categoryProgress={baseProgress} />);

    const arcsBar = screen.getByRole('button', { name: /Arcs/ });
    expect(arcsBar).toBeInTheDocument();
    const arcFill = within(arcsBar).getByRole('progressbar', { name: /Arcs.*80% complete/ });
    expect(arcFill).toBeInTheDocument();
    expect(arcFill.classList.contains('bg-emerald-500')).toBe(true);
  });

  it('renders amber completeness bar when completeness between 0.3 and 0.7', () => {
    render(<FieldPreview categoryProgress={baseProgress} />);

    const foundationBar = screen.getByRole('button', { name: /Foundation/ });
    expect(foundationBar).toBeInTheDocument();
    const foundationFill = within(foundationBar).getByRole('progressbar', { name: /Foundation.*50% complete/ });
    expect(foundationFill).toBeInTheDocument();
    expect(foundationFill.classList.contains('bg-amber-500')).toBe(true);
  });

  it('renders gray completeness bar when completeness < 0.3', () => {
    render(<FieldPreview categoryProgress={baseProgress} />);

    const charsBar = screen.getByRole('button', { name: /Characters/ });
    expect(charsBar).toBeInTheDocument();
    const charFill = within(charsBar).getByRole('progressbar', { name: /Characters.*20% complete/ });
    expect(charFill).toBeInTheDocument();
    expect(charFill.classList.contains('bg-gray-400')).toBe(true);
  });

  it('renders no completeness bars when categoryProgress is not provided', () => {
    render(<FieldPreview />);

    const configBar = screen.getByRole('button', { name: /Project Config/ });
    expect(() => within(configBar).getByRole('progressbar')).toThrow();
  });

  it('renders missing field tags when fields_missing is non-empty', () => {
    render(<FieldPreview categoryProgress={baseProgress} />);

    expect(screen.getByText('logline')).toBeInTheDocument();
    expect(screen.getByText('thematic_spine')).toBeInTheDocument();
    expect(screen.getByText('name')).toBeInTheDocument();
    expect(screen.getByText('role')).toBeInTheDocument();
    expect(screen.getByText('entry_type')).toBeInTheDocument();
    expect(screen.getByText('title')).toBeInTheDocument();
  });

  it('renders no missing field tags when categoryProgress is not provided', () => {
    render(<FieldPreview />);

    expect(screen.queryByText('logline')).not.toBeInTheDocument();
    expect(screen.queryByText('thematic_spine')).not.toBeInTheDocument();
  });

  it('does not render missing field tags for categories with empty fields_missing', () => {
    const progress: CategoryProgress[] = [
      { category: 'config', completeness: 1, confidence: 1, fields_collected: ['project_name'], fields_missing: [] },
      { category: 'foundation', completeness: 1, confidence: 1, fields_collected: ['premise_text'], fields_missing: [] },
    ];

    render(<FieldPreview categoryProgress={progress} />);

    const tags = document.querySelectorAll('[data-testid="missing-field-tag"]');
    expect(tags.length).toBe(0);
  });

  it('renders completeness bar for config section at 100%', () => {
    render(<FieldPreview categoryProgress={baseProgress} />);

    const configBar = screen.getByRole('button', { name: /Project Config/ });
    const configFill = within(configBar).getByRole('progressbar', { name: /Project Config.*100% complete/ });
    expect(configFill).toBeInTheDocument();
    expect(configFill.classList.contains('bg-emerald-500')).toBe(true);
  });

  it('renders completeness bar for world_bible section at 0%', () => {
    render(<FieldPreview categoryProgress={baseProgress} />);

    const worldBar = screen.getByRole('button', { name: /World/ });
    const worldFill = within(worldBar).getByRole('progressbar', { name: /World.*0% complete/ });
    expect(worldFill).toBeInTheDocument();
    expect(worldFill.classList.contains('bg-gray-400')).toBe(true);
  });
});
