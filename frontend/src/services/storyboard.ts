/**
 * Storyboard Service
 *
 * Service for interacting with storyboard card API endpoints:
 * - List and create storyboard cards
 */

import type {
  StoryboardCard,
  StoryboardCardCreateRequest,
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
