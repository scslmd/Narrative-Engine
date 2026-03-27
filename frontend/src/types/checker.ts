export interface ModelCatalog {
  workflow_order: string[];
  discovered_models: Array<{
    role: string;
    model_id: string;
    name: string;
    description?: string;
  }>;
}

export type CheckerStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface RoleModelCheckStatus {
  run_id: string;
  status: CheckerStatus;
  attempt_number: number;
  progress_current?: number;
  progress_total?: number;
  error?: string;
}

export interface RoleModelCheckRequest {
  project_id: string;
  models: Record<string, string>;
}
