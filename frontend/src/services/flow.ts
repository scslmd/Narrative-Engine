import type { StoryFlowStage } from '../types/flow';
import api from '../lib/api';

interface StageListResponse {
  project_id: string;
  items: StoryFlowStage[];
  meta: Record<string, string>;
}

interface FlowStageUpdateRequest {
  display_name?: string;
  description?: string;
  depends_on?: string[];
  writer_notes?: string;
  custom_prompt_guidance?: string;
  stage_configuration_state?: string;
}

interface FlowStageCreateRequest {
  project_id: string;
  stage_kind: StoryFlowStage['stage_kind'];
  display_name?: string;
  description?: string;
}

export async function getStages(projectId: string): Promise<StoryFlowStage[]> {
  const response = await api.get('/story-development/flow/stages', { params: { project_id: projectId } });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch flow stages for ${projectId}: ${response.status}`);
  }

  const data: StageListResponse = response.data;
  return data.items;
}

export async function addStage(
  projectId: string,
  stageKind: StoryFlowStage['stage_kind'],
  displayName?: string,
): Promise<StoryFlowStage> {
  const payload: FlowStageCreateRequest = {
    project_id: projectId,
    stage_kind: stageKind,
  };

  if (displayName) payload.display_name = displayName;

  const response = await api.post('/story-development/flow/stages', payload);

  if (response.status !== 201) {
    throw new Error(`Failed to create flow stage for ${projectId}: ${response.status}`);
  }

  return response.data;
}

export async function updateStageWithProject(projectId: string, stageId: string, updates: FlowStageUpdateRequest): Promise<StoryFlowStage> {
  const payload: FlowStageUpdateRequest = {};

  if (updates.display_name !== undefined) payload.display_name = updates.display_name;
  if (updates.description !== undefined) payload.description = updates.description;
  if (updates.depends_on !== undefined) payload.depends_on = updates.depends_on;
  if (updates.writer_notes !== undefined) payload.writer_notes = updates.writer_notes;
  if (updates.custom_prompt_guidance !== undefined) payload.custom_prompt_guidance = updates.custom_prompt_guidance;
  if (updates.stage_configuration_state !== undefined) payload.stage_configuration_state = updates.stage_configuration_state;

  const response = await api.patch(`/story-development/flow/stages/${stageId}?project_id=${projectId}`, payload);

  if (response.status !== 200) {
    throw new Error(`Failed to update flow stage ${stageId}: ${response.status}`);
  }

  return response.data;
}

export async function deleteStage(projectId: string, stageId: string): Promise<void> {
  const response = await api.delete(`/story-development/flow/stages/${stageId}?project_id=${projectId}`);

  if (response.status !== 200) {
    throw new Error(`Failed to delete flow stage ${stageId}: ${response.status}`);
  }

  return undefined;
}

export async function archiveStage(projectId: string, stageId: string): Promise<StoryFlowStage> {
  return updateStageWithProject(projectId, stageId, { stage_configuration_state: 'ARCHIVED' });
}

export async function renameStage(projectId: string, stageId: string, displayName: string): Promise<StoryFlowStage> {
  return updateStageWithProject(projectId, stageId, { display_name: displayName });
}

/**
 * Initialize flow stages for a project
 */
export async function initFlow(projectId: string): Promise<StoryFlowStage[]> {
  const response = await api.post('/story-development/flow/stages', {}, {
    params: { project_id: projectId },
  });

  if (response.status !== 201) {
    throw new Error(`Failed to initialize flow for ${projectId}: ${response.status}`);
  }

  const data: StageListResponse = response.data;
  return data.items;
}

/**
 * Reorder flow stages
 */
export async function reorderFlowStages(
  orderedIds: string[],
  projectId: string,
): Promise<void> {
  const response = await api.post(
    '/story-development/flow/stages/reorder',
    { stage_ids: orderedIds },
    { params: { project_id: projectId } },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to reorder flow stages for ${projectId}: ${response.status}`);
  }
}
