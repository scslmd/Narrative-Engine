import { PanelLeft } from 'lucide-react';
import { useStudioStore } from '../../stores/studioStore';

interface StudioCommandBarProps {
  projectName?: string;
}

export function StudioCommandBar({ projectName = 'Current Project' }: StudioCommandBarProps) {
  const leftRailMode = useStudioStore((state) => state.leftRailMode);
  const setLeftRailMode = useStudioStore((state) => state.setLeftRailMode);

  return (
    <header className="flex items-center justify-between gap-3 border-b border-[var(--border-primary)] bg-[var(--bg-primary)] px-4 py-3">
      <div className="min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--text-tertiary)]">Studio Desk</p>
        <h1 className="truncate text-sm font-semibold text-[var(--text-primary)]">{projectName}</h1>
      </div>
      <button
        type="button"
        onClick={() => {
          setLeftRailMode(leftRailMode === 'overlay' ? 'collapsed' : 'overlay');
        }}
        className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:hidden"
      >
        <PanelLeft className="h-3.5 w-3.5" />
        Project
      </button>
    </header>
  );
}
