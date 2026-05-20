import { PanelLeft, PanelRight } from 'lucide-react';
import { useStudioStore } from '../../stores/studioStore';

interface StudioCommandBarProps {
  projectName?: string;
  railCollapsed?: boolean;
  panelVisible?: boolean;
  onToggleRail?: () => void;
  onTogglePanel?: () => void;
}

export function StudioCommandBar({
  projectName = 'Current Project',
  railCollapsed,
  panelVisible,
  onToggleRail,
  onTogglePanel,
}: StudioCommandBarProps) {
  const leftRailMode = useStudioStore((state) => state.leftRailMode);
  const setLeftRailMode = useStudioStore((state) => state.setLeftRailMode);

  return (
    <header className="flex items-center justify-between gap-3 border-b border-[var(--border-primary)] bg-[var(--bg-primary)] px-4 py-3">
      <div className="min-w-0 flex items-center gap-3">
        <button
          type="button"
          onClick={() => {
            if (onToggleRail) {
              onToggleRail();
            } else {
              setLeftRailMode(leftRailMode === 'overlay' ? 'collapsed' : 'overlay');
            }
          }}
          className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:hidden"
          aria-label="Toggle project rail"
        >
          <PanelLeft className="h-3.5 w-3.5" />
          Project
        </button>
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--text-tertiary)]">Studio Desk</p>
          <h1 className="truncate text-sm font-semibold text-[var(--text-primary)]">{projectName}</h1>
        </div>
      </div>
      <div className="flex items-center gap-1">
        {/* Desktop rail toggle */}
        <button
          type="button"
          onClick={() => {
            if (onToggleRail) {
              onToggleRail();
            } else {
              setLeftRailMode(leftRailMode === 'collapsed' ? 'expanded' : 'collapsed');
            }
          }}
          className="hidden items-center gap-1 rounded-lg px-2 py-1.5 text-[10px] font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:flex"
          title={railCollapsed ? 'Expand rail' : 'Collapse rail'}
        >
          <PanelLeft className="h-3.5 w-3.5" />
        </button>
        {/* Desktop panel toggle */}
        <button
          type="button"
          onClick={() => {
            if (onTogglePanel) {
              onTogglePanel();
            }
          }}
          className="hidden items-center gap-1 rounded-lg px-2 py-1.5 text-[10px] font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:flex"
          title={panelVisible ? 'Hide context panel' : 'Show context panel'}
        >
          <PanelRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </header>
  );
}
