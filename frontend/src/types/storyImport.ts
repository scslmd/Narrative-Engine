export interface StoryImportRequest {
  project_name: string;
  story_text: string;
  project_id?: string;
  genre?: string;
  tone?: string;
}

export interface StoryImportResponse {
  project_id: string;
  status: string;
  message: string;
  warnings: string[];
  chapters_processed: number;
  total_estimated_chapters: number;
  chunks_processed: number;
  total_estimated_chunks: number;
  analysis_mode: string;
}

export interface ImportSubmitResponse {
  import_id: string;
  status: "pending";
}

export interface ImportProgress {
  import_id: string;
  status: "pending" | "running" | "completed" | "failed";
  phase: string;
  chapters_processed: number;
  total_estimated_chapters: number;
  chunks_processed: number;
  total_estimated_chunks: number;
  result: StoryImportResponse | null;
  error: string | null;
}
