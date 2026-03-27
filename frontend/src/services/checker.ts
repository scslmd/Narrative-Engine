import type { ModelCatalog, RoleModelCheckStatus, RoleModelCheckRequest } from '../types/checker';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getModelCatalog(): Promise<ModelCatalog> {
  const response = await fetch(`${API_BASE}/v1/models`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch model catalog: ${response.statusText}`);
  }

  return response.json();
}

export async function runChecker(request: RoleModelCheckRequest): Promise<RoleModelCheckStatus> {
  const response = await fetch(`${API_BASE}/v1/role-model-checker/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to run checker: ${response.statusText}`);
  }

  return response.json();
}

export async function getCheckerStatus(runId: string): Promise<RoleModelCheckStatus> {
  const response = await fetch(`${API_BASE}/v1/role-model-checker/${runId}/status`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch checker status: ${response.statusText}`);
  }

  return response.json();
}

export async function retryChecker(runId: string): Promise<RoleModelCheckStatus> {
  const response = await fetch(`${API_BASE}/v1/role-model-checker/${runId}/retry`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to retry checker: ${response.statusText}`);
  }

  return response.json();
}
