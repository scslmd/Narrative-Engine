import type { ReactNode } from 'react';
import {
  Anchor,
  Book,
  FileCheck,
  GitBranch,
  LayoutList,
  Lightbulb,
  Map,
  Network,
  Sparkles,
  User,
} from 'lucide-react';

export type PlanningTabKey =
  | 'manifest'
  | 'planning'
  | 'flow'
  | 'arcs'
  | 'branches'
  | 'decisions'
  | 'checker'
  | 'brainstorm'
  | 'foundation'
  | 'characters'
  | 'world-bible'
  | 'relationships';

export interface PlanningTabDescriptor {
  key: PlanningTabKey;
  label: string;
  icon: ReactNode;
}

export const ALL_PLANNING_TABS: PlanningTabDescriptor[] = [
  { key: 'manifest', label: 'Manifest', icon: <LayoutList className="w-3.5 h-3.5" /> },
  { key: 'planning', label: 'Planning', icon: <Map className="w-3.5 h-3.5" /> },
  { key: 'flow', label: 'Flow', icon: <GitBranch className="w-3.5 h-3.5" /> },
  { key: 'arcs', label: 'Arcs', icon: <Network className="w-3.5 h-3.5" /> },
  { key: 'branches', label: 'Branches', icon: <GitBranch className="w-3.5 h-3.5" /> },
  { key: 'decisions', label: 'Decisions', icon: <Sparkles className="w-3.5 h-3.5" /> },
  { key: 'checker', label: 'Checker', icon: <FileCheck className="w-3.5 h-3.5" /> },
  { key: 'brainstorm', label: 'Brainstorm', icon: <Lightbulb className="w-3.5 h-3.5" /> },
  { key: 'foundation', label: 'Foundation', icon: <Anchor className="w-3.5 h-3.5" /> },
  { key: 'characters', label: 'Characters', icon: <User className="w-3.5 h-3.5" /> },
  { key: 'world-bible', label: 'World Bible', icon: <Book className="w-3.5 h-3.5" /> },
  { key: 'relationships', label: 'Relationships', icon: <Network className="w-3.5 h-3.5" /> },
];

export const CORE_PLANNING_TAB_KEYS: PlanningTabKey[] = [
  'manifest',
  'planning',
  'flow',
  'arcs',
  'branches',
  'decisions',
  'checker',
];

export const CONTENT_PLANNING_TAB_KEYS: PlanningTabKey[] = [
  'brainstorm',
  'foundation',
  'characters',
  'world-bible',
  'relationships',
];
