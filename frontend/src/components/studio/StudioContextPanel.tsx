import { AidsPanel } from '../aids/AidsPanel';
import { GenerationView } from '../../views/GenerationView';
import { InspectView } from '../../views/InspectView';
import { JobLaunchPanel } from '../JobLaunchPanel';
import { NotesPanel } from '../NotesPanel';
import { ReviewView } from '../../views/ReviewView';
import { StudioCharactersPanel } from './StudioCharactersPanel';
import { StudioIdeasPanel } from './StudioIdeasPanel';
import { StudioRelationshipsPanel } from './StudioRelationshipsPanel';
import { StudioWorldBiblePanel } from './StudioWorldBiblePanel';
import { useStudioStore } from '../../stores/studioStore';
import type { StudioPanelKey } from '../../stores/studioStore';

const panelLabels: Record<StudioPanelKey, string> = {
  suggestions: 'Suggestions',
  ideas: 'Ideas',
  characters: 'Characters',
  worldBible: 'World Bible',
  relationships: 'Relationships',
  generation: 'Generation',
  review: 'Review',
  inspect: 'Inspect',
  notes: 'Notes',
  jobs: 'Jobs',
};

interface StudioContextPanelProps {
  projectId: string;
}

export function StudioContextPanel({ projectId }: StudioContextPanelProps) {
  const activePanel = useStudioStore((s) => s.activePanel);
  const setContextPanelOpen = useStudioStore((s) => s.setContextPanelOpen);

  const label = panelLabels[activePanel];

  const renderPanel = () => {
    switch (activePanel) {
      case 'ideas':
        return <StudioIdeasPanel projectId={projectId} />;
      case 'characters':
        return <StudioCharactersPanel projectId={projectId} />;
      case 'worldBible':
        return <StudioWorldBiblePanel projectId={projectId} />;
      case 'relationships':
        return <StudioRelationshipsPanel projectId={projectId} />;
      case 'generation':
        return <GenerationView />;
      case 'review':
        return <ReviewView />;
      case 'inspect':
        return <InspectView />;
      case 'notes':
        return <NotesPanel projectId={projectId} />;
      case 'jobs':
        return <JobLaunchPanel projectId={projectId} />;
      case 'suggestions':
        return <AidsPanel projectId={projectId} suggestions={[]} />;
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 dark:border-slate-700 px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-slate-100">{label}</h2>
        <button
          type="button"
          onClick={() => setContextPanelOpen(false)}
          className="rounded-md p-1 text-gray-400 hover:text-gray-600 dark:hover:text-slate-300"
          aria-label="Close panel"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M18 6 6 18" />
            <path d="m6 6 12 12" />
          </svg>
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">{renderPanel()}</div>
    </div>
  );
}
