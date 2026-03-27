export interface DraftArtifact {
  artifact_id: string;
  project_id: string;
  title: string;
  content: string;
  source_plan_ids: string[];
  source_context: string[];
  provenance_note: string | null;
  status: 'DRAFT' | 'PROPOSED' | 'CANONICAL' | 'SUPERSEDED' | 'REJECTED' | 'ARCHIVED';
}

export interface ManuscriptDocument {
  document_id: string;
  project_id: string;
  title: string;
  content: string;
  chapter_id: string | null;
  scene_id: string | null;
  current_draft_artifact_id: string | null;
  version: number;
}

export interface PromoteDraftToManuscriptRequest {
  project_id: string;
  document_id: string;
  draft_artifact_id: string;
  title?: string;
  chapter_id?: string;
  scene_id?: string;
  version?: number;
}
