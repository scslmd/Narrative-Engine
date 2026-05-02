export type MythosEntryType =
  | 'archetype'
  | 'motif'
  | 'cosmic_rule'
  | 'symbol'
  | 'ritual'
  | 'deity'
  | 'cycle'
  | 'theme';

export type MythosVisibilityScope = 'project' | 'forkable' | 'private';

export interface MythosEntry {
  mythos_id: string;
  project_id: string;
  entry_type: MythosEntryType;
  name: string;
  summary: string;
  canonical_facts: string[];
  pattern_notes: string[];
  source_corpus?: string | null;
  generation_guidance: string;
  visibility_scope: MythosVisibilityScope;
  writer_notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MythosEntryCreateRequest {
  project_id: string;
  entry_type: MythosEntryType;
  name: string;
  summary?: string;
  canonical_facts?: string[];
  pattern_notes?: string[];
  source_corpus?: string | null;
  generation_guidance?: string;
  visibility_scope?: MythosVisibilityScope;
  writer_notes?: string | null;
}

export interface MythosEntryUpdateRequest {
  entry_type?: MythosEntryType;
  name?: string;
  summary?: string;
  canonical_facts?: string[];
  pattern_notes?: string[];
  source_corpus?: string | null;
  generation_guidance?: string;
  visibility_scope?: MythosVisibilityScope;
  writer_notes?: string | null;
}
