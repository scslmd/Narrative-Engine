/**
 * Storyboard Service
 *
 * Service for interacting with storyboard card API endpoints:
 * - CRUD operations for storyboard cards
 * - Reindexing card order
 */

import type {
  StoryboardCard,
  StoryboardCardCreateRequest,
  StoryboardCardUpdateRequest,
  StoryboardCardReindexRequest,
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
  const response = await api.get('/storyboard/cards', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch storyboard cards: ${response.status}`);
  }

  const data: StoryboardListResponse = response.data;
  return data.items;
}

/**
 * Get a specific storyboard card by ID
 */
export async function getStoryboardCard(cardId: string, projectId: string): Promise<StoryboardCard> {
  const response = await api.get(
    `/storyboard/cards/${cardId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch storyboard card ${cardId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Create a new storyboard card
 */
export async function createStoryboardCard(
  projectId: string,
  data: StoryboardCardCreateRequest,
): Promise<StoryboardCard> {
  const response = await api.post('/storyboard/cards', data, {
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
  projectId: string,
  data: StoryboardCardUpdateRequest,
): Promise<StoryboardCard> {
  const response = await api.patch(
    `/storyboard/cards/${cardId}`,
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update storyboard card ${cardId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Delete a storyboard card
 */
export async function deleteStoryboardCard(cardId: string, projectId: string): Promise<void> {
  const response = await api.delete(
    `/storyboard/cards/${cardId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 204) {
    throw new Error(`Failed to delete storyboard card ${cardId}: ${response.status}`);
  }
}

/**
 * Reindex storyboard cards by new card order
 */
export async function reindexStoryboardCards(
  projectId: string,
  data: StoryboardCardReindexRequest,
): Promise<void> {
  const response = await api.post(
    `/storyboard/cards/reindex`,
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to reindex storyboard cards: ${response.status}`);
  }
}
