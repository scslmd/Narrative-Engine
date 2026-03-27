import type { StoryFlowStage } from '../types/flow';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const flowService = {
  async getStages(projectId: string): Promise<StoryFlowStage[]> {
    try {
      const response = await fetch(`${API_BASE}/v1/story-development/flow/stages?project_id=${projectId}`);
      if (!response.ok) {
        console.warn('Story-flow stages endpoint not available yet, returning empty array');
        return [];
      }
      const data = await response.json();
      return data.items || [];
    } catch (error) {
      console.warn('Story-flow stages endpoint not available yet, returning empty array');
      return [];
    }
  },

  async addStage(_projectId: string, _stageKind: StoryFlowStage['stage_kind']): Promise<StoryFlowStage> {
    throw new Error('Story-flow stage creation not yet implemented on backend');
  },

  async updateStage(_stageId: string, _updates: Partial<StoryFlowStage>): Promise<StoryFlowStage> {
    throw new Error('Story-flow stage update not yet implemented on backend');
  },

  async reorderStages(_projectId: string, _newOrder: string[]): Promise<StoryFlowStage[]> {
    throw new Error('Story-flow stage reordering not yet implemented on backend');
  },

  async deleteStage(_stageId: string): Promise<void> {
    throw new Error('Story-flow stage deletion not yet implemented on backend');
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
