/**
 * Characters Service
 * 
 * Service for interacting with character-related API endpoints:
 * - List character profiles
 * - Create character profile
 * - Update character profile
 * 
 * Backend endpoints:
 * - GET /story-development/characters
 * - POST /story-development/characters
 * - PATCH /story-development/characters/{character_id}
 */

import type {
  CharacterProfile,
  CharacterProfileCreateRequest,
  CharacterProfileUpdateRequest,
  CharacterProfileListResponse,
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
