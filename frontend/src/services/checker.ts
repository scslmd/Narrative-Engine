import type { ModelCatalog, RoleModelCheckStatus, RoleModelCheckRequest } from '../types/checker';
import api from '../lib/api';

export async function getModelCatalog(): Promise<ModelCatalog> {
  const response = await api.get('/models');
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch model catalog: ${response.status}`);
  }

  return response.data;
}

export async function runChecker(request: RoleModelCheckRequest): Promise<RoleModelCheckStatus> {
  const response = await api.post('/role-model-checker/run', request);

  if (response.status !== 201) {
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

  if (response.status !== 201) {
    throw new Error(`Failed to retry checker: ${response.status}`);
  }

  return response.data;
}
