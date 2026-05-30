import type { ComponentType, SVGProps } from 'react';
import IdeasIcon from './ideas-32px.svg?react';
import NotesIcon from './notes-32px.svg?react';
import CharactersIcon from './characters-32px.svg?react';
import WorldBibleIcon from './world-bible-32px.svg?react';
import RelationshipsIcon from './relationships-32px.svg?react';
import ArcsIcon from './arcs-32px.svg?react';
import StructureIcon from './structure-32px.svg?react';
import ChaptersIcon from './chapters-32px.svg?react';
import ResearchIcon from './research-32px.svg?react';
import ManuscriptsIcon from './manuscripts-32px.svg?react';
import DraftsIcon from './drafts-32px.svg?react';
import GenerationIcon from './generation-32px.svg?react';
import RevisionIcon from './revision-32px.svg?react';
import SuggestionsIcon from './suggestions-32px.svg?react';
import ReviewIcon from './review-32px.svg?react';
import InspectIcon from './inspect-32px.svg?react';
import PolishIcon from './polish-32px.svg?react';
import CanonIcon from './canon-32px.svg?react';
import JobsIcon from './jobs-32px.svg?react';

export type RailIconComponent = ComponentType<SVGProps<SVGSVGElement>>;

export const railIconKeys = [
  'ideas',
  'notes',
  'characters',
  'worldBible',
  'relationships',
  'arcs',
  'structure',
  'chapters',
  'research',
  'manuscripts',
  'drafts',
  'generation',
  'revision',
  'suggestions',
  'review',
  'inspect',
  'polish',
  'canon',
  'jobs',
] as const;

export type RailIconKey = (typeof railIconKeys)[number];

export const railIcons: Record<RailIconKey, RailIconComponent> = {
  ideas: IdeasIcon,
  notes: NotesIcon,
  characters: CharactersIcon,
  worldBible: WorldBibleIcon,
  relationships: RelationshipsIcon,
  arcs: ArcsIcon,
  structure: StructureIcon,
  chapters: ChaptersIcon,
  research: ResearchIcon,
  manuscripts: ManuscriptsIcon,
  drafts: DraftsIcon,
  generation: GenerationIcon,
  revision: RevisionIcon,
  suggestions: SuggestionsIcon,
  review: ReviewIcon,
  inspect: InspectIcon,
  polish: PolishIcon,
  canon: CanonIcon,
  jobs: JobsIcon,
};
