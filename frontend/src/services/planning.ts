/**
 * Planning Service
 * 
 * Service for interacting with planning-related API endpoints:
 * - Sequence plans
 * - Chapter plans
 * - Scene plans
 * - Planning dependencies
 * - Chapter packets
 */

import type {
  SequencePlan,
  ChapterPlan,
  ScenePlan,
  ChapterPacket,
  PlanningDependency,
  SequencePlanCreateRequest,
  SequencePlanUpdateRequest,
  ChapterPacketCreateRequest,
  ChapterPacketUpdateRequest,
  ChapterPlanCreateRequest,
  ChapterPlanUpdateRequest,
  ScenePlanCreateRequest,
  ScenePlanUpdateRequest,
} from '../types/planning';
import api from '../lib/api';

interface PlanningListResponse<T> {
  project_id: string;
  items: T[];
  meta: Record<string, string>;
}

/**
 * Get all sequence plans for a project
 */
export async function getSequencePlans(projectId: string): Promise<SequencePlan[]> {
  const response = await api.get('/story-development/planning/sequence-plans', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch sequence plans: ${response.status}`);
  }

  const data: PlanningListResponse<SequencePlan> = response.data;
  return data.items;
}

/**
 * Get a specific sequence plan by ID
 */
export async function getSequencePlan(sequenceId: string, projectId: string): Promise<SequencePlan> {
  const response = await api.get(
    `/story-development/planning/sequence-plans/${sequenceId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch sequence plan ${sequenceId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Get all chapter plans for a project
 */
export async function getChapterPlans(projectId: string): Promise<ChapterPlan[]> {
  const response = await api.get('/story-development/planning/chapter-plans', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch chapter plans: ${response.status}`);
  }

  const data: PlanningListResponse<ChapterPlan> = response.data;
  return data.items;
}

/**
 * Get a specific chapter plan by ID
 */
export async function getChapterPlan(chapterId: string, projectId: string): Promise<ChapterPlan> {
  const response = await api.get(
    `/story-development/planning/chapter-plans/${chapterId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch chapter plan ${chapterId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Get all scene plans for a project
 */
export async function getScenePlans(projectId: string): Promise<ScenePlan[]> {
  const response = await api.get('/story-development/planning/scene-plans', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch scene plans: ${response.status}`);
  }

  const data: PlanningListResponse<ScenePlan> = response.data;
  return data.items;
}

/**
 * Get a specific scene plan by ID
 */
export async function getScenePlan(sceneId: string, projectId: string): Promise<ScenePlan> {
  const response = await api.get(
    `/story-development/planning/scene-plans/${sceneId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch scene plan ${sceneId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Get all planning dependencies for a project
 */
export async function getPlanningDependencies(projectId: string): Promise<PlanningDependency[]> {
  const response = await api.get('/story-development/planning/dependencies', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch planning dependencies: ${response.status}`);
  }

  const data: PlanningListResponse<PlanningDependency> = response.data;
  return data.items;
}

/**
 * Get a specific planning dependency by ID
 */
export async function getPlanningDependency(
  dependencyId: string,
  projectId: string,
): Promise<PlanningDependency> {
  const response = await api.get(
    `/story-development/planning/dependencies/${dependencyId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch planning dependency ${dependencyId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Get all chapter packets for a project
 */
export async function getChapterPackets(projectId: string): Promise<ChapterPacket[]> {
  const response = await api.get('/story-development/planning/chapter-packets', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch chapter packets: ${response.status}`);
  }

  const data: PlanningListResponse<ChapterPacket> = response.data;
  return data.items;
}

/**
 * Get a specific chapter packet by ID
 */
export async function getChapterPacket(packetId: string, projectId: string): Promise<ChapterPacket> {
  const response = await api.get(
    `/story-development/planning/chapter-packets/${packetId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch chapter packet ${packetId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Get dependencies for a specific object (sequence, chapter, or scene)
 */
export function getDependenciesForObject(
  dependencies: PlanningDependency[],
  objectId: string,
): PlanningDependency[] {
  return dependencies.filter(
    (dep) => dep.upstream_id === objectId || dep.downstream_id === objectId,
  );
}

/**
 * Get upstream dependencies (things this object depends on)
 */
export function getUpstreamDependencies(
  dependencies: PlanningDependency[],
  objectId: string,
): PlanningDependency[] {
  return dependencies.filter((dep) => dep.downstream_id === objectId);
}

/**
 * Get downstream dependencies (things that depend on this object)
 */
export function getDownstreamDependencies(
  dependencies: PlanningDependency[],
  objectId: string,
): PlanningDependency[] {
  return dependencies.filter((dep) => dep.upstream_id === objectId);
}

// ============================================================================
// Sequence Plan mutations
// ============================================================================

/**
 * Create a new sequence plan
 */
export async function createSequencePlan(
  projectId: string,
  data: SequencePlanCreateRequest,
): Promise<SequencePlan> {
  const response = await api.post('/story-development/planning/sequence-plans', data, {
    params: { project_id: projectId },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create sequence plan: ${response.status}`);
  }

  return response.data;
}

/**
 * Update an existing sequence plan
 */
export async function updateSequencePlan(
  sequenceId: string,
  projectId: string,
  data: SequencePlanUpdateRequest,
): Promise<SequencePlan> {
  const response = await api.patch(
    `/story-development/planning/sequence-plans/${sequenceId}`,
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update sequence plan ${sequenceId}: ${response.status}`);
  }

  return response.data;
}

// ============================================================================
// Chapter Packet mutations
// ============================================================================

/**
 * Create a new chapter packet
 */
export async function createChapterPacket(
  projectId: string,
  data: ChapterPacketCreateRequest,
): Promise<ChapterPacket> {
  const response = await api.post('/story-development/planning/chapter-packets', data, {
    params: { project_id: projectId },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create chapter packet: ${response.status}`);
  }

  return response.data;
}

/**
 * Update an existing chapter packet
 */
export async function updateChapterPacket(
  packetId: string,
  projectId: string,
  data: ChapterPacketUpdateRequest,
): Promise<ChapterPacket> {
  const response = await api.patch(
    `/story-development/planning/chapter-packets/${packetId}`,
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update chapter packet ${packetId}: ${response.status}`);
  }

  return response.data;
}

// ============================================================================
// Chapter Plan mutations
// ============================================================================

/**
 * Create a new chapter plan
 */
export async function createChapterPlan(
  projectId: string,
  data: ChapterPlanCreateRequest,
): Promise<ChapterPlan> {
  const response = await api.post('/story-development/planning/chapter-plans', data, {
    params: { project_id: projectId },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create chapter plan: ${response.status}`);
  }

  return response.data;
}

/**
 * Update an existing chapter plan
 */
export async function updateChapterPlan(
  chapterId: string,
  projectId: string,
  data: ChapterPlanUpdateRequest,
): Promise<ChapterPlan> {
  const response = await api.patch(
    `/story-development/planning/chapter-plans/${chapterId}`,
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update chapter plan ${chapterId}: ${response.status}`);
  }

  return response.data;
}

// ============================================================================
// Scene Plan mutations
// ============================================================================

/**
 * Create a new scene plan
 */
export async function createScenePlan(
  projectId: string,
  data: ScenePlanCreateRequest,
): Promise<ScenePlan> {
  const response = await api.post('/story-development/planning/scene-plans', data, {
    params: { project_id: projectId },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create scene plan: ${response.status}`);
  }

  return response.data;
}

/**
 * Update an existing scene plan
 */
export async function updateScenePlan(
  sceneId: string,
  projectId: string,
  data: ScenePlanUpdateRequest,
): Promise<ScenePlan> {
  const response = await api.patch(
    `/story-development/planning/scene-plans/${sceneId}`,
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update scene plan ${sceneId}: ${response.status}`);
  }

  return response.data;
}
