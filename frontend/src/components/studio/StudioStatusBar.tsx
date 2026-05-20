import { memo, useState } from 'react';
import { useStudioStore } from '../../stores/studioStore';

interface StudioStatusBarProps {
  projectId: string;
}

function StudioStatusBarImpl({ projectId }: StudioStatusBarProps) {
  const layout = useStudioStore((s) => s.layout);
  const [collapsed, setCollapsed] = useState(false);

  const panelCount = Object.values(layout.panels).filter((p) => p.visible).length;

  if (collapsed) {
    return (
      <div
        data-status-bar
        className="flex shrink-0 items-center justify-end border-t border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-1"
      >
        <button
          type="button"
          onClick={() => setCollapsed(false)}
          className="text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
        >
          ▲
        </button>
      </div>
    );
  }

  return (
    <div
      data-status-bar
      className="flex shrink-0 items-center justify-between border-t border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-1.5"
    >
      <div className="flex items-center gap-4">
        <span className="text-[10px] font-medium text-[var(--text-tertiary)]">
          Project: {projectId.length > 12 ? `${projectId.slice(0, 12)}…` : projectId}
        </span>
        <span data-panel-count className="text-[10px] text-[var(--text-secondary)]">
          {panelCount} panel{panelCount !== 1 ? 's' : ''} active
        </span>
        {layout.layoutPreset && (
          <span className="rounded bg-[var(--bg-primary)] px-1.5 py-0.5 text-[9px] font-medium text-[var(--text-tertiary)]">
            {layout.layoutPreset.replace('-', ' ')} layout
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className="text-[10px] text-[var(--text-tertiary)]">
          Radial Hub
        </span>
        <button
          type="button"
          onClick={() => setCollapsed(true)}
          className="text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
        >
          ▼
        </button>
      </div>
    </div>
  );
}

export const StudioStatusBar = memo(StudioStatusBarImpl);
