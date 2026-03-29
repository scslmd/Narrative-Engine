/**
 * Characters Service
 * 
 * Service for interacting with character-related API endpoints:
 * - List character profiles
 * - Get character profile
 * - Create character profile
 * - Update character profile
 * - Get character relationships
 * - Create relationship
 * 
 * Backend endpoints:
 * - GET /story-development/characters
 * - GET /story-development/characters/{character_id}
 * - POST /story-development/characters
 * - PATCH /story-development/characters/{character_id}
 * - GET /story-development/characters/{character_id}/relationships
 * - POST /story-development/relationships
 */

import type {
  CharacterProfile,
  RelationshipEdge,
  CharacterProfileCreateRequest,
  CharacterProfileUpdateRequest,
  RelationshipEdgeCreateRequest,
  CharacterProfileListResponse,
  RelationshipEdgeListResponse,
} from '../types/characters';
import api from '../lib/api';

/**
 * Get all character profiles for a project
 */
export async function getCharacters(projectId: string): Promise<CharacterProfile[]> {
  const response = await api.get('/story-development/characters', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch characters: ${response.status}`);
  }

  const data: CharacterProfileListResponse = response.data;
  return data.items;
}

/**
 * Get a specific character profile by ID
 */
export async function getCharacter(characterId: string, projectId: string): Promise<CharacterProfile> {
  const response = await api.get(
    `/story-development/characters/${characterId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch character ${characterId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Create a new character profile
 */
export async function createCharacter(
  request: CharacterProfileCreateRequest,
): Promise<CharacterProfile> {
  const response = await api.post('/story-development/characters', request);

  if (response.status !== 201) {
    throw new Error(`Failed to create character: ${response.status}`);
  }

  return response.data;
}

/**
 * Update a character profile
 */
export async function updateCharacter(
  characterId: string,
  projectId: string,
  updates: CharacterProfileUpdateRequest,
): Promise<CharacterProfile> {
  const response = await api.patch(
    `/story-development/characters/${characterId}`,
    updates,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update character ${characterId}: ${response.status}`);
  }

  return response.data;
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
  const request: RelationshipEdgeCreateRequest = {
    project_id: projectId,
    source_character_id: edge.source_character_id,
    target_character_id: edge.target_character_id,
    relation_kind: edge.relation_kind,
    summary: edge.summary,
    tension: edge.tension,
    notes: edge.notes,
  };

  const response = await api.post('/story-development/relationships', request);

  if (response.status !== 201) {
    throw new Error(`Failed to create relationship: ${response.status}`);
  }

  return response.data;
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
