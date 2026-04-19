/**
 * Brain Dump Service
 *
 * Service for interacting with brain dump session API endpoints:
 * - Create brain dump session
 * - List brain dump sessions
 * - Get brain dump session
 * - Update brain dump session
 * - Delete brain dump session
 * - Organize brain dump session (AI categorization)
 *
 * Backend endpoints:
 * - POST /v1/story-development/braindump/sessions
 * - GET /v1/story-development/braindump/sessions
 * - GET /v1/story-development/braindump/sessions/{session_id}
 * - PATCH /v1/story-development/braindump/sessions/{session_id}
 * - DELETE /v1/story-development/braindump/sessions/{session_id}
 * - POST /v1/story-development/braindump/sessions/{session_id}/organize
 */

import type {
  BrainDumpSession,
  BrainDumpSessionCreateRequest,
  BrainDumpSessionPatchRequest,
  BrainDumpSessionListResponse,
  BrainDumpOrganizeResponse,
} from '../types/braindump';
import api from '../lib/api';

/**
 * Create a new brain dump session
 */
export async function createBrainDumpSession(
  request: BrainDumpSessionCreateRequest,
): Promise<BrainDumpSession> {
  const response = await api.post('/v1/story-development/braindump/sessions', request);

  if (response.status !== 201) {
    throw new Error(`Failed to create brain dump session: ${response.status}`);
  }

  return response.data;
}

/**
 * Get all brain dump sessions for a project
 */
export async function getBrainDumpSessions(projectId: string): Promise<BrainDumpSession[]> {
  const response = await api.get('/v1/story-development/braindump/sessions', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch brain dump sessions: ${response.status}`);
  }

  const data: BrainDumpSessionListResponse = response.data;
  return data.sessions;
}

/**
 * Get a specific brain dump session
 */
export async function getBrainDumpSession(
  sessionId: string,
  projectId: string,
): Promise<BrainDumpSession> {
  const response = await api.get(
    `/v1/story-development/braindump/sessions/${sessionId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch brain dump session: ${response.status}`);
  }

  return response.data;
}

/**
 * Update a brain dump session
 */
export async function updateBrainDumpSession(
  sessionId: string,
  projectId: string,
  patch: BrainDumpSessionPatchRequest,
): Promise<BrainDumpSession> {
  const response = await api.patch(
    `/v1/story-development/braindump/sessions/${sessionId}`,
    patch,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update brain dump session: ${response.status}`);
  }

  return response.data;
}

/**
 * Delete a brain dump session
 */
export async function deleteBrainDumpSession(
  sessionId: string,
  projectId: string,
): Promise<void> {
  const response = await api.delete(
    `/v1/story-development/braindump/sessions/${sessionId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 204) {
    throw new Error(`Failed to delete brain dump session: ${response.status}`);
  }
}

/**
 * Organize a brain dump session with AI categorization
 */
export async function organizeBrainDumpSession(
  sessionId: string,
  projectId: string,
): Promise<BrainDumpOrganizeResponse> {
  const response = await api.post(
    `/v1/story-development/braindump/sessions/${sessionId}/organize`,
    {},
    { params: { project_id: projectId } },
  );

  if (response.status !== 201) {
    throw new Error(`Failed to organize brain dump session: ${response.status}`);
  }

  return response.data;
}
