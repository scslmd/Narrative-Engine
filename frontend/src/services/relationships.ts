/**
 * Relationships Service
 * 
 * Service for interacting with character relationship API endpoints:
 * - List all relationships for a project
 * - Delete a relationship
 * 
 * Backend endpoints:
 * - GET /story-development/relationships
 * - DELETE /story-development/relationships/{edge_id}
 */

import type {
  RelationshipEdge,
  RelationshipEdgeListResponse,
} from '../types/characters';
import api from '../lib/api';

/**
 * Get all relationships for a project
 */
export async function getRelationships(projectId: string): Promise<RelationshipEdge[]> {
  const response = await api.get('/story-development/relationships', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch relationships: ${response.status}`);
  }

  const data: RelationshipEdgeListResponse = response.data;
  return data.items;
}

/**
 * Delete a relationship edge
 */
export async function deleteRelationship(
  edgeId: string,
  projectId: string,
): Promise<void> {
  const response = await api.delete(
    `/story-development/relationships/${edgeId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to delete relationship ${edgeId}: ${response.status}`);
  }
}
