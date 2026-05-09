/**
 * Storyboard Service
 *
 * Service for interacting with storyboard card API endpoints:
 * - List and create storyboard cards
 */

import type {
  StoryboardCard,
  StoryboardCardCreateRequest,
  StoryboardCardUpdateRequest,
} from '../types/planning';
import api from '../lib/api';

interface StoryboardListResponse {
  project_id: string;
  items: StoryboardCard[];
  meta: Record<string, string>;
}

/**
 * Get all storyboard cards for a project
 */
export async function getStoryboardCards(projectId: string): Promise<StoryboardCard[]> {
  const response = await api.get('/v1/story-development/storyboard/cards', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch storyboard cards: ${response.status}`);
  }

  const data: StoryboardListResponse = response.data;
  return data.items;
}

/**
 * Create a new storyboard card
 */
export async function createStoryboardCard(
  projectId: string,
  data: StoryboardCardCreateRequest,
): Promise<StoryboardCard> {
  const response = await api.post('/v1/story-development/storyboard/cards', data, {
    params: { project_id: projectId },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create storyboard card: ${response.status}`);
  }

  return response.data;
}

/**
 * Update an existing storyboard card
 */
export async function updateStoryboardCard(
  cardId: string,
  data: StoryboardCardUpdateRequest,
  projectId?: string,
): Promise<StoryboardCard> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;

  const response = await api.patch(`/v1/story-development/storyboard/cards/${cardId}`, data, { params });

  if (response.status !== 200) {
    throw new Error(`Failed to update storyboard card ${cardId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Delete a storyboard card
 */
export async function deleteStoryboardCard(
  cardId: string,
  projectId?: string,
): Promise<void> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;

  const response = await api.delete(`/v1/story-development/storyboard/cards/${cardId}`, { params });

  if (response.status !== 204) {
    throw new Error(`Failed to delete storyboard card ${cardId}: ${response.status}`);
  }
}

/**
 * Reindex cards within a column (drag-drop reorder)
 */
export async function reindexColumn(
  columnId: string,
  orderedIds: string[],
  projectId?: string,
): Promise<StoryboardCard[]> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;

  const response = await api.put(
    `/v1/story-development/storyboard/cards/${columnId}/reindex`,
    { card_ids: orderedIds },
    { params },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to reindex column ${columnId}: ${response.status}`);
  }

  const data = response.data;
  return data.items;
}
