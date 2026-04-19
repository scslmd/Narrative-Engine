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

export const flowService = {
  async getStages(projectId: string): Promise<StoryFlowStage[]> {
    const response = await api.get('/story-development/flow/stages', { params: { project_id: projectId } });
    
    if (response.status !== 200) {
      throw new Error(`Failed to fetch flow stages for ${projectId}: ${response.status}`);
    }

    const data: StageListResponse = response.data;
    return data.items;
  },

  async addStage(projectId: string, stageKind: StoryFlowStage['stage_kind']): Promise<StoryFlowStage> {
    const response = await api.post('/story-development/flow/stages', {
      project_id: projectId,
      stage_kind: stageKind,
    });

    if (response.status !== 201) {
      throw new Error(`Failed to create flow stage for ${projectId}: ${response.status}`);
    }

    return response.data;
  },

  // Legacy method - kept for compatibility but throws error directing users to use updateStageWithProject
  async updateStage(stageId: string, updates: Partial<StoryFlowStage>): Promise<StoryFlowStage> {
    void stageId; // Parameter kept for API compatibility
    void updates; // Parameter kept for API compatibility
    throw new Error(`updateStage requires project_id parameter. Use updateStageWithProject(projectId, stageId, updates) instead.`);
  },

  async updateStageWithProject(projectId: string, stageId: string, updates: FlowStageUpdateRequest): Promise<StoryFlowStage> {
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
  },

  async reorderStages(projectId: string, newOrder: string[]): Promise<StoryFlowStage[]> {
    const response = await api.post('/story-development/flow/stages/reorder', 
      { stage_order: newOrder },
      { params: { project_id: projectId } }
    );

    if (response.status !== 200) {
      throw new Error(`Failed to reorder flow stages for ${projectId}: ${response.status}`);
    }

    return response.data.stages;
  },

  async deleteStage(projectId: string, stageId: string): Promise<void> {
    const response = await api.delete(`/story-development/flow/stages/${stageId}?project_id=${projectId}`);

    if (response.status !== 200) {
      throw new Error(`Failed to delete flow stage ${stageId}: ${response.status}`);
    }

    return undefined;
  },

  async disableStage(projectId: string, stageId: string): Promise<StoryFlowStage> {
    return this.updateStageWithProject(projectId, stageId, { stage_configuration_state: 'disabled' });
  },

  async archiveStage(projectId: string, stageId: string): Promise<StoryFlowStage> {
    return this.updateStageWithProject(projectId, stageId, { stage_configuration_state: 'archived' });
  },

  async renameStage(projectId: string, stageId: string, displayName: string): Promise<StoryFlowStage> {
    return this.updateStageWithProject(projectId, stageId, { display_name: displayName });
  },
};
