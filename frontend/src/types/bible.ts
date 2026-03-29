/**
 * World Bible Types
 * 
 * Types for world bible entries (locations, organizations, artifacts, etc.).
 * Backend schema: app.schemas.story_development.WorldBibleEntry
 */

export type WorldBibleEntryType =
  | 'location'
  | 'organization'
  | 'artifact'
  | 'event'
  | 'concept'
  | 'creature'
  | 'magic_system'
  | 'technology'
  | 'culture'
  | 'history';

export interface WorldBibleEntry {
  entry_id: string;
  project_id: string;
  entry_type: WorldBibleEntryType;
  title: string;
  summary: string;
  canonical_facts: string[];
  related_character_ids: string[];
  source_artifacts: string[];
  visibility_scope: string;
  continuity_warnings: string[];
  writer_notes: string | null;
}

export interface WorldBibleEntryCreateRequest {
  project_id: string;
  entry_type: WorldBibleEntryType;
  title: string;
  summary: string;
  canonical_facts?: string[];
  related_character_ids?: string[];
  source_artifacts?: string[];
  visibility_scope?: string;
  continuity_warnings?: string[];
  writer_notes?: string | null;
}

export interface WorldBibleEntryUpdateRequest {
  title?: string;
  summary?: string;
  canonical_facts?: string[];
  related_character_ids?: string[];
  source_artifacts?: string[];
  visibility_scope?: string;
  continuity_warnings?: string[];
  writer_notes?: string | null;
}

// Response wrappers
export interface WorldBibleEntryListResponse {
  project_id: string;
  items: WorldBibleEntry[];
  meta: Record<string, string>;
}

/**
 * Legacy types for backward compatibility with existing components.
 * These are being phased out in favor of WorldBibleEntry.
 */

export type BibleEntryType = 'character' | 'location' | 'rule' | 'object' | 'concept';

export interface BibleEntry {
  id: string;
  type: BibleEntryType;
  title: string;
  summary: string;
  details?: string;
}
