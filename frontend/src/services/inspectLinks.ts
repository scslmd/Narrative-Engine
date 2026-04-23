import type { InspectRunLink, InspectRunLinkCreateRequest } from '../types/inspectLinks';
import api from '../lib/api';

interface InspectLinkListResponse {
  project_id: string;
  items: InspectRunLink[];
  meta: Record<string, string>;
}

export async function getInspectLinks(
  projectId?: string,
  objectKind?: string,
  objectId?: string,
  runId?: string,
): Promise<InspectRunLink[]> {
  const params: Record<string, string> = {};
  
  if (projectId) params.project_id = projectId;
  if (objectKind) params.object_kind = objectKind;
  if (objectId) params.object_id = objectId;
  if (runId) params.run_id = runId;

  const response = await api.get('/story-development/review/inspect-links', { params });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch inspect links: ${response.status}`);
  }

  const data: InspectLinkListResponse = response.data;
  return data.items;
}

export async function createInspectLink(data: InspectRunLinkCreateRequest): Promise<InspectRunLink> {
  const response = await api.post('/story-development/review/inspect-links', data, {
    params: { project_id: data.project_id },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create inspect link: ${response.status}`);
  }

  return response.data;
}
