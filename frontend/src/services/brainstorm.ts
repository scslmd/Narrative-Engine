/**
 * Brainstorm Service
 * 
 * Service for interacting with brainstorm-related API endpoints:
 * - List brainstorm items
 * - Create brainstorm items
 * - Cluster brainstorm items
 * - Promote brainstorm items
 * - List brainstorm promotions
 * 
 * Backend endpoints:
 * - GET /story-development/brainstorm/items
 * - POST /story-development/brainstorm/items
 * - POST /story-development/brainstorm/items/cluster
 * - POST /story-development/brainstorm/items/promote
 * - GET /story-development/brainstorm/promotions
 */

import type {
  BrainstormItem,
  BrainstormPromotion,
  BrainstormItemCreateRequest,
  BrainstormItemClusterRequest,
  BrainstormItemPromoteRequest,
  BrainstormItemListResponse,
  BrainstormPromotionListResponse,
} from '../types/brainstorm';
import api from '../lib/api';

/**
 * Get all brainstorm items for a project
 */
export async function getBrainstormItems(projectId: string): Promise<BrainstormItem[]> {
  const response = await api.get('/story-development/brainstorm/items', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch brainstorm items: ${response.status}`);
  }

  const data: BrainstormItemListResponse = response.data;
  return data.items;
}

/**
 * Create a new brainstorm item
 */
export async function createBrainstormItem(
  request: BrainstormItemCreateRequest,
): Promise<BrainstormItem> {
  const response = await api.post('/story-development/brainstorm/items', request);

  if (response.status !== 201) {
    throw new Error(`Failed to create brainstorm item: ${response.status}`);
  }

  return response.data;
}

/**
 * Cluster multiple brainstorm items together
 */
export async function clusterBrainstormItems(
  request: BrainstormItemClusterRequest,
): Promise<BrainstormItem[]> {
  const response = await api.post('/story-development/brainstorm/items/cluster', request);

  if (response.status !== 200) {
    throw new Error(`Failed to cluster brainstorm items: ${response.status}`);
  }

  return response.data;
}

/**
 * Promote a brainstorm item to a target object
 */
export async function promoteBrainstormItem(
  request: BrainstormItemPromoteRequest,
): Promise<BrainstormPromotion> {
  const response = await api.post('/story-development/brainstorm/items/promote', request);

  if (response.status !== 201) {
    throw new Error(`Failed to promote brainstorm item: ${response.status}`);
  }

  return response.data;
}

/**
 * Get all brainstorm promotions for a project
 */
export async function getBrainstormPromotions(projectId: string): Promise<BrainstormPromotion[]> {
  const response = await api.get('/story-development/brainstorm/promotions', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch brainstorm promotions: ${response.status}`);
  }

  const data: BrainstormPromotionListResponse = response.data;
  return data.items;
}

/**
 * Get promotions for a specific brainstorm item
 */
export function getPromotionsForItem(
  promotions: BrainstormPromotion[],
  itemId: string,
): BrainstormPromotion[] {
  return promotions.filter((p) => p.source_item_ids.includes(itemId));
}

/**
 * Check if a brainstorm item has been promoted
 */
export function isItemPromoted(
  promotions: BrainstormPromotion[],
  itemId: string,
): boolean {
  return promotions.some((p) => p.source_item_ids.includes(itemId));
}
