/**
 * World Bible Service
 * 
 * Service for interacting with world bible-related API endpoints:
 * - List world bible entries
 * - Create world bible entry
 * - Update world bible entry
 * 
 * Backend endpoints:
 * - GET /story-development/world-bible
 * - POST /story-development/world-bible
 * - PATCH /story-development/world-bible/{entry_type}/{title}
 */

import type {
  WorldBibleEntry,
  WorldBibleEntryCreateRequest,
  WorldBibleEntryUpdateRequest,
  WorldBibleEntryListResponse,
} from '../types/bible';
import api from '../lib/api';

/**
 * Get all world bible entries for a project
 */
export async function getWorldBibleEntries(projectId: string): Promise<WorldBibleEntry[]> {
  const response = await api.get('/story-development/world-bible', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch world bible entries: ${response.status}`);
  }

  const data: WorldBibleEntryListResponse = response.data;
  return data.items;
}

/**
 * Create a new world bible entry
 */
export async function createWorldBibleEntry(
  request: WorldBibleEntryCreateRequest,
): Promise<WorldBibleEntry> {
  const response = await api.post('/story-development/world-bible', request);

  if (response.status !== 201) {
    throw new Error(`Failed to create world bible entry: ${response.status}`);
  }

  return response.data;
}

/**
 * Get a single world bible entry by type and title
 */
export async function getWorldBibleEntry(
  entryType: string,
  title: string,
  projectId: string,
): Promise<WorldBibleEntry> {
  const response = await api.get(
    `/story-development/world-bible/${entryType}/${encodeURIComponent(title)}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch world bible entry ${entryType}/${title}: ${response.status}`);
  }

  return response.data;
}

/**
 * Update a world bible entry
 */
export async function updateWorldBibleEntry(
  entryType: string,
  title: string,
  projectId: string,
  updates: WorldBibleEntryUpdateRequest,
): Promise<WorldBibleEntry> {
  const response = await api.patch(
    `/story-development/world-bible/${entryType}/${encodeURIComponent(title)}`,
    updates,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update world bible entry ${entryType}/${title}: ${response.status}`);
  }

  return response.data;
}
