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
}
