import type { ModelCatalog, RoleModelCheckStatus, RoleModelCheckRequest } from '../types/checker';
import api from '../lib/api';

export async function getModelCatalog(): Promise<ModelCatalog> {
  const response = await api.get('/models');

  if (response.status !== 200) {
    throw new Error(`Failed to fetch model catalog: ${response.status}`);
  }

  const raw = response.data;

  // Backend returns discovered_models as list[str] (model ID strings).
  // Transform into Array<{role, model_id, name}> expected by the component.
  // Already-shaped objects (from tests/legacy) pass through unchanged.
  const rawModels = Array.isArray(raw.discovered_models) ? raw.discovered_models : [];
  const roles = Array.isArray(raw.workflow_order) ? raw.workflow_order : [];

  if (rawModels.length > 0 && typeof rawModels[0] === 'object' && 'model_id' in rawModels[0]) {
    return {
      workflow_order: roles,
      discovered_models: rawModels as Array<{ role: string; model_id: string; name: string }>,
    };
  }

  // Backend format: list of model ID strings. Expand into per-role entries.
  const models: Array<{ role: string; model_id: string; name: string }> = [];
  for (const roleId of roles) {
    for (const modelId of rawModels) {
      const id = String(modelId);
      models.push({
        role: roleId,
        model_id: id,
        name: id.replace(/\.gguf$/i, '').replace(/[-_]/g, ' '),
      });
    }
  }

  return {
    workflow_order: roles,
    discovered_models: models,
  };
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

export async function getCheckerAttempts(runId: string): Promise<{ run_id: string; items: AttemptHistoryItem[]; meta: Record<string, string> }> {
  const response = await api.get(`/role-model-checker/${runId}/attempts`);
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch checker attempts: ${response.status}`);
  }

  return response.data;
}

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
