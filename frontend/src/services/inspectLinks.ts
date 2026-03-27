import type { InspectRunLink } from '../types/inspectLinks';
import api from '../lib/api';

interface InspectLinkListResponse {
  project_id: string;
  items: InspectRunLink[];
  meta: Record<string, string>;
}

export async function getInspectLinks(projectId?: string, findingId?: string, runId?: string): Promise<InspectRunLink[]> {
  const params: Record<string, string> = {};
  
  if (projectId) params.project_id = projectId;
  if (findingId) params.finding_id = findingId;
  if (runId) params.run_id = runId;

  const response = await api.get('/story-development/review/inspect-links', { params });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch inspect links: ${response.status}`);
  }

  const data: InspectLinkListResponse = response.data;
  return data.items;
}

export async function getInspectLink(linkId: string): Promise<InspectRunLink> {
  const response = await api.get(`/story-development/review/inspect-links/${linkId}`);
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch inspect link: ${response.status}`);
  }

  return response.data;
}
