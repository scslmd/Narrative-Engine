export interface MythosExtractionRequest {
  text: string;
  source_corpus?: string | null;
  generation_mode: 'same_world' | 'transposed' | 'pure_pattern';
  project_id?: string | null;
}

export interface MythosExtractionSummary {
  source_corpus: string;
  archetypal_patterns: number;
  narrative_structures: number;
  cosmic_rules: number;
  symbolic_motifs: number;
}

export interface MythosExtractionResponse {
  project_id: string;
  status: 'completed' | 'failed';
  extraction: MythosExtractionSummary | null;
  error: string | null;
}
