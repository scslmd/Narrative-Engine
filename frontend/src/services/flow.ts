import type { StoryFlowStage } from '../types/flow';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const flowService = {
  async getStages(projectId: string): Promise<StoryFlowStage[]> {
    const response = await fetch(`${API_BASE}/v1/story-development/flow/stages?project_id=${projectId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch flow stages for ${projectId}: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data.items || [];
  },

  async addStage(projectId: string, stageKind: StoryFlowStage['stage_kind']): Promise<StoryFlowStage> {
    throw new Error(`Story-flow stage creation is not implemented for ${projectId} (${stageKind})`);
  },

  async updateStage(stageId: string, updates: Partial<StoryFlowStage>): Promise<StoryFlowStage> {
    throw new Error(`Story-flow stage update is not implemented for ${stageId}: ${JSON.stringify(updates)}`);
  },

  async reorderStages(projectId: string, newOrder: string[]): Promise<StoryFlowStage[]> {
    throw new Error(`Story-flow stage reordering is not implemented for ${projectId}: ${newOrder.join(',')}`);
  },

  async deleteStage(stageId: string): Promise<void> {
    throw new Error(`Story-flow stage deletion is not implemented for ${stageId}`);
  },

  async disableStage(stageId: string): Promise<StoryFlowStage> {
    return this.updateStage(stageId, { stage_configuration_state: 'DISABLED' });
  },

  async archiveStage(stageId: string): Promise<StoryFlowStage> {
    return this.updateStage(stageId, { stage_configuration_state: 'ARCHIVED' });
  },

  async renameStage(stageId: string, displayName: string): Promise<StoryFlowStage> {
    return this.updateStage(stageId, { display_name: displayName });
  },
};
