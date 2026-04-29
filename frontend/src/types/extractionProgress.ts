export interface ExtractionSubmitResponse {
  extraction_id: string;
}

export interface ExtractionProgressResult {
  project_id: string;
  source_corpus: string;
  archetypal_patterns: number;
  narrative_structures: number;
  world_rules: number;
  symbolic_motifs: number;
  warnings: string[];
}

export interface ExtractionProgressResponse {
  extraction_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  phase: string;
  result: ExtractionProgressResult | null;
  error: string | null;
}
