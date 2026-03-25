import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { ManifestViewer } from '../components/ManifestViewer';
import { SequenceViewer } from '../components/SequenceViewer';
import { ChapterReader } from '../components/ChapterReader';
import { InspectMode } from '../components/inspect';
import { FindingsList } from '../components/review';
import { RoleModelChecker } from '../components/checker';
import { StoryBranchesList } from '../components/branches';
import { DecisionTree } from '../components/decisions';
import { InspectRunLinksList } from '../components/inspectLinks';

export function PlanningView() {
  const { projectId } = useParams<{ projectId: string }>();
  const [activeTab, setActiveTab] = useState<'manifest' | 'sequences' | 'checker' | 'branches' | 'decisions'>('manifest');

  if (!projectId) {
    return <div className="text-gray-500">No project selected</div>;
  }

  return (
    <div className="h-full flex flex-col">
      <header className="border-b px-4 py-2 bg-white">
        <nav className="flex gap-4 flex-wrap">
          <button
            onClick={() => setActiveTab('manifest')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'manifest' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Manifest
          </button>
          <button
            onClick={() => setActiveTab('sequences')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'sequences' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Sequences
          </button>
          <button
            onClick={() => setActiveTab('branches')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'branches' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Branches
          </button>
          <button
            onClick={() => setActiveTab('decisions')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'decisions' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Decisions
          </button>
          <button
            onClick={() => setActiveTab('checker')}
            className={`px-3 py-1.5 text-sm rounded ${activeTab === 'checker' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Checker
          </button>
        </nav>
      </header>

      <main className="flex-1 overflow-y-auto pr-2">
        {activeTab === 'manifest' && <ManifestViewer projectId={projectId} />}
        {activeTab === 'sequences' && <SequenceViewer projectId={projectId} />}
        {activeTab === 'branches' && (
          <div className="p-4">
            <StoryBranchesList projectId={projectId} />
          </div>
        )}
        {activeTab === 'decisions' && (
          <div className="p-4">
            <DecisionTree projectId={projectId} />
          </div>
        )}
        {activeTab === 'checker' && (
          <div className="p-4">
            <RoleModelChecker projectId={projectId} />
          </div>
        )}
      </main>
    </div>
  );
}

export function WritingView() {
  const { projectId } = useParams<{ projectId: string }>();

  if (!projectId) {
    return <div className="text-gray-500">No project selected</div>;
  }

  return (
    <div className="h-full overflow-y-auto pr-2">
      <SequenceViewer projectId={projectId} />
    </div>
  );
}

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

export function InspectView() {
  const { projectId, jobId } = useParams<{ projectId: string; jobId?: string }>();

  if (!projectId) {
    return <div className="text-gray-500">No project selected</div>;
  }

  return (
    <div className="h-full">
      <InspectMode />
    </div>
  );
}