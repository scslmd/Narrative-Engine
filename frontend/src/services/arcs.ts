/**
 * Arcs Service
 * 
 * Service for interacting with arcs-related API endpoints:
 * - Arc candidates
 * - Arc selections
 * - Arc stage mappings
 */

import type {
  ArcCandidate,
  ArcSelection,
  ArcStageMap,
  ArcComparisonRecord,
  ArcCandidateCreateRequest,
  ArcSelectionCreateRequest,
  ArcSelectionUpdateRequest,
  ArcStageMapCreateRequest,
} from '../types/arcs';
import api from '../lib/api';

interface ArcsListResponse<T> {
  project_id: string;
  items: T[];
  meta: Record<string, string>;
}

/**
 * Get all arc candidates for a project
 */
export async function getArcCandidates(projectId: string): Promise<ArcCandidate[]> {
  const response = await api.get('/v1/story-development/arcs/candidates', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch arc candidates: ${response.status}`);
  }

  const data: ArcsListResponse<ArcCandidate> = response.data;
  return data.items;
}

/**
 * Get all arc comparisons for a project
 */
export async function getArcComparisons(projectId: string): Promise<ArcComparisonRecord[]> {
  const response = await api.get('/v1/story-development/arcs/comparisons', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch arc comparisons: ${response.status}`);
  }

  const data: ArcsListResponse<ArcComparisonRecord> = response.data;
  return data.items;
}

/**
 * Get all arc selections for a project
 */
export async function getArcSelections(projectId: string): Promise<ArcSelection[]> {
  const response = await api.get('/v1/story-development/arcs/selections', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch arc selections: ${response.status}`);
  }

  const data: ArcsListResponse<ArcSelection> = response.data;
  return data.items;
}

/**
 * Get all arc stage mappings for a project
 */
export async function getArcStageMaps(projectId: string): Promise<ArcStageMap[]> {
  const response = await api.get('/v1/story-development/arcs/stage-maps', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch arc stage maps: ${response.status}`);
  }

  const data: ArcsListResponse<ArcStageMap> = response.data;
  return data.items;
}

// ============================================================================
// Arc mutation functions
// ============================================================================

/**
 * Create a new arc candidate
 */
export async function createArcCandidate(data: ArcCandidateCreateRequest): Promise<ArcCandidate> {
  const response = await api.post('/v1/story-development/arcs/candidates', data, {
    params: { project_id: data.project_id },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create arc candidate: ${response.status}`);
  }

  return response.data;
}

/**
 * Create an arc selection
 */
export async function createArcSelection(data: ArcSelectionCreateRequest): Promise<ArcSelection> {
  const response = await api.post('/v1/story-development/arcs/selections', data, {
    params: { project_id: data.project_id },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create arc selection: ${response.status}`);
  }

  return response.data;
}

/**
 * Delete an arc selection
 */
export async function deleteArcSelection(
  selectionId: string,
  projectId: string,
): Promise<void> {
  const response = await api.delete(
    `/v1/story-development/arcs/selections/${selectionId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to delete arc selection ${selectionId}: ${response.status}`);
  }
}

/**
 * Create an arc stage map
 */
export async function createArcStageMap(data: ArcStageMapCreateRequest): Promise<ArcStageMap> {
  const response = await api.post('/v1/story-development/arcs/stage-maps', data, {
    params: { project_id: data.project_id },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create arc stage map: ${response.status}`);
  }

  return response.data;
}

/**
 * Update an arc selection
 */
export async function updateArcSelection(
  selectionId: string,
  data: ArcSelectionUpdateRequest,
  projectId: string,
): Promise<ArcSelection> {
  const response = await api.patch(
    `/v1/story-development/arcs/selections/${selectionId}`,
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update arc selection ${selectionId}: ${response.status}`);
  }

  return response.data;
}

