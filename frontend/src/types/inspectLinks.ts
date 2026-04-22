export interface InspectRunLink {
  link_id: string;
  project_id: string;
  object_kind: string;
  object_id: string;
  logical_run_id: string;
  run_id: string;
  run_kind: string;
  attempt_number: number | null;
  label: string | null;
}

export interface InspectRunLinkCreateRequest {
  link_id: string;
  project_id: string;
  object_kind: string;
  object_id: string;
  logical_run_id: string;
  run_id: string;
  run_kind: string;
  attempt_number?: number | null;
  label?: string | null;
}
