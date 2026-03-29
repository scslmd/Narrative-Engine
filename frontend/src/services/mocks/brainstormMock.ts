/**
 * FE-029: Brainstorm mock service
 * 
 * Provides deterministic mock data for brainstorm workspace.
 * Uses 2000ms delay and project-scoped in-memory storage.
 */

import type { BrainstormItem, BrainstormItemCreateRequest, BrainstormClusterRequest } from '../../types/brainstorm';

const DELAY_MS = 2000;

// In-memory storage scoped by project
const storage = new Map<string, BrainstormItem[]>();

function getItemsForProject(projectId: string): BrainstormItem[] {
  if (!storage.has(projectId)) {
    storage.set(projectId, []);
  }
  return storage.get(projectId) || [];
}

function setItemsForProject(projectId: string, items: BrainstormItem[]): void {
  storage.set(projectId, items);
}

export async function getBrainstormItems(projectId: string): Promise<BrainstormItem[]> {
  await new Promise(resolve => setTimeout(resolve, DELAY_MS));
  return getItemsForProject(projectId);
}

export async function createBrainstormItem(
  projectId: string,
  request: BrainstormItemCreateRequest,
): Promise<BrainstormItem> {
  await new Promise(resolve => setTimeout(resolve, DELAY_MS));
  
  const items = getItemsForProject(projectId);
  const newItem: BrainstormItem = {
    item_id: crypto.randomUUID(),
    project_id: projectId,
    content: request.content,
    item_type: request.item_type || 'IDEA',
    state: request.state || 'KEEP',
    tags: request.tags || [],
    cluster_id: request.cluster_id || null,
    promoted_to: null,
    promoted_at: null,
    created_at: new Date().toISOString(),
  };
  
  items.unshift(newItem);
  setItemsForProject(projectId, items);
  
  return newItem;
}

export async function clusterBrainstormItems(
  projectId: string,
  request: BrainstormClusterRequest,
): Promise<{ cluster_id: string; item_ids: string[] }> {
  await new Promise(resolve => setTimeout(resolve, DELAY_MS));
  
  const items = getItemsForProject(projectId);
  const clusterId = crypto.randomUUID();
  
  // Update items with matching IDs
  items.forEach(item => {
    if (request.item_ids.includes(item.item_id)) {
      item.cluster_id = clusterId;
    }
  });
  
  setItemsForProject(projectId, items);
  
  return { cluster_id: clusterId, item_ids: request.item_ids };
}

export async function promoteBrainstormItem(
  projectId: string,
  itemId: string,
  targetObjectType: string,
  targetObjectId?: string,
): Promise<{ success: boolean; target_object_id?: string }> {
  await new Promise(resolve => setTimeout(resolve, DELAY_MS));
  
  const items = getItemsForProject(projectId);
  const item = items.find(i => i.item_id === itemId);
  
  if (!item) {
    throw new Error(`Brainstorm item not found: ${itemId}`);
  }
  
  const targetObjectIdFinal = targetObjectId || crypto.randomUUID();
  
  item.promoted_to = targetObjectType;
  item.promoted_at = new Date().toISOString();
  
  setItemsForProject(projectId, items);
  
  return { success: true, target_object_id: targetObjectIdFinal };
}

export async function getPromotions(projectId: string): Promise<BrainstormItem[]> {
  await new Promise(resolve => setTimeout(resolve, DELAY_MS));
  const items = getItemsForProject(projectId);
  return items.filter(item => item.promoted_to !== null);
}
