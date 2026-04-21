/**
 * Relationships Service
 * 
 * Service for interacting with character relationship API endpoints:
 * - List all relationships for a project
 * - Get relationships for a specific character
 * - Create a relationship
 * - Update a relationship
 * - Delete a relationship
 * 
 * Backend endpoints:
 * - GET /story-development/relationships
 * - GET /story-development/characters/{character_id}/relationships
 * - POST /story-development/relationships
 * - PATCH /story-development/relationships/{edge_id}
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
 * Get relationships for a specific character
 */
export async function getCharacterRelationships(
  characterId: string,
  projectId: string,
): Promise<RelationshipEdge[]> {
  const response = await api.get(
    `/story-development/characters/${characterId}/relationships`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch relationships for character ${characterId}: ${response.status}`);
  }

  const data: RelationshipEdgeListResponse = response.data;
  return data.items;
}

/**
 * Create a relationship between two characters
 */
export async function createRelationship(
  projectId: string,
  edge: Omit<RelationshipEdge, 'edge_id'>,
): Promise<RelationshipEdge> {
  const response = await api.post('/story-development/relationships', {
    project_id: projectId,
    source_character_id: edge.source_character_id,
    target_character_id: edge.target_character_id,
    relation_kind: edge.relation_kind,
    summary: edge.summary,
    tension: edge.tension,
    notes: edge.notes,
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create relationship: ${response.status}`);
  }

  return response.data;
}

/**
 * Update a relationship edge
 */
export async function updateRelationship(
  edgeId: string,
  projectId: string,
  updates: Pick<
    RelationshipEdge,
    'relation_kind' | 'summary' | 'tension' | 'notes'
  >,
): Promise<RelationshipEdge> {
  const response = await api.patch(
    `/story-development/relationships/${edgeId}`,
    updates,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update relationship ${edgeId}: ${response.status}`);
  }

  return response.data;
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

/**
 * Get all relationships where a character is involved (as source or target)
 */
export function getRelationshipsForCharacter(
  relationships: RelationshipEdge[],
  characterId: string,
): RelationshipEdge[] {
  return relationships.filter(
    (rel) => rel.source_character_id === characterId || rel.target_character_id === characterId,
  );
}

/**
 * Get outgoing relationships (where character is the source)
 */
export function getOutgoingRelationships(
  relationships: RelationshipEdge[],
  characterId: string,
): RelationshipEdge[] {
  return relationships.filter((rel) => rel.source_character_id === characterId);
}

/**
 * Get incoming relationships (where character is the target)
 */
export function getIncomingRelationships(
  relationships: RelationshipEdge[],
  characterId: string,
): RelationshipEdge[] {
  return relationships.filter((rel) => rel.target_character_id === characterId);
}

/**
 * Get the related character for a given relationship edge
 */
export function getRelatedCharacter(
  edge: RelationshipEdge,
  characterId: string,
): string {
  return edge.source_character_id === characterId
    ? edge.target_character_id
    : edge.source_character_id;
}

/**
 * Check if two characters have a relationship
 */
export function hasRelationship(
  relationships: RelationshipEdge[],
  characterId1: string,
  characterId2: string,
): boolean {
  return relationships.some(
    (rel) =>
      (rel.source_character_id === characterId1 && rel.target_character_id === characterId2) ||
      (rel.source_character_id === characterId2 && rel.target_character_id === characterId1),
  );
}
