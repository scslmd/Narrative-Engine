import { useWritingDocumentController } from '../../domains/writing/useWritingDocumentController';
import { JobLaunchPanel } from '../JobLaunchPanel';
import { NotesPanel } from '../NotesPanel';
import { StudioDraftsPanel } from './StudioDraftsPanel';
import { StudioGenerationPanel } from './StudioGenerationPanel';
import { StudioIdeasPanel } from './StudioIdeasPanel';
import { StudioInspectPanel } from './StudioInspectPanel';
import { StudioManuscriptsPanel } from './StudioManuscriptsPanel';
import { StudioCharactersPanel } from './StudioCharactersPanel';
import { StudioRelationshipsPanel } from './StudioRelationshipsPanel';
import { StudioArcsPanel } from './StudioArcsPanel';
import { StudioReviewPanel } from './StudioReviewPanel';
import { StudioSuggestionsPanel } from './StudioSuggestionsPanel';
import { StudioWorldBiblePanel } from './StudioWorldBiblePanel';
import { useStudioStore } from '../../stores/studioStore';
import type { StudioPanelKey } from '../../stores/studioStore';

const primaryTabs: Array<{ label: string; panel: StudioPanelKey }> = [
  { label: 'Suggestions', panel: 'suggestions' },
  { label: 'Drafts', panel: 'drafts' },
  { label: 'Manuscripts', panel: 'manuscripts' },
  { label: 'Ideas', panel: 'ideas' },
  { label: 'Characters', panel: 'characters' },
  { label: 'World', panel: 'worldBible' },
  { label: 'Review', panel: 'review' },
];

const panelLabels: Record<StudioPanelKey, string> = {
  suggestions: 'Suggestions',
  ideas: 'Ideas',
  drafts: 'Drafts',
  manuscripts: 'Manuscripts',
  characters: 'Characters',
  worldBible: 'World Bible',
  relationships: 'Relationships',
  arcs: 'Arcs',
  structure: 'Structure',
  chapters: 'Chapters',
  canon: 'Canon',
  generation: 'Generation',
  review: 'Review',
  inspect: 'Inspect',
  notes: 'Notes',
  jobs: 'Jobs',
};

interface StudioContextPanelProps {
  projectId: string;
  showCloseButton?: boolean;
  onManuscriptSelect?: (documentId: string) => void;
}

export function StudioContextPanel({ projectId, showCloseButton = true, onManuscriptSelect }: StudioContextPanelProps) {
  const activePanel = useStudioStore((s) => s.activePanel);
  const openPanel = useStudioStore((s) => s.openPanel);
  const setPanelVisible = useStudioStore((s) => s.setPanelVisible);

  const writingController = useWritingDocumentController({
    projectId,
    chapterId: undefined,
  });
  const openSuggestionCount = writingController.openSuggestions.length;

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
      case 'arcs':
        return <StudioArcsPanel projectId={projectId} />;
      case 'generation':
        return <StudioGenerationPanel projectId={projectId} />;
      case 'review':
        return <StudioReviewPanel projectId={projectId} />;
      case 'inspect':
        return <StudioInspectPanel />;
      case 'suggestions':
        return <StudioSuggestionsPanel projectId={projectId} />;
      case 'drafts':
        return <StudioDraftsPanel projectId={projectId} />;
      case 'manuscripts':
        return <StudioManuscriptsPanel onSelect={onManuscriptSelect} />;
      case 'notes':
        return <NotesPanel projectId={projectId} />;
      case 'jobs':
        return <JobLaunchPanel projectId={projectId} />;
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div
        className="flex items-center gap-1 overflow-x-auto border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] px-2 py-2"
        role="tablist"
        aria-label="Studio context tabs"
      >
        {primaryTabs.map((tab) => {
          const active = activePanel === tab.panel;
          const isSuggestions = tab.panel === 'suggestions';

          return (
            <button
              key={tab.panel}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => openPanel(tab.panel)}
              className={`relative rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                active
                  ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-sm ring-1 ring-[var(--border-primary)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]'
              }`}
            >
              {tab.label}
              {isSuggestions && openSuggestionCount > 0 && (
                <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-amber-500 text-[9px] font-bold text-white">
                  {openSuggestionCount > 9 ? '9+' : openSuggestionCount}
                </span>
              )}
            </button>
          );
        })}
      </div>
      <div className="flex items-center justify-between border-b border-[var(--border-primary)] px-4 py-3">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">{label}</h2>
        {showCloseButton ? (
          <button
            type="button"
            onClick={() => setPanelVisible(false)}
            className="rounded-md px-2 py-1 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            Close
          </button>
        ) : null}
      </div>
      <div className="flex-1 overflow-y-auto p-4">{renderPanel()}</div>
    </div>
  );
}
