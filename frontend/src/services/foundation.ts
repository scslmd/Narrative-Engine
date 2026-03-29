/**
 * Foundation Service
 * 
 * Service for interacting with foundation-related API endpoints:
 * - Get foundation profile
 * - Create foundation profile
 * - Update foundation profile
 * - Get foundation revisions
 * - Get foundation review cues
 * 
 * Backend endpoints:
 * - GET /story-development/foundation
 * - POST /story-development/foundation
 * - PATCH /story-development/foundation
 * - GET /story-development/foundation/revisions
 * - GET /story-development/foundation/review-cues
 */

import type {
  FoundationProfile,
  FoundationRevision,
  FoundationReviewCue,
  FoundationCreateRequest,
  FoundationUpdateRequest,
  FoundationReadResponse,
  FoundationWriteResponse,
  FoundationRevisionListResponse,
  FoundationReviewCueListResponse,
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
 * Get all foundation revisions for a project
 */
export async function getFoundationRevisions(projectId: string): Promise<FoundationRevision[]> {
  const response = await api.get('/story-development/foundation/revisions', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch foundation revisions: ${response.status}`);
  }

  const data: FoundationRevisionListResponse = response.data;
  return data.items;
}

/**
 * Get foundation review cues for a project
 */
export async function getFoundationReviewCues(projectId: string): Promise<FoundationReviewCue[]> {
  const response = await api.get('/story-development/foundation/review-cues', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch foundation review cues: ${response.status}`);
  }

  const data: FoundationReviewCueListResponse = response.data;
  return data.items;
}

/**
 * Get the active foundation profile from a read response
 */
export function getActiveProfile(response: FoundationReadResponse): FoundationProfile | null {
  return response.active_profile;
}

/**
 * Get the latest revision from the revision history
 */
export function getLatestRevision(revisions: FoundationRevision[]): FoundationRevision | null {
  if (revisions.length === 0) {
    return null;
  }
  return revisions.reduce((latest, current) => {
    const latestSnapshot = latest.snapshot;
    const currentSnapshot = current.snapshot;
    return currentSnapshot.version > latestSnapshot.version ? current : latest;
  });
}

/**
 * Check if foundation has review cues (needs attention)
 */
export function hasReviewCues(cues: FoundationReviewCue[]): boolean {
  return cues.length > 0;
}

/**
 * Get review cues grouped by impacted area
 */
export function groupReviewCuesByArea(
  cues: FoundationReviewCue[],
): Record<string, FoundationReviewCue[]> {
  return cues.reduce((acc, cue) => {
    if (!acc[cue.impacted_area]) {
      acc[cue.impacted_area] = [];
    }
    acc[cue.impacted_area].push(cue);
    return acc;
  }, {} as Record<string, FoundationReviewCue[]>);
}
