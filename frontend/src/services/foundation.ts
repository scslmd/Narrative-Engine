/**
 * Foundation Service
 * 
 * Service for interacting with foundation-related API endpoints:
 * - Get foundation profile
 * - Create foundation profile
 * - Update foundation profile
 * 
 * Backend endpoints:
 * - GET /story-development/foundation
 * - POST /story-development/foundation
 * - PATCH /story-development/foundation
 */

import type {
  FoundationCreateRequest,
  FoundationUpdateRequest,
  FoundationReadResponse,
  FoundationWriteResponse,
  FoundationRevision,
  FoundationReviewCue,
} from '../types/foundation';
import api from '../lib/api';

/**
 * Get the foundation profile for a project
 */
export async function getFoundation(projectId: string): Promise<FoundationReadResponse> {
  const response = await api.get('/story-development/foundation', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch foundation: ${response.status}`);
  }

  return response.data;
}

/**
 * Create a foundation profile for a project
 */
export async function createFoundation(
  request: FoundationCreateRequest,
): Promise<FoundationWriteResponse> {
  const response = await api.post('/story-development/foundation', request);

  if (response.status !== 201) {
    throw new Error(`Failed to create foundation: ${response.status}`);
  }

  return response.data;
}

/**
 * Update the foundation profile for a project
 */
export async function updateFoundation(
  projectId: string,
  updates: FoundationUpdateRequest,
): Promise<FoundationWriteResponse> {
  const response = await api.patch('/story-development/foundation', updates, {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to update foundation: ${response.status}`);
  }

  return response.data;
}

/**
 * Get review cues for a project's foundation
 */
export async function getReviewCues(projectId: string): Promise<FoundationReviewCue[]> {
  const response = await api.get('/story-development/foundation/review-cues', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch review cues: ${response.status}`);
  }

  const data = response.data;
  return data.items;
}

/**
 * Get foundation revisions for a project
 */
export async function getFoundationRevisions(projectId: string): Promise<FoundationRevision[]> {
  const response = await api.get('/story-development/foundation/revisions', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch foundation revisions: ${response.status}`);
  }

  const data = response.data;
  return data.items;
}
