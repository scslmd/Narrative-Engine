import { useState } from 'react';
import { FindingsList } from '../review';
import { InspectRunLinksList } from '../inspectLinks';

interface StudioReviewPanelProps {
  projectId: string;
}

export function StudioReviewPanel({ projectId }: StudioReviewPanelProps) {
  const [activeTab, setActiveTab] = useState<'findings' | 'links'>('findings');

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setActiveTab('findings')}
          className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
            activeTab === 'findings'
              ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700'
          }`}
        >
          Findings
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('links')}
          className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
            activeTab === 'links'
              ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700'
          }`}
        >
          Inspect Links
        </button>
      </div>

      {activeTab === 'findings' ? (
        <FindingsList projectId={projectId} />
      ) : (
        <InspectRunLinksList projectId={projectId} />
      )}
    </div>
  );
}
