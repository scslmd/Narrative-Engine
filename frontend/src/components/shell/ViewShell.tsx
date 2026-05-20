import React, { useMemo } from 'react';
import { PanelLeft, PanelRight } from 'lucide-react';
import { useStudioStore } from '../../stores/studioStore';

export interface ViewShellProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode[];
  leftRailContent?: React.ReactNode;
  rightPanelContent?: React.ReactNode;
  showRightPanel?: boolean;
  onToggleRightPanel?: () => void;
  children: React.ReactNode;
}

export function ViewShell({
  title,
  subtitle,
  actions,
  leftRailContent,
  rightPanelContent,
  showRightPanel = false,
  onToggleRightPanel,
  children,
}: ViewShellProps) {
  const leftRailMode = useStudioStore((state) => state.leftRailMode);
  const leftRailWidth = useStudioStore((state) => state.leftRailWidth);
  const setLeftRailMode = useStudioStore((state) => state.setLeftRailMode);

  const railWidth = useMemo(() => {
    if (leftRailMode === 'collapsed') return '80px';
    return `${leftRailWidth}px`;
  }, [leftRailMode, leftRailWidth]);

  const leftDrawerOpen = leftRailMode === 'overlay';

  const hasLeftRail = !!leftRailContent;
  const hasRightPanelContent = !!rightPanelContent;
  const hasRightPanel = showRightPanel && hasRightPanelContent;

  const gridTemplateColumns = useMemo(() => {
    if (hasLeftRail && hasRightPanel) {
      return `${railWidth} minmax(0,1fr) 320px`;
    }
    if (hasLeftRail) {
      return `${railWidth} minmax(0,1fr)`;
    }
    if (hasRightPanel) {
      return `minmax(0,1fr) 320px`;
    }
    return 'minmax(0,1fr)';
  }, [hasLeftRail, hasRightPanel, railWidth]);

  return (
    <div className="relative flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
      <header className="flex items-center justify-between gap-3 border-b border-[var(--border-primary)] bg-[var(--bg-primary)] px-4 py-3">
        <div className="min-w-0 flex items-center gap-3">
          {hasLeftRail && (
            <button
              type="button"
              onClick={() => setLeftRailMode(leftRailMode === 'overlay' ? 'collapsed' : 'overlay')}
              className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:hidden"
              aria-label="Toggle left rail"
            >
              <PanelLeft className="h-3.5 w-3.5" />
              Nav
            </button>
          )}
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--text-tertiary)]">{title}</p>
            {subtitle && (
              <h1 className="truncate text-sm font-semibold text-[var(--text-primary)]">{subtitle}</h1>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          {hasLeftRail && (
            <button
              type="button"
              onClick={() => setLeftRailMode(leftRailMode === 'collapsed' ? 'expanded' : 'collapsed')}
              className="hidden items-center gap-1 rounded-lg px-2 py-1.5 text-[10px] font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:flex"
              title={leftRailMode === 'collapsed' ? 'Expand rail' : 'Collapse rail'}
            >
              <PanelLeft className="h-3.5 w-3.5" />
            </button>
          )}
          {actions && actions.length > 0 && (
            <div className="hidden items-center gap-1 xl:flex">
              {actions.map((action, i) => (
                <React.Fragment key={i}>{action}</React.Fragment>
              ))}
            </div>
          )}
          {hasRightPanelContent && (
            <button
              type="button"
              onClick={onToggleRightPanel}
              className="hidden items-center gap-1 rounded-lg px-2 py-1.5 text-[10px] font-medium transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] xl:flex"
              title={showRightPanel ? 'Hide panel' : 'Show panel'}
            >
              <PanelRight className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </header>

      <div className="grid min-h-0 flex-1" style={{ gridTemplateColumns }}>
        {hasLeftRail && (
          <div className="min-h-0 overflow-hidden hidden xl:block">
            {leftRailContent}
          </div>
        )}

        <main className="min-h-0 overflow-hidden bg-[var(--bg-primary)]">
          {children}
        </main>

        {hasRightPanel && (
          <aside className="min-h-0 hidden border-l border-[var(--border-primary)] bg-[var(--bg-secondary)] xl:block">
            {rightPanelContent}
          </aside>
        )}
      </div>

      {leftDrawerOpen && hasLeftRail && (
        <div className="absolute left-0 top-0 z-30 h-full w-72 overflow-hidden border-r border-[var(--border-primary)] bg-[var(--bg-primary)] xl:hidden">
          {leftRailContent}
        </div>
      )}

      {leftDrawerOpen && (
        <button
          type="button"
          aria-label="Close left rail drawer"
          onClick={() => setLeftRailMode('collapsed')}
          className="absolute inset-0 z-20 bg-black/20 xl:hidden"
        />
      )}

      {hasRightPanelContent && !showRightPanel && (
        <div className="absolute right-3 top-16 z-10 hidden gap-1 xl:flex">
          <button
            type="button"
            onClick={onToggleRightPanel}
            className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] px-2 py-1 text-[10px] font-medium text-[var(--text-secondary)] shadow-sm transition-colors hover:text-[var(--text-primary)]"
            title="Show panel"
          >
            <PanelRight className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
