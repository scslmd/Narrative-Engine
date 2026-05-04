export interface ExportMetadata {
  export_version: number;
  engine_version: string;
  created_at: string;
  original_project_id: string;
  original_project_name: string;
}

export interface ExportImportSubmitResponse {
  import_id: string;
  status: string;
}

export interface ExportImportProgressResponse {
  import_id: string;
  status: string;
  phase: string | null;
  export_version: number | null;
  created_at: string | null;
  original_project_id: string | null;
  result: {
    project_id: string;
    project_name: string;
    export_version: number;
  } | null;
  error: string | null;
}
