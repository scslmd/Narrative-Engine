export interface RevisionChecklistItem {
  item_id: string;
  label: string;
  done: boolean;
}

export interface RevisionPass {
  pass_id: string;
  project_id: string;
  pass_type: string;
  status: string;
  checklist: RevisionChecklistItem[];
  notes: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface RevisionPassCreateRequest {
  project_id: string;
  pass_type: string;
  status?: string;
  notes?: string | null;
}

export interface RevisionPassUpdateRequest {
  status?: string;
  notes?: string | null;
  checklist?: RevisionChecklistItem[];
}

export interface RevisionPassListResponse {
  project_id: string;
  items: RevisionPass[];
  meta: Record<string, string>;
}
