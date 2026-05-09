/**
 * Characters Service
 *
 * Service for interacting with character-related API endpoints:
 * - List character profiles
 * - Get single character profile
 * - Create character profile
 * - Update character profile
 * - Get character relationships
 *
 * Backend endpoints:
 * - GET /v1/story-development/characters
 * - GET /v1/story-development/characters/{character_id}
 * - POST /v1/story-development/characters
 * - PATCH /v1/story-development/characters/{character_id}
 * - GET /v1/story-development/characters/{character_id}/relationships
 */

import type {
  CharacterProfile,
  CharacterProfileCreateRequest,
  CharacterProfileUpdateRequest,
  CharacterProfileListResponse,
  RelationshipEdge,
  RelationshipEdgeListResponse,
} from '../types/characters';
import api from '../lib/api';

/**
 * Get all character profiles for a project
 */
export async function getCharacters(projectId: string): Promise<CharacterProfile[]> {
  const response = await api.get('/v1/story-development/characters', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch characters: ${response.status}`);
  }

  const data: CharacterProfileListResponse = response.data;
  return data.items;
}

/**
 * Create a new character profile
 */
export async function createCharacter(
  request: CharacterProfileCreateRequest,
): Promise<CharacterProfile> {
  const response = await api.post('/v1/story-development/characters', request);

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
    `/v1/story-development/characters/${characterId}`,
    updates,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update character ${characterId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Get a single character profile by ID
 */
export async function getCharacter(
  characterId: string,
  projectId: string,
): Promise<CharacterProfile> {
  const response = await api.get(
    `/v1/story-development/characters/${characterId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch character ${characterId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Get relationships for a character
 */
export async function getCharacterRelationships(
  characterId: string,
  projectId: string,
): Promise<RelationshipEdge[]> {
  const response = await api.get(
    `/v1/story-development/characters/${characterId}/relationships`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch relationships for ${characterId}: ${response.status}`);
  }

  const data: RelationshipEdgeListResponse = response.data;
  return data.items;
}

