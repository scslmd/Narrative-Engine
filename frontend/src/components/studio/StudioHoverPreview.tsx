import { memo, useEffect, useState, useCallback } from 'react';
import type { StudioPanelKey } from '../../stores/studioStore';
import { getCharacters } from '../../services/characters';
import { getWorldBibleEntries } from '../../services/worldBible';
import { getBrainstormItems } from '../../services/brainstorm';

interface StudioHoverPreviewProps {
  panelKey: StudioPanelKey;
  isHovering: boolean;
  projectId: string;
}

const PREVIEW_LABELS: Record<StudioPanelKey, string> = {
  suggestions: 'Revision Suggestions',
  ideas: 'Brainstorm Ideas',
  drafts: 'Draft Artifacts',
  manuscripts: 'Manuscript Documents',
  characters: 'Character Profiles',
  worldBible: 'World Bible Entries',
  relationships: 'Character Relationships',
  arcs: 'Character Arcs',
  structure: 'Story Structure',
  chapters: 'Chapter Plans',
  canon: 'Canon Scope',
  generation: 'Story Generation',
  review: 'Review Findings',
  inspect: 'Job Inspector',
  notes: 'Notes',
  jobs: 'Jobs',
};

async function fetchCharacterPreview(projectId: string): Promise<string> {
  try {
    const characters = await getCharacters(projectId);
    if (characters.length > 0) {
      return characters.slice(0, 3).map((c) => `${c.display_name} — ${c.role_in_story}`).join('\n');
    }
    return 'No characters defined yet.';
  } catch {
    return 'Unable to load preview.';
  }
}

async function fetchWorldBiblePreview(projectId: string): Promise<string> {
  try {
    const entries = await getWorldBibleEntries(projectId);
    if (entries.length > 0) {
      return entries.slice(0, 3).map((e) => `${e.entry_type}: ${e.title}`).join('\n');
    }
    return 'No world bible entries yet.';
  } catch {
    return 'Unable to load preview.';
  }
}

async function fetchIdeasPreview(projectId: string): Promise<string> {
  try {
    const items = await getBrainstormItems(projectId);
    if (items.length > 0) {
      return items.slice(0, 3).map((i) => `• ${i.content.slice(0, 60)}`).join('\n');
    }
    return 'No ideas captured yet.';
  } catch {
    return 'Unable to load preview.';
  }
}

const PREVIEW_FETCHERS: Record<string, (projectId: string) => Promise<string>> = {
  characters: fetchCharacterPreview,
  worldBible: fetchWorldBiblePreview,
  ideas: fetchIdeasPreview,
};

function StudioHoverPreviewImpl({ panelKey, isHovering, projectId }: StudioHoverPreviewProps) {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadPreview = useCallback(async () => {
    const fetcher = PREVIEW_FETCHERS[panelKey];
    if (!fetcher) {
      setContent('');
      return;
    }
    setLoading(true);
    const text = await fetcher(projectId);
    setContent(text);
    setLoading(false);
  }, [panelKey, projectId]);

  useEffect(() => {
    if (isHovering && !content) {
      loadPreview();
    }
  }, [isHovering, content, loadPreview]);

  if (!isHovering) return null;

  const label = PREVIEW_LABELS[panelKey] || panelKey;

  return (
    <div
      data-hover-preview
      className="absolute z-50 mt-1 w-64 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-3 shadow-xl"
      style={{ pointerEvents: 'none' }}
    >
      <div className="mb-1 text-xs font-semibold text-[var(--text-primary)]">{label}</div>
      {loading ? (
        <div className="text-[10px] text-[var(--text-secondary)]">Loading...</div>
      ) : content ? (
        <pre className="whitespace-pre-wrap text-[10px] leading-relaxed text-[var(--text-secondary)]">
          {content}
        </pre>
      ) : (
        <div className="text-[10px] text-[var(--text-secondary)]">Click panel to expand</div>
      )}
    </div>
  );
}

export const StudioHoverPreview = memo(StudioHoverPreviewImpl);
