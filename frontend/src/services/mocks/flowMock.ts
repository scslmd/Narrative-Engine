import type { StoryFlowStage } from '../../types/flow';

const DEFAULT_STAGES: StoryFlowStage[] = [
  {
    stage_id: 'stage-1',
    project_id: 'mock-project',
    position: 0,
    display_name: 'Brainstorm',
    stage_kind: 'brainstorm',
    description: 'Generate initial ideas and concepts',
    stage_configuration_state: 'ACTIVE',
    progress_percentage: 100,
  },
  {
    stage_id: 'stage-2',
    project_id: 'mock-project',
    position: 1,
    display_name: 'Foundation',
    stage_kind: 'foundation',
    description: 'Establish core story elements',
    stage_configuration_state: 'ACTIVE',
    progress_percentage: 80,
  },
  {
    stage_id: 'stage-3',
    project_id: 'mock-project',
    position: 2,
    display_name: 'Character',
    stage_kind: 'character',
    description: 'Develop character profiles and arcs',
    stage_configuration_state: 'ACTIVE',
    progress_percentage: 60,
  },
  {
    stage_id: 'stage-4',
    project_id: 'mock-project',
    position: 3,
    display_name: 'World Bible',
    stage_kind: 'world_bible',
    description: 'Build the story world and rules',
    stage_configuration_state: 'ACTIVE',
    progress_percentage: 40,
  },
  {
    stage_id: 'stage-5',
    project_id: 'mock-project',
    position: 4,
    display_name: 'Arc Selection',
    stage_kind: 'arc_selection',
    description: 'Choose the main narrative arc',
    stage_configuration_state: 'ACTIVE',
    progress_percentage: 20,
  },
  {
    stage_id: 'stage-6',
    project_id: 'mock-project',
    position: 5,
    display_name: 'Planning',
    stage_kind: 'planning',
    description: 'Create chapter and scene outlines',
    stage_configuration_state: 'ACTIVE',
    progress_percentage: 0,
  },
  {
    stage_id: 'stage-7',
    project_id: 'mock-project',
    position: 6,
    display_name: 'Drafting',
    stage_kind: 'drafting',
    description: 'Write the manuscript',
    stage_configuration_state: 'ACTIVE',
    progress_percentage: 0,
  },
  {
    stage_id: 'stage-8',
    project_id: 'mock-project',
    position: 7,
    display_name: 'Review',
    stage_kind: 'review',
    description: 'Edit and refine the story',
    stage_configuration_state: 'ACTIVE',
    progress_percentage: 0,
  },
];

let stages = [...DEFAULT_STAGES];

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const flowMockService = {
  async getStages(projectId: string): Promise<StoryFlowStage[]> {
    await delay(200);
    return stages.filter((s) => s.project_id === projectId || projectId === 'mock-project');
  },

  async addStage(projectId: string, stageKind: StoryFlowStage['stage_kind']): Promise<StoryFlowStage> {
    await delay(2000);
    
    const newStage: StoryFlowStage = {
      stage_id: `stage-${Date.now()}`,
      project_id: projectId,
      position: stages.length,
      display_name: `Custom Stage ${stages.filter((s) => s.stage_kind === 'review').length + 1}`,
      stage_kind: stageKind,
      description: '',
      stage_configuration_state: 'ACTIVE',
      progress_percentage: 0,
    };

    stages = [...stages, newStage];
    return newStage;
  },

  async updateStage(stageId: string, updates: Partial<StoryFlowStage>): Promise<StoryFlowStage> {
    await delay(2000);
    
    const index = stages.findIndex((s) => s.stage_id === stageId);
    if (index === -1) {
      throw new Error('Stage not found');
    }

    const updatedStage = { ...stages[index], ...updates };
    stages = [...stages.slice(0, index), updatedStage, ...stages.slice(index + 1)];
    return updatedStage;
  },

  async reorderStages(projectId: string, newOrder: string[]): Promise<StoryFlowStage[]> {
    await delay(2000);
    
    const projectStages = stages.filter((s) => s.project_id === projectId);
    const reordered = newOrder.map((id) => projectStages.find((s) => s.stage_id === id)).filter(Boolean) as StoryFlowStage[];
    
    reordered.forEach((stage, index) => {
      stage.position = index;
    });

    stages = stages.filter((s) => s.project_id !== projectId);
    stages = [...stages, ...reordered];
    
    return reordered;
  },

  async deleteStage(stageId: string): Promise<void> {
    await delay(2000);
    
    const stage = stages.find((s) => s.stage_id === stageId);
    if (stage && ['brainstorm', 'foundation', 'character', 'world_bible', 'arc_selection', 'planning', 'drafting', 'review'].includes(stage.stage_kind)) {
      throw new Error('Cannot delete default stages');
    }

    stages = stages.filter((s) => s.stage_id !== stageId);
  },
};
