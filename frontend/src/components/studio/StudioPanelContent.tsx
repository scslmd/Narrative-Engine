import { memo } from 'react';
import type { StudioPanelKey } from '../../stores/studioStore';
import { StudioCharactersPanel } from './StudioCharactersPanel';
import { StudioIdeasPanel } from './StudioIdeasPanel';
import { StudioWorldBiblePanel } from './StudioWorldBiblePanel';
import { StudioRelationshipsPanel } from './StudioRelationshipsPanel';
import { StudioArcsPanel } from './StudioArcsPanel';
import { StudioGenerationPanel } from './StudioGenerationPanel';
import { StudioReviewPanel } from './StudioReviewPanel';
import { StudioInspectPanel } from './StudioInspectPanel';
import { StudioSuggestionsPanel } from './StudioSuggestionsPanel';
import { StudioDraftsPanel } from './StudioDraftsPanel';
import { StudioManuscriptsPanel } from './StudioManuscriptsPanel';
import { StudioStructurePanel } from './StudioStructurePanel';
import { StudioChaptersPanel } from './StudioChaptersPanel';
import { StudioCanonPanel } from './StudioCanonPanel';
import { NotesPanel } from '../NotesPanel';
import { JobLaunchPanel } from '../JobLaunchPanel';

interface StudioPanelContentProps {
  panelKey: StudioPanelKey;
  projectId: string;
}

function StudioPanelContentImpl({ panelKey, projectId }: StudioPanelContentProps) {
  switch (panelKey) {
    case 'characters':
      return <StudioCharactersPanel projectId={projectId} />;
    case 'ideas':
      return <StudioIdeasPanel projectId={projectId} />;
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
      return <StudioManuscriptsPanel />;
    case 'structure':
      return <StudioStructurePanel projectId={projectId} />;
    case 'chapters':
      return <StudioChaptersPanel projectId={projectId} />;
    case 'canon':
      return <StudioCanonPanel projectId={projectId} />;
    case 'notes':
      return <NotesPanel projectId={projectId} />;
    case 'jobs':
      return <JobLaunchPanel projectId={projectId} />;
    default:
      return (
        <div className="flex h-full items-center justify-center p-2.5 text-xs text-[var(--text-secondary)]">
          Panel &quot;{panelKey}&quot; not yet implemented.
        </div>
      );
  }
}

export const StudioPanelContent = memo(StudioPanelContentImpl);
