import type { StoryDecisionNode, StoryDecisionPath } from '../types/decisions';
import api from '../lib/api';

interface DecisionListResponse {
  project_id: string;
  items: StoryDecisionNode[];
  meta: Record<string, unknown>;
}

export async function getDecisions(projectId: string): Promise<StoryDecisionNode[]> {
  const response = await api.get('/v1/story-development/decisions', { params: { project_id: projectId } });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch decisions: ${response.status}`);
  }

  const data: DecisionListResponse = response.data;
  return data.items;
}

interface DecisionPathResponse {
  project_id: string;
  node: StoryDecisionNode;
  parent_path: StoryDecisionNode[];
}

export async function getDecisionPath(nodeId: string): Promise<StoryDecisionPath> {
  const response = await api.get(`/v1/story-development/decisions/${nodeId}/path`);
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch decision path: ${response.status}`);
  }

  const data: DecisionPathResponse = response.data;
  return {
    path_id: data.node.node_id,
    project_id: data.project_id,
    nodes: [...data.parent_path.map(n => n.node_id), data.node.node_id],
    created_at: data.node.created_at,
  };
}

