/**
 * Brainstorm Service
 * 
 * Service for interacting with brainstorm-related API endpoints:
 * - List brainstorm items
 * - Create brainstorm items
 * - Cluster brainstorm items
 * 
 * Backend endpoints:
 * - GET /story-development/brainstorm/items
 * - POST /story-development/brainstorm/items
 * - POST /story-development/brainstorm/items/cluster
 */

import type {
  BrainstormItem,
  BrainstormItemCreateRequest,
  BrainstormItemClusterRequest,
  BrainstormItemListResponse,
  BrainstormPromotionResult,
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
 * Promote a brainstorm item to a target entity (character, world bible entry, arc)
 */
export async function promoteBrainstormItem(
  itemId: string,
  projectId: string,
  targetKind: string,
  targetId: string,
): Promise<BrainstormPromotionResult> {
  const response = await api.post('/story-development/brainstorm/items/promote', {
    item_id: itemId,
    project_id: projectId,
    target_object_kind: targetKind,
    target_object_id: targetId,
  });

  if (response.status !== 201) {
    throw new Error(`Failed to promote brainstorm item: ${response.status}`);
  }

  return response.data;
}
