export type PatternEntryType =
  | 'plot'
  | 'character'
  | 'relationship'
  | 'world'
  | 'theme'
  | 'scene'
  | 'structure';

export type PatternSourceType = 'narrative' | 'mythology' | 'manual';

export interface PatternEntry {
  pattern_id: string;
  project_id: string;
  pattern_type: PatternEntryType;
  name: string;
  summary: string;
  source_type: PatternSourceType;
  generation_modes: string[];
  beats: string[];
  constraints: string[];
  transposition_notes: string;
  writer_notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PatternEntryCreateRequest {
  project_id: string;
  pattern_type: PatternEntryType;
  name: string;
  summary?: string;
  source_type?: PatternSourceType;
  generation_modes?: string[];
  beats?: string[];
  constraints?: string[];
  transposition_notes?: string;
  writer_notes?: string | null;
}

export interface PatternEntryUpdateRequest {
  pattern_type?: PatternEntryType;
  name?: string;
  summary?: string;
  source_type?: PatternSourceType;
  generation_modes?: string[];
  beats?: string[];
  constraints?: string[];
  transposition_notes?: string;
  writer_notes?: string | null;
}
