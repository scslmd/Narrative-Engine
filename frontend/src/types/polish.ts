export interface PolishReport {
  report_id: string;
  project_id: string;
  document_id: string;
  readability_score: number;
  word_count: number;
  sentence_count: number;
  avg_sentence_length: number;
  passive_voice_count: number;
  repetitive_words: string[];
  style_issues: string[];
  generated_at: string;
}

export interface PolishAnalyzeRequest {
  project_id: string;
  document_id: string;
  text: string;
}

export interface ExportRequest {
  project_id: string;
  document_id: string;
  format: string;
  include_frontmatter?: boolean;
  include_toc?: boolean;
  stylesheet?: string | null;
}

export interface ExportStatus {
  export_id: string;
  project_id: string;
  document_id: string;
  format: string;
  status: string;
  artifact_path: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface PolishReportListResponse {
  project_id: string;
  items: PolishReport[];
  meta: Record<string, string>;
}
