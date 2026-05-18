import { Link } from 'react-router-dom';
import {
  BookOpen,
  Brain,
  FileStack,
  FileText,
  Network,
  NotebookPen,
  Scroll,
  Users,
} from 'lucide-react';
import { useStudioStore, type StudioPanelKey } from '../../stores/studioStore';

interface RailItem {
  label: string;
  panel: StudioPanelKey;
  icon: typeof Brain;
}

interface RailSection {
  label: string;
  items: RailItem[];
}

const railSections: RailSection[] = [
  {
    label: 'Develop',
    items: [
      { label: 'Drafts', panel: 'drafts', icon: FileText },
      { label: 'Manuscripts', panel: 'manuscripts', icon: BookOpen },
      { label: 'Ideas', panel: 'ideas', icon: Brain },
      { label: 'Suggestions', panel: 'suggestions', icon: NotebookPen },
      { label: 'Review', panel: 'review', icon: FileStack },
    ],
  },
  {
    label: 'Reference',
    items: [
      { label: 'Characters', panel: 'characters', icon: Users },
      { label: 'World Bible', panel: 'worldBible', icon: BookOpen },
      { label: 'Relationships', panel: 'relationships', icon: Network },
      { label: 'Canon', panel: 'generation', icon: Scroll },
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
  item: RailItem;
  onClick: () => void;
}

function RailButton({ active, compact, item, onClick }: RailButtonProps) {
  const Icon = item.icon;

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={item.label}
      aria-pressed={active}
      title={item.label}
      className={`flex w-full items-center rounded-xl text-left text-xs font-medium transition-colors ${
        compact ? 'flex-col gap-1 justify-center px-0 py-3' : 'gap-2.5 px-3 py-2.5'
      } ${
        active
          ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-sm ring-1 ring-[var(--border-primary)]'
          : 'text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]'
      }`}
    >
      <Icon className={compact ? 'h-7 w-7 shrink-0' : 'h-3.5 w-3.5 shrink-0'} />
      {compact ? <span className="text-[9px] font-medium leading-tight text-center truncate w-full">{item.label}</span> : <span className="truncate">{item.label}</span>}
    </button>
  );
}

export function StudioProjectRail({ projectId, compact = false }: StudioProjectRailProps) {
  const activePanel = useStudioStore((state) => state.activePanel);
  const openPanel = useStudioStore((state) => state.openPanel);

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

      <nav className={`flex-1 overflow-y-auto ${compact ? 'px-2 py-3' : 'px-3 py-4'}`} aria-label="Studio project map">
        <div className="space-y-4">
          {railSections.map((section) => (
            <section key={section.label} className="space-y-2">
              {!compact ? (
                <p className="px-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--text-tertiary)]">
                  {section.label}
                </p>
              ) : null}
              <div className={`space-y-1.5 ${compact ? '' : 'rounded-2xl bg-[var(--bg-primary)]/40 p-1.5'}`}>
                {section.items.map((item) => (
                  <RailButton
                    key={item.panel}
                    active={activePanel === item.panel}
                    compact={compact}
                    item={item}
                    onClick={() => openPanel(item.panel)}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      </nav>

      {!compact ? (
        <div className="space-y-1 border-t border-[var(--border-primary)] px-3 py-3 text-[11px] text-[var(--text-tertiary)]">
          <Link
            className="block rounded-lg px-3 py-2 transition-colors hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]"
            to={`/workspace/${projectId}/plan`}
          >
            Open full Planning
          </Link>
          <Link
            className="block rounded-lg px-3 py-2 transition-colors hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]"
            to={`/workspace/${projectId}/canon`}
          >
            Open full Canon
          </Link>
        </div>
      ) : null}
    </aside>
  );
}
