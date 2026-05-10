/**
 * Relationships Service
 * 
 * Service for interacting with character relationship API endpoints:
 * - List all relationships for a project
 * - Create, update, and delete relationships
 * 
 * Backend endpoints:
 * - POST /v1/story-development/relationships (201)
 * - GET /v1/story-development/relationships
 * - PATCH /v1/story-development/relationships/{edge_id}
 * - DELETE /v1/story-development/relationships/{edge_id}
 * - POST /v1/story-development/relationships/extract
 */

import type {
  RelationshipEdge,
  RelationshipEdgeCreateRequest,
  RelationshipEdgeListResponse,
} from '../types/characters';

export interface RelationshipUpdateRequest {
  relation_kind?: string;
  summary?: string;
  tension?: string | null;
  notes?: string | null;
}

export interface RelationshipExtractRequest {
  manuscript_text: string;
  character_ids?: string[];
  model?: string;
}

import api from '../lib/api';

/**
 * Get all relationships for a project
 */
export async function getRelationships(projectId: string): Promise<RelationshipEdge[]> {
  const response = await api.get('/v1/story-development/relationships', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch relationships: ${response.status}`);
  }

  const data: RelationshipEdgeListResponse = response.data;
  return data.items;
}

/**
 * Create a relationship edge between two characters
 */
export async function createRelationship(
  data: RelationshipEdgeCreateRequest,
): Promise<RelationshipEdge> {
  const response = await api.post('/v1/story-development/relationships', data);

  if (response.status !== 201) {
    throw new Error(`Failed to create relationship: ${response.status}`);
  }

  return response.data;
}

/**
 * Extract relationships from manuscript text using AI analysis
 */
export async function extractRelationships(
  projectId: string,
  data: RelationshipExtractRequest,
): Promise<RelationshipEdge[]> {
  const response = await api.post(
    '/v1/story-development/relationships/extract',
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to extract relationships: ${response.status}`);
  }

  const result: RelationshipEdgeListResponse = response.data;
  return result.items;
}

/**
 * Delete a relationship edge
 */
export async function deleteRelationship(
  edgeId: string,
  projectId: string,
): Promise<void> {
  const response = await api.delete(
    `/v1/story-development/relationships/${edgeId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to delete relationship ${edgeId}: ${response.status}`);
  }
}

/**
 * Update a relationship edge
 */
export async function updateRelationship(
  edgeId: string,
  data: RelationshipUpdateRequest,
  projectId: string,
): Promise<RelationshipEdge> {
  const response = await api.patch(
    `/v1/story-development/relationships/${edgeId}`,
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update relationship ${edgeId}: ${response.status}`);
  }

  return response.data;
}

