import type { ModelCatalog, RoleModelCheckStatus, RoleModelCheckRequest } from '../types/checker';

export async function getModelCatalog(): Promise<ModelCatalog> {
  const response = await fetch('/api/models');
  
  if (!response.ok) {
    throw new Error(`Failed to fetch model catalog: ${response.statusText}`);
  }

  return response.json();
}

export async function runChecker(request: RoleModelCheckRequest): Promise<RoleModelCheckStatus> {
  const response = await fetch('/api/role-model-checker/run', {
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
  const response = await fetch(`/api/role-model-checker/${runId}/status`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch checker status: ${response.statusText}`);
  }

  return response.json();
}

export async function retryChecker(runId: string): Promise<RoleModelCheckStatus> {
  const response = await fetch(`/api/role-model-checker/${runId}/retry`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to retry checker: ${response.statusText}`);
  }

  return response.json();
}
