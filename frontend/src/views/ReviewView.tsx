import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { FindingsList } from '../components/review';
import { InspectRunLinksList } from '../components/inspectLinks';

export function ReviewView() {
  const { projectId } = useParams<{ projectId: string }>();
  const [activeTab, setActiveTab] = useState<'findings' | 'links'>('findings');

  if (!projectId) {
    return <div className="text-gray-500">No project selected</div>;
  }

  return (
    <div className="h-full flex flex-col">
      <header className="border-b px-4 py-2 bg-white">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('findings')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'findings' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Findings
          </button>
          <button
            onClick={() => setActiveTab('links')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'links' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Inspect Run Links
          </button>
        </nav>
      </header>

      <main className="flex-1 overflow-y-auto pr-2">
        {activeTab === 'findings' && (
          <div className="p-4">
            <FindingsList projectId={projectId} />
          </div>
        )}
        {activeTab === 'links' && (
          <div className="p-4">
            <InspectRunLinksList projectId={projectId} />
          </div>
        )}
      </main>
    </div>
  );
}
