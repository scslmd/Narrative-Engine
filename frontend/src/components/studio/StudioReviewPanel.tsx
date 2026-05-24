import { useState } from 'react';
import { FindingsList } from '../review';
import { InspectRunLinksList } from '../inspectLinks';

interface StudioReviewPanelProps {
  projectId: string;
}

export function StudioReviewPanel({ projectId }: StudioReviewPanelProps) {
  const [activeTab, setActiveTab] = useState<'findings' | 'links'>('findings');

  return (
 <div className="flex h-full flex-col">
        <div className="flex shrink-0 gap-1 px-2.5 py-1 border-b border-[var(--border-primary)]">
          <button
            type="button"
            onClick={() => setActiveTab('findings')}
            className={`rounded px-1.5 py-0.5 text-[9px] font-medium transition-colors ${
              activeTab === 'findings'
                ? 'bg-[var(--accent-primary)] text-white'
                : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]'
            }`}
          >
            Findings
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('links')}
            className={`rounded px-1.5 py-0.5 text-[9px] font-medium transition-colors ${
              activeTab === 'links'
                ? 'bg-[var(--accent-primary)] text-white'
                : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]'
            }`}
          >
            Links
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {activeTab === 'findings' ? (
            <FindingsList projectId={projectId} />
          ) : (
            <InspectRunLinksList projectId={projectId} />
          )}
        </div>
      </div>
  );
}
