import type { InspectRunLink } from '../types/inspectLinks';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface InspectLinkListResponse {
  project_id: string;
  items: InspectRunLink[];
  meta: Record<string, string>;
}

export async function getInspectLinks(projectId?: string, findingId?: string, runId?: string): Promise<InspectRunLink[]> {
  const params = new URLSearchParams();
  
  if (projectId) params.append('project_id', projectId);
  if (findingId) params.append('finding_id', findingId);
  if (runId) params.append('run_id', runId);

  const url = `${API_BASE}/v1/story-development/review/inspect-links${params.toString() ? '?' + params.toString() : ''}`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch inspect links: ${response.statusText}`);
  }

  const data: InspectLinkListResponse = await response.json();
  return data.items;
}

export async function getInspectLink(linkId: string): Promise<InspectRunLink> {
  const response = await fetch(`${API_BASE}/v1/story-development/review/inspect-links/${linkId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch inspect link: ${response.statusText}`);
  }

  return response.json();
}
