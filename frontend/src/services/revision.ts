import type {
  RevisionChecklistItem,
  RevisionPass,
  RevisionPassCreateRequest,
  RevisionPassListResponse,
  RevisionPassUpdateRequest,
} from '../types/revision';
import api from '../lib/api';

export async function getRevisionPasses(
  projectId: string,
  params?: { pass_type?: string; status?: string },
): Promise<RevisionPass[]> {
  const response = await api.get('/story-development/revision/passes', {
    params: { project_id: projectId, ...params },
  });

  const data: RevisionPassListResponse = response.data;
  return data.items;
}

export async function getRevisionPass(
  passId: string,
  projectId: string,
): Promise<RevisionPass> {
  const response = await api.get(`/story-development/revision/passes/${passId}`, {
    params: { project_id: projectId },
  });

  return response.data;
}

export async function createRevisionPass(
  request: RevisionPassCreateRequest,
): Promise<RevisionPass> {
  const response = await api.post('/story-development/revision/passes', request);

  return response.data;
}

export async function updateRevisionPass(
  passId: string,
  projectId: string,
  request: RevisionPassUpdateRequest,
): Promise<RevisionPass> {
  const response = await api.patch(`/story-development/revision/passes/${passId}`, request, {
    params: { project_id: projectId },
  });

  return response.data;
}

export async function completeRevisionPass(
  passId: string,
  projectId: string,
): Promise<RevisionPass> {
  const response = await api.post(`/story-development/revision/passes/${passId}/complete`, null, {
    params: { project_id: projectId },
  });

  return response.data;
}

export async function getChecklist(passType: string): Promise<RevisionChecklistItem[]> {
  const response = await api.get(`/story-development/revision/checklists/${passType}`);

  return response.data;
}
