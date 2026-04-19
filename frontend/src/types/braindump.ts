/**
 * Brain Dump Types
 *
 * Types for brain dump sessions and AI organize operations.
 */

export type BrainDumpSessionState = 'active' | 'organized' | 'archived';

export type BrainstormItemType =
  | 'character'
  | 'location'
  | 'plot_point'
  | 'theme'
  | 'conflict'
  | 'world_building'
  | 'dialogue'
  | 'relationship'
  | 'object'
  | 'rule';

export interface BrainDumpSession {
  session_id: string;
  project_id: string;
  title: string | null;
  raw_text: string;
  state: BrainDumpSessionState;
  created_at: string | null;
  updated_at: string;
}

export interface BrainDumpSessionCreateRequest {
  project_id: string;
  title?: string | null;
  raw_text?: string;
}

export interface BrainDumpSessionPatchRequest {
  raw_text?: string | null;
  title?: string | null;
  state?: BrainDumpSessionState | null;
}

export interface BrainDumpSessionListResponse {
  project_id: string;
  sessions: BrainDumpSession[];
  meta: Record<string, string>;
}

export interface BrainDumpOrganizeResponse {
  session_id: string;
  categorized_items: Record<BrainstormItemType, BrainstormItem[]>;
  total_items: number;
}

export interface BrainstormItem {
  item_id: string;
  project_id: string;
  content: string;
  status: string;
  tags: string[];
  source_notes: string | null;
  item_type: BrainstormItemType | null;
}
