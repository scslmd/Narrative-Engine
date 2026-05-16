import { BookOpen, GitPullRequestArrow, Lightbulb, PanelLeft, PanelRight, Search, Wand2 } from 'lucide-react';
import { useStudioStore, type StudioPanelKey } from '../../stores/studioStore';

const commands: Array<{ label: string; panel: StudioPanelKey; icon: typeof Lightbulb }> = [
  { label: 'Capture', panel: 'ideas', icon: Lightbulb },
  { label: 'Write', panel: 'suggestions', icon: BookOpen },
  { label: 'Generate', panel: 'generation', icon: Wand2 },
  { label: 'Review', panel: 'review', icon: GitPullRequestArrow },
  { label: 'Inspect', panel: 'inspect', icon: Search },
];

interface StudioCommandBarProps {
  projectName?: string;
}

export function StudioCommandBar({ projectName = 'Current Project' }: StudioCommandBarProps) {
  const activePanel = useStudioStore((state) => state.activePanel);
  const openPanel = useStudioStore((state) => state.openPanel);
  const toggleLeftRail = useStudioStore((state) => state.toggleLeftRail);
  const toggleContextPanel = useStudioStore((state) => state.toggleContextPanel);

  return (
    <header className="flex items-center justify-between gap-3 border-b border-[var(--border-primary)] bg-[var(--bg-primary)] px-4 py-3">
      <div className="min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--text-tertiary)]">Studio Desk</p>
        <h1 className="truncate text-sm font-semibold text-[var(--text-primary)]">{projectName}</h1>
      </div>
      <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={toggleLeftRail}
            className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:hidden"
          >
            <PanelLeft className="h-3.5 w-3.5" />
            Project
          </button>
          <button
            type="button"
            onClick={toggleContextPanel}
            className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:hidden"
          >
            <PanelRight className="h-3.5 w-3.5" />
            Context
          </button>
        </div>
        <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Studio commands">
        {commands.map((command) => {
          const Icon = command.icon;
          const active = activePanel === command.panel;
          return (
            <button
              key={command.panel}
              type="button"
              onClick={() => openPanel(command.panel)}
              aria-pressed={active}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                active
                  ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {command.label}
            </button>
          );
        })}
      </nav>
    </header>
  );
}
