import type { ModelCatalog, RoleModelCheckStatus, RoleModelCheckRequest } from '../types/checker';
import api from '../lib/api';

export interface AttemptHistoryItem {
  attempt_number: number;
  status: string;
  executor_name: string | null;
  executor_instance_id: string | null;
  queue_delay_ms: number | null;
  lease_owner: string | null;
  lease_expires_at: string | null;
  claimed_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  last_heartbeat_at: string | null;
  finish_reason: string | null;
  failure_stage: string | null;
  retryable: boolean | null;
  retry_reason: string | null;
  error_code: string | null;
  error_category: string | null;
}

export interface RoleModelCheckAttemptHistoryResponse {
  run_id: string;
  items: AttemptHistoryItem[];
  meta: Record<string, string>;
}

export async function getModelCatalog(): Promise<ModelCatalog> {
  const response = await api.get('/models');
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch model catalog: ${response.status}`);
  }

  return response.data;
}

export async function runChecker(request: RoleModelCheckRequest): Promise<RoleModelCheckStatus> {
  const response = await api.post('/role-model-checker/run', request);

  if (response.status !== 202 && response.status !== 200) {
    throw new Error(`Failed to run checker: ${response.status}`);
  }

  return response.data;
}

export async function getCheckerStatus(runId: string): Promise<RoleModelCheckStatus> {
  const response = await api.get(`/role-model-checker/${runId}/status`);
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch checker status: ${response.status}`);
  }

  return response.data;
}

export async function retryChecker(runId: string): Promise<RoleModelCheckStatus> {
  const response = await api.post(`/role-model-checker/${runId}/retry`);

  if (response.status !== 202) {
    throw new Error(`Failed to retry checker: ${response.status}`);
  }

  return response.data;
}

export async function getCheckerAttempts(runId: string): Promise<RoleModelCheckAttemptHistoryResponse> {
  const response = await api.get(`/role-model-checker/${runId}/attempts`);
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch checker attempts: ${response.status}`);
  }

  return response.data;
}
