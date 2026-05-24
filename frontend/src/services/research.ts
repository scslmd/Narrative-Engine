import type {
  ResearchItem,
  ResearchItemCreateRequest,
  ResearchItemListResponse,
  ResearchItemUpdateRequest,
} from '../types/research';
import api from '../lib/api';

export async function getResearchItems(
  projectId: string,
  params?: { status?: string; genre_tag?: string },
): Promise<ResearchItem[]> {
  const response = await api.get('/story-development/research/items', {
    params: { project_id: projectId, ...params },
  });

  const data: ResearchItemListResponse = response.data;
  return data.items;
}

export async function getResearchItem(
  itemId: string,
  projectId: string,
): Promise<ResearchItem> {
  const response = await api.get(`/story-development/research/items/${itemId}`, {
    params: { project_id: projectId },
  });

  return response.data;
}

export async function createResearchItem(
  request: ResearchItemCreateRequest,
): Promise<ResearchItem> {
  const response = await api.post('/story-development/research/items', request);

  return response.data;
}

export async function updateResearchItem(
  itemId: string,
  projectId: string,
  request: ResearchItemUpdateRequest,
): Promise<ResearchItem> {
  const response = await api.patch(`/story-development/research/items/${itemId}`, request, {
    params: { project_id: projectId },
  });

  return response.data;
}

export async function deleteResearchItem(
  itemId: string,
  projectId: string,
): Promise<void> {
  await api.delete(`/story-development/research/items/${itemId}`, {
    params: { project_id: projectId },
  });
}
