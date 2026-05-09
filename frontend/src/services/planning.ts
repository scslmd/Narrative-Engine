/**
 * Planning Service
 * 
 * Service for interacting with planning-related API endpoints:
 * - Sequence plans
 * - Chapter plans
 * - Scene plans
 * - Beat plans
 * - Planning dependencies
 * - Chapter packets
 */

import type {
  SequencePlan,
  ChapterPlan,
  ScenePlan,
  BeatPlan,
  ChapterPacket,
  PlanningDependency,
  SequencePlanCreateRequest,
  SequencePlanUpdateRequest,
  ChapterPacketCreateRequest,
  ChapterPlanCreateRequest,
  ChapterPlanUpdateRequest,
  ScenePlanCreateRequest,
  ScenePlanUpdateRequest,
  BeatPlanCreateRequest,
  BeatPlanUpdateRequest,
  PlanningReorderRequest,
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
  const response = await api.get('/v1/story-development/planning/sequence-plans', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch sequence plans: ${response.status}`);
  }

  const data: PlanningListResponse<SequencePlan> = response.data;
  return data.items;
}

/**
 * Get all chapter plans for a project
 */
export async function getChapterPlans(projectId: string): Promise<ChapterPlan[]> {
  const response = await api.get('/v1/story-development/planning/chapter-plans', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch chapter plans: ${response.status}`);
  }

  const data: PlanningListResponse<ChapterPlan> = response.data;
  return data.items;
}

/**
 * Get all scene plans for a project
 */
export async function getScenePlans(projectId: string): Promise<ScenePlan[]> {
  const response = await api.get('/v1/story-development/planning/scene-plans', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch scene plans: ${response.status}`);
  }

  const data: PlanningListResponse<ScenePlan> = response.data;
  return data.items;
}

/**
 * Get all planning dependencies for a project
 */
export async function getPlanningDependencies(projectId: string): Promise<PlanningDependency[]> {
  const response = await api.get('/v1/story-development/planning/dependencies', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch planning dependencies: ${response.status}`);
  }

  const data: PlanningListResponse<PlanningDependency> = response.data;
  return data.items;
}

/**
 * Get all chapter packets for a project
 */
export async function getChapterPackets(projectId: string): Promise<ChapterPacket[]> {
  const response = await api.get('/v1/story-development/planning/chapter-packets', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch chapter packets: ${response.status}`);
  }

  const data: PlanningListResponse<ChapterPacket> = response.data;
  return data.items;
}

/**
 * Get a single sequence plan by ID
 */
export async function getSequencePlan(
  sequenceId: string,
  projectId: string,
): Promise<SequencePlan> {
  const response = await api.get(
    `/v1/story-development/planning/sequence-plans/${sequenceId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch sequence plan ${sequenceId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Get a single chapter plan by ID
 */
export async function getChapterPlan(
  chapterId: string,
  projectId: string,
): Promise<ChapterPlan> {
  const response = await api.get(
    `/v1/story-development/planning/chapter-plans/${chapterId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch chapter plan ${chapterId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Get a single scene plan by ID
 */
export async function getScenePlan(
  sceneId: string,
  projectId: string,
): Promise<ScenePlan> {
  const response = await api.get(
    `/v1/story-development/planning/scene-plans/${sceneId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch scene plan ${sceneId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Get a single beat plan by ID
 */
export async function getBeatPlan(
  beatId: string,
  projectId: string,
): Promise<BeatPlan> {
  const response = await api.get(
    `/v1/story-development/planning/beat-plans/${beatId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch beat plan ${beatId}: ${response.status}`);
  }

  return response.data;
}

/**
 * Get a single chapter packet by ID
 */
export async function getChapterPacket(
  packetId: string,
  projectId: string,
): Promise<ChapterPacket> {
  const response = await api.get(
    `/v1/story-development/planning/chapter-packets/${packetId}`,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch chapter packet ${packetId}: ${response.status}`);
  }

  return response.data;
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
  const response = await api.post('/v1/story-development/planning/sequence-plans', data, {
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
    `/v1/story-development/planning/sequence-plans/${sequenceId}`,
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update sequence plan ${sequenceId}: ${response.status}`);
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
  const response = await api.post('/v1/story-development/planning/chapter-plans', data, {
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
    `/v1/story-development/planning/chapter-plans/${chapterId}`,
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
  const response = await api.post('/v1/story-development/planning/scene-plans', data, {
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
    `/v1/story-development/planning/scene-plans/${sceneId}`,
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update scene plan ${sceneId}: ${response.status}`);
  }

  return response.data;
}

// ============================================================================
// Beat Plan queries and mutations
// ============================================================================

/**
 * Get all beat plans for a project
 */
export async function getBeatPlans(projectId: string): Promise<BeatPlan[]> {
  const response = await api.get('/v1/story-development/planning/beat-plans', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch beat plans: ${response.status}`);
  }

  const data: PlanningListResponse<BeatPlan> = response.data;
  return data.items;
}

/**
 * Create a new beat plan
 */
export async function createBeatPlan(
  projectId: string,
  data: BeatPlanCreateRequest,
): Promise<BeatPlan> {
  const response = await api.post('/v1/story-development/planning/beat-plans', data, {
    params: { project_id: projectId },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create beat plan: ${response.status}`);
  }

  return response.data;
}

/**
 * Update an existing beat plan
 */
export async function updateBeatPlan(
  beatId: string,
  projectId: string,
  data: BeatPlanUpdateRequest,
): Promise<BeatPlan> {
  const response = await api.patch(
    `/v1/story-development/planning/beat-plans/${beatId}`,
    data,
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to update beat plan ${beatId}: ${response.status}`);
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
  const response = await api.post('/v1/story-development/planning/chapter-packets', data, {
    params: { project_id: projectId },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create chapter packet: ${response.status}`);
  }

  return response.data;
}

// ============================================================================
// Planning reorder
// ============================================================================

/**
 * Reorder sequence, chapter, or scene plans
 */
export async function reorderPlanObjects(
  data: PlanningReorderRequest,
): Promise<void> {
  const response = await api.post('/v1/story-development/planning/reorder', data);

  if (response.status !== 200) {
    throw new Error(`Failed to reorder ${data.plan_kind} plans: ${response.status}`);
  }
}

