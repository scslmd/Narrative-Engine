import type { StoryFlowStage } from '../types/flow';
import { flowMockService } from './mocks/flowMock';

export const flowService = {
  async getStages(projectId: string): Promise<StoryFlowStage[]> {
    return flowMockService.getStages(projectId);
  },

  async addStage(projectId: string, stageKind: StoryFlowStage['stage_kind']): Promise<StoryFlowStage> {
    return flowMockService.addStage(projectId, stageKind);
  },

  async updateStage(stageId: string, updates: Partial<StoryFlowStage>): Promise<StoryFlowStage> {
    return flowMockService.updateStage(stageId, updates);
  },

  async reorderStages(projectId: string, newOrder: string[]): Promise<StoryFlowStage[]> {
    return flowMockService.reorderStages(projectId, newOrder);
  },

  async deleteStage(stageId: string): Promise<void> {
    return flowMockService.deleteStage(stageId);
  },

  async disableStage(stageId: string): Promise<StoryFlowStage> {
    return flowMockService.updateStage(stageId, { stage_configuration_state: 'DISABLED' });
  },

  async archiveStage(stageId: string): Promise<StoryFlowStage> {
    return flowMockService.updateStage(stageId, { stage_configuration_state: 'ARCHIVED' });
  },

  async renameStage(stageId: string, displayName: string): Promise<StoryFlowStage> {
    return flowMockService.updateStage(stageId, { display_name: displayName });
  },
};
