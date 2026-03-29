/**
 * World Bible Service
 * 
 * Service for interacting with world bible-related API endpoints:
 * - List world bible entries
 * - Get world bible entry
 * - Create world bible entry
 * - Update world bible entry
 * 
 * Backend endpoints:
 * - GET /story-development/world-bible
 * - GET /story-development/world-bible/{entry_type}/{title}
 * - POST /story-development/world-bible
 * - PATCH /story-development/world-bible/{entry_type}/{title}
 */

import type {
  WorldBibleEntry,
  WorldBibleEntryType,
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
 * Get world bible entries filtered by type
 */
export async function getWorldBibleEntriesByType(
  projectId: string,
  entryType: WorldBibleEntryType,
): Promise<WorldBibleEntry[]> {
  const allEntries = await getWorldBibleEntries(projectId);
  return allEntries.filter((entry) => entry.entry_type === entryType);
}

/**
 * Get a specific world bible entry by type and title
 */
export async function getWorldBibleEntry(
  entryType: WorldBibleEntryType,
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
 * Update a world bible entry
 */
export async function updateWorldBibleEntry(
  entryType: WorldBibleEntryType,
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

/**
 * Get world bible entries grouped by type
 */
export function groupEntriesByType(
  entries: WorldBibleEntry[],
): Record<WorldBibleEntryType, WorldBibleEntry[]> {
  return entries.reduce((acc, entry) => {
    if (!acc[entry.entry_type]) {
      acc[entry.entry_type] = [];
    }
    acc[entry.entry_type].push(entry);
    return acc;
  }, {} as Record<WorldBibleEntryType, WorldBibleEntry[]>);
}

/**
 * Get entries that reference a specific character
 */
export function getEntriesForCharacter(
  entries: WorldBibleEntry[],
  characterId: string,
): WorldBibleEntry[] {
  return entries.filter((entry) => entry.related_character_ids.includes(characterId));
}

/**
 * Check if an entry has continuity warnings
 */
export function hasContinuityWarnings(entry: WorldBibleEntry): boolean {
  return entry.continuity_warnings.length > 0;
}

/**
 * Get all entries with continuity warnings
 */
export function getEntriesWithWarnings(entries: WorldBibleEntry[]): WorldBibleEntry[] {
  return entries.filter((entry) => entry.continuity_warnings.length > 0);
}

/**
 * Get unique entry types from a list of entries
 */
export function getUniqueEntryTypes(entries: WorldBibleEntry[]): WorldBibleEntryType[] {
  return Array.from(new Set(entries.map((entry) => entry.entry_type)));
}
