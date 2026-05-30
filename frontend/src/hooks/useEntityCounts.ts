import { useQueries } from '@tanstack/react-query';
import { getArcCandidates } from '../services/arcs';
import { getBrainstormItems } from '../services/brainstorm';
import { getChapterPlans } from '../services/planning';
import { getCharacters } from '../services/characters';
import { getDraftArtifacts, getManuscriptDocuments, getRevisionSuggestions } from '../services/drafting';
import { getRelationships } from '../services/relationships';
import { getResearchItems } from '../services/research';
import { getRevisionPasses } from '../services/revision';
import { getStoryboardCards } from '../services/storyboard';
import { getWorldBibleEntries } from '../services/worldBible';
import { jobsApi } from '../lib/jobsApi';
import type { StudioPanelKey } from '../stores/studioStore';

export interface EntityCounts {
  ideas: number;
  characters: number;
  worldBible: number;
  relationships: number;
  arcs: number;
  structure: number;
  chapters: number;
  manuscripts: number;
  drafts: number;
  generation: null;
  revision: number;
  suggestions: number;
  review: null;
  inspect: null;
  canon: null;
  jobs: number;
  research: number;
  notes: null;
  polish: null;
}

const DEFAULT_COUNTS: EntityCounts = {
  ideas: 0,
  characters: 0,
  worldBible: 0,
  relationships: 0,
  arcs: 0,
  structure: 0,
  chapters: 0,
  manuscripts: 0,
  drafts: 0,
  generation: null,
  revision: 0,
  suggestions: 0,
  review: null,
  inspect: null,
  canon: null,
  jobs: 0,
  research: 0,
  notes: null,
  polish: null,
};

interface QueryDefinition {
  panel: keyof EntityCounts;
  queryFn: (projectId: string) => Promise<unknown[]>;
}

const QUERY_DEFINITIONS: QueryDefinition[] = [
  { panel: 'ideas', queryFn: (id: string) => getBrainstormItems(id) },
  { panel: 'characters', queryFn: (id: string) => getCharacters(id) },
  { panel: 'worldBible', queryFn: (id: string) => getWorldBibleEntries(id) },
  { panel: 'relationships', queryFn: (id: string) => getRelationships(id) },
  { panel: 'arcs', queryFn: (id: string) => getArcCandidates(id) },
  { panel: 'structure', queryFn: (id: string) => getStoryboardCards(id) },
  { panel: 'chapters', queryFn: (id: string) => getChapterPlans(id) },
  { panel: 'manuscripts', queryFn: (id: string) => getManuscriptDocuments(id) },
  { panel: 'drafts', queryFn: (id: string) => getDraftArtifacts(id) },
  { panel: 'revision', queryFn: (id: string) => getRevisionPasses(id) },
  { panel: 'suggestions', queryFn: (id: string) => getRevisionSuggestions(id) },
  { panel: 'jobs', queryFn: (id: string) => jobsApi.list(id) },
  { panel: 'research', queryFn: (id: string) => getResearchItems(id) },
];

export function useEntityCounts(projectId: string): EntityCounts {
  const queries = useQueries({
    queries: QUERY_DEFINITIONS.map((def) => ({
      queryKey: [def.panel, projectId],
      queryFn: () => def.queryFn(projectId),
      select: (data: unknown[]) => data.length,
    })),
  });

  const counts: EntityCounts = { ...DEFAULT_COUNTS };
  for (let i = 0; i < queries.length; i++) {
    const length = queries[i].data;
    if (typeof length === 'number') {
      const panel = QUERY_DEFINITIONS[i].panel as keyof Omit<EntityCounts, 'generation' | 'review' | 'inspect' | 'canon' | 'notes' | 'polish'>;
      counts[panel] = length;
    }
  }

  return counts;
}

export function getPanelCount(panel: StudioPanelKey, counts: EntityCounts): number | null {
  return counts[panel] ?? null;
}
