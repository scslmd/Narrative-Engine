export interface PatternExtractionRequest {
  text: string;
  source_type: 'mythology' | 'narrative';
  generation_mode?: 'same_world' | 'new_characters' | 'transposed';
  project_id?: string | null;
  source_corpus?: string | null;
}

export interface PatternExtractionSummary {
  source_corpus: string;
  archetypal_patterns: number;
  narrative_structures: number;
  world_rules: number;
  symbolic_motifs: number;
}

export interface ExtractPatternsRequest {
  source_type: 'mythology' | 'narrative';
  generation_mode?: 'same_world' | 'new_characters' | 'transposed';
  source_corpus?: string | null;
}

export interface PatternExtractionResponse {
  status: 'completed' | 'failed';
  project_id: string;
  extraction: PatternExtractionSummary | null;
  error: string | null;
}
