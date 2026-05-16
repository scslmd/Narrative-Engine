import { Link } from 'react-router-dom';
import { BookOpen, Brain, GitBranch, Network, Scroll, StickyNote, Users } from 'lucide-react';
import { useStudioStore, type StudioPanelKey } from '../../stores/studioStore';

const railItems: Array<{ label: string; panel: StudioPanelKey; icon: typeof Brain }> = [
  { label: 'Ideas', panel: 'ideas', icon: Brain },
  { label: 'Characters', panel: 'characters', icon: Users },
  { label: 'World Bible', panel: 'worldBible', icon: BookOpen },
  { label: 'Relationships', panel: 'relationships', icon: Network },
  { label: 'Canon', panel: 'generation', icon: Scroll },
  { label: 'Jobs', panel: 'jobs', icon: GitBranch },
  { label: 'Notes', panel: 'notes', icon: StickyNote },
];

interface StudioProjectRailProps {
  projectId: string;
}

export function StudioProjectRail({ projectId }: StudioProjectRailProps) {
  const activePanel = useStudioStore((state) => state.activePanel);
  const openPanel = useStudioStore((state) => state.openPanel);

  return (
    <aside className="flex h-full flex-col border-r border-[var(--border-primary)] bg-[var(--bg-secondary)]">
      <div className="border-b border-[var(--border-primary)] px-3 py-2">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-tertiary)]">Project Map</p>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-2" aria-label="Studio project map">
        {railItems.map((item) => {
          const Icon = item.icon;
          const active = activePanel === item.panel;
          return (
            <button
              key={item.panel}
              type="button"
              onClick={() => openPanel(item.panel)}
              aria-pressed={active}
              className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs font-medium transition-colors ${
                active
                  ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-sm'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {item.label}
            </button>
          );
        })}
      </nav>
      <div className="space-y-1 border-t border-[var(--border-primary)] p-2 text-[11px] text-[var(--text-tertiary)]">
        <Link className="block rounded px-2 py-1 hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]" to={`/workspace/${projectId}/plan`}>Open full Planning</Link>
        <Link className="block rounded px-2 py-1 hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]" to={`/workspace/${projectId}/canon`}>Open full Canon</Link>
      </div>
    </aside>
  );
}
