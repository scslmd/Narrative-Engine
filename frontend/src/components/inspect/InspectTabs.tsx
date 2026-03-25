import { useState } from 'react';
import StepTimeline from './StepTimeline';
import ArtifactLineage from './ArtifactLineage';
import type { InspectContext } from '../../types/inspect';

interface InspectTabsProps {
  context: InspectContext;
}

type TabKey = 'steps' | 'lineage' | 'attempts';

export default function InspectTabs({ context }: InspectTabsProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('steps');

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'steps', label: 'Steps' },
    { key: 'lineage', label: 'Lineage' },
    { key: 'attempts', label: 'Attempts' },
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="border-b px-4">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex-1 overflow-y-auto">
        {activeTab === 'steps' && <StepTimeline context={context} />}
        {activeTab === 'lineage' && <ArtifactLineage context={context} />}
        {activeTab === 'attempts' && (
          <div className="p-4 text-sm text-gray-500">
            Attempts view coming soon...
          </div>
        )}
      </div>
    </div>
  );
}
