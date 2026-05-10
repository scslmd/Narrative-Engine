import api from '../lib/api';
import type {
  CascadeScanRequest,
  CascadeJobResponse,
  StagedEntitiesResponse,
  CascadeApplyResponse,
  EntityApprovalUpdate,
} from '../types/discovery';

export async function submitScan(request: CascadeScanRequest): Promise<{ job_id: string; status: string }> {
  const response = await api.post('/v1/discovery/scan', request);
  return response.data;
}

export async function getJobStatus(jobId: string): Promise<CascadeJobResponse> {
  const response = await api.get(`/v1/discovery/jobs/${jobId}`);
  return response.data;
}

export async function getStagedEntities(stageId: string): Promise<StagedEntitiesResponse> {
  const response = await api.get(`/v1/discovery/staging/${stageId}`);
  return response.data;
}

export async function updateEntityApproval(stageId: string, updates: EntityApprovalUpdate[]): Promise<{ updated: number }> {
  const response = await api.patch(`/v1/discovery/staging/${stageId}/entities`, updates);
  return response.data;
}

export async function applyStagedEntities(stageId: string): Promise<CascadeApplyResponse> {
  const response = await api.post(`/v1/discovery/staging/${stageId}/apply`);
  return response.data;
}

export async function undoApply(stageId: string): Promise<{ stage_id: string; entities_reverted: number }> {
  const response = await api.post(`/v1/discovery/staging/${stageId}/undo`);
  return response.data;
}

export async function discardStaging(stageId: string): Promise<{ deleted: boolean }> {
  const response = await api.delete(`/v1/discovery/staging/${stageId}`);
  return response.data;
}
