import { useRef } from 'react';
import { Link } from 'react-router-dom';
import { useEntityCounts, getPanelCount } from '../../hooks/useEntityCounts';
import { useStudioStore, type StudioPanelKey } from '../../stores/studioStore';
import { railIcons } from '../../assets/icons/rail';
import type { RailIconComponent } from '../../assets/icons/rail';

interface RailItem {
  label: string;
  panel: StudioPanelKey;
  icon: RailIconComponent;
}

interface RailSection {
  label: string;
  items: RailItem[];
}

const STAGE_COLORS: readonly string[] = [
  '#3b82f6',
  '#8b5cf6',
  '#06b6d4',
  '#22c55e',
  '#f59e0b',
  '#ec4899',
];

export const railSections: RailSection[] = [
  {
    label: 'Ideation',
    items: [
      { label: 'Ideas', panel: 'ideas', icon: railIcons.ideas },
      { label: 'Notes', panel: 'notes', icon: railIcons.notes },
    ],
  },
  {
    label: 'Planning',
    items: [
      { label: 'Characters', panel: 'characters', icon: railIcons.characters },
      { label: 'World Bible', panel: 'worldBible', icon: railIcons.worldBible },
      { label: 'Relationships', panel: 'relationships', icon: railIcons.relationships },
      { label: 'Arcs', panel: 'arcs', icon: railIcons.arcs },
      { label: 'Structure', panel: 'structure', icon: railIcons.structure },
      { label: 'Chapters', panel: 'chapters', icon: railIcons.chapters },
    ],
  },
  {
    label: 'Research',
    items: [
      { label: 'Research', panel: 'research', icon: railIcons.research },
    ],
  },
  {
    label: 'Drafting',
    items: [
      { label: 'Manuscripts', panel: 'manuscripts', icon: railIcons.manuscripts },
      { label: 'Drafts', panel: 'drafts', icon: railIcons.drafts },
      { label: 'Generation', panel: 'generation', icon: railIcons.generation },
    ],
  },
  {
    label: 'Revision',
    items: [
      { label: 'Revision', panel: 'revision', icon: railIcons.revision },
      { label: 'Suggestions', panel: 'suggestions', icon: railIcons.suggestions },
      { label: 'Review', panel: 'review', icon: railIcons.review },
      { label: 'Inspect', panel: 'inspect', icon: railIcons.inspect },
    ],
  },
  {
    label: 'Polish',
    items: [
      { label: 'Polish', panel: 'polish', icon: railIcons.polish },
      { label: 'Canon', panel: 'canon', icon: railIcons.canon },
      { label: 'Jobs', panel: 'jobs', icon: railIcons.jobs },
    ],
  },
];

interface StudioProjectRailProps {
  projectId: string;
  compact?: boolean;
}

interface RailButtonProps {
  active: boolean;
  compact: boolean;
  count: number | null;
  item: RailItem;
  stageIndex: number;
  onClick: () => void;
}

function RailButton({ active, compact, count, item, stageIndex, onClick }: RailButtonProps) {
  const Icon = item.icon;
  const stageColor = STAGE_COLORS[stageIndex] || STAGE_COLORS[0];

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={item.label}
      aria-pressed={active}
      title={item.label}
      className={`relative flex w-full items-center rounded-xl text-left text-xs font-medium transition-colors ${
        compact ? 'flex-col gap-1 justify-center px-0 py-3' : 'gap-2.5 px-3 py-2.5'
      } ${
        active
          ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-sm ring-1 ring-[var(--border-primary)]'
          : 'text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]'
      }`}
      style={active ? { ['--stage-color' as string]: stageColor } : undefined}
    >
      {active && !compact && (
        <span
          className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-r-full"
          style={{ backgroundColor: stageColor }}
        />
      )}
      <Icon className={compact ? 'h-7 w-7 shrink-0' : 'h-3.5 w-3.5 shrink-0'} />
      {compact ? (
        <span className="text-[9px] font-medium leading-tight text-center truncate w-full">
          {item.label}
        </span>
      ) : (
        <span className="flex-1 truncate">{item.label}</span>
      )}
      {!compact && count !== null && count > 0 && (
        <span className="shrink-0 rounded-full bg-white/5 px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-muted)]">
          {count}
        </span>
      )}
    </button>
  );
}

function findStageIndex(panel: StudioPanelKey): number {
  for (let i = 0; i < railSections.length; i++) {
    if (railSections[i].items.some((item) => item.panel === panel)) {
      return i;
    }
  }
  return -1;
}

interface WorkflowProgressProps {
  activePanel: StudioPanelKey | null;
  compact?: boolean;
  visitedStages: Set<number>;
  onDotClick: (index: number) => void;
}

function StudioWorkflowProgress({ activePanel, compact, visitedStages, onDotClick }: WorkflowProgressProps) {
  if (compact) return null;

  const currentStageIndex = activePanel ? findStageIndex(activePanel) : -1;
  const stageLabel = currentStageIndex >= 0
    ? railSections[currentStageIndex].label
    : '';

  return (
    <div className="border-b border-[var(--border-primary)] px-4 py-3">
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--text-tertiary)]">
        Writing Progress
      </p>
      <div className="mt-2 flex items-center gap-0.5">
        {STAGE_COLORS.map((color, i) => (
          <div key={i} className="flex items-center">
            <button
              type="button"
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold transition-all hover:scale-110"
              style={{
                borderColor: i === currentStageIndex ? color : visitedStages.has(i) ? '#22c55e' : 'var(--border-primary)',
                backgroundColor: i === currentStageIndex ? `${color}33` : visitedStages.has(i) ? '#22c55e22' : 'transparent',
                color: i === currentStageIndex ? color : visitedStages.has(i) ? '#22c55e' : 'var(--text-tertiary)',
                boxShadow: i === currentStageIndex ? `0 0 12px ${color}44` : 'none',
              }}
              onClick={() => onDotClick(i)}
              aria-label={`Scroll to stage ${i + 1}`}
            >
              {visitedStages.has(i) ? '\u2713' : i + 1}
            </button>
            {i < STAGE_COLORS.length - 1 && (
              <div
                className="h-[2px] w-3"
                style={{
                  backgroundColor: visitedStages.has(i)
                    ? '#22c55e'
                    : 'var(--border-primary)',
                }}
              />
            )}
          </div>
        ))}
      </div>
      <p className="mt-2 text-[11px] text-[var(--text-tertiary)]">
        Stage {currentStageIndex + 1} of 6 — {stageLabel || 'Select a panel'}
      </p>
    </div>
  );
}

interface SectionHeaderProps {
  label: string;
  sectionIndex: number;
  isCollapsed: boolean;
  onToggle: () => void;
}

function SectionHeader({ label, sectionIndex, isCollapsed, onToggle }: SectionHeaderProps) {
  const stageColor = STAGE_COLORS[sectionIndex] || STAGE_COLORS[0];

  return (
    <button
      type="button"
      onClick={onToggle}
      className="flex w-full items-center gap-1 px-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--text-tertiary)] transition-colors hover:text-[var(--text-secondary)]"
      aria-expanded={!isCollapsed}
    >
      <span
        className="h-1 w-1.5 shrink-0 rounded-full transition-transform"
        style={{
          backgroundColor: stageColor,
          transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)',
        }}
      />
      {label}
    </button>
  );
}

export function StudioProjectRail({ projectId, compact = false }: StudioProjectRailProps) {
  const activePanel = useStudioStore((state) => state.activePanel);
  const openPanel = useStudioStore((state) => state.openPanel);
  const visitedStages = useStudioStore((state) => state.visitedStages);
  const collapsedSections = useStudioStore((state) => state.collapsedSections);
  const toggleSection = useStudioStore((state) => state.toggleSection);
  const counts = useEntityCounts(projectId);
  const sectionRefs = useRef<(HTMLElement | null)[]>([]);

  const scrollToSection = (index: number) => {
    const el = sectionRefs.current[index];
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  };

  return (
    <aside
      className={`flex h-full flex-col border-r border-[var(--border-primary)] bg-[var(--bg-secondary)] ${
        compact ? 'w-20' : ''
      }`}
    >
      {!compact ? (
        <div className="border-b border-[var(--border-primary)] px-4 py-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--text-tertiary)]">
            Project Map
          </p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">
            Keep drafting in the center. Open context only when needed.
          </p>
        </div>
      ) : null}

      <StudioWorkflowProgress
        activePanel={activePanel}
        compact={compact}
        visitedStages={visitedStages}
        onDotClick={scrollToSection}
      />

      <nav className={`flex-1 overflow-y-auto ${compact ? 'px-2 py-3' : 'px-3 py-4'}`} aria-label="Studio project map">
        <div className="space-y-4">
          {railSections.map((section, sectionIndex) => {
            const isCollapsed = collapsedSections[sectionIndex];
            return (
              <section
                key={section.label}
                ref={(el) => { sectionRefs.current[sectionIndex] = el; }}
                className="space-y-2"
              >
                {!compact && (
                  <SectionHeader
                    label={section.label}
                    sectionIndex={sectionIndex}
                    isCollapsed={isCollapsed}
                    onToggle={() => toggleSection(sectionIndex)}
                  />
                )}
                {!(compact || isCollapsed) && (
                  <div className="rounded-2xl bg-[var(--bg-primary)]/40 p-1.5 space-y-1.5">
                    {section.items.map((item) => (
                      <RailButton
                        key={item.panel}
                        active={activePanel === item.panel}
                        compact={compact}
                        count={getPanelCount(item.panel, counts)}
                        item={item}
                        stageIndex={sectionIndex}
                        onClick={() => openPanel(item.panel)}
                      />
                    ))}
                  </div>
                )}
                {compact && (
                  <div className="space-y-1.5">
                    {section.items.map((item) => (
                      <RailButton
                        key={item.panel}
                        active={activePanel === item.panel}
                        compact={compact}
                        count={getPanelCount(item.panel, counts)}
                        item={item}
                        stageIndex={sectionIndex}
                        onClick={() => openPanel(item.panel)}
                      />
                    ))}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      </nav>

      {!compact ? (
        <div className="space-y-1 border-t border-[var(--border-primary)] px-3 py-3">
          <Link
            className="block rounded-lg px-3 py-2 text-[11px] text-[var(--text-tertiary)] transition-colors hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]"
            to={`/workspace/${projectId}/studio?tab=structure`}
          >
            Open Planning Panel
          </Link>
          <Link
            className="block rounded-lg px-3 py-2 text-[11px] text-[var(--text-tertiary)] transition-colors hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]"
            to={`/workspace/${projectId}/studio?tab=canon`}
          >
            Open Canon Panel
          </Link>
        </div>
      ) : null}
    </aside>
  );
}
