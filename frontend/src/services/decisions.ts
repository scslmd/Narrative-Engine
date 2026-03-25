import type { StoryDecisionNode, StoryDecisionPath } from '../types/decisions';

interface DecisionListResponse {
  project_id: string;
  items: StoryDecisionNode[];
  meta: Record<string, unknown>;
}

export async function getDecisions(projectId: string): Promise<StoryDecisionNode[]> {
  const response = await fetch(`/api/story-development/decisions?project_id=${projectId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch decisions: ${response.statusText}`);
  }

  const data: DecisionListResponse = await response.json();
  return data.items;
}

export async function getDecision(nodeId: string): Promise<StoryDecisionNode> {
  const response = await fetch(`/api/story-development/decisions/${nodeId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch decision: ${response.statusText}`);
  }

  return response.json();
}

interface DecisionPathResponse {
  project_id: string;
  node: StoryDecisionNode;
  parent_path: StoryDecisionNode[];
}

export async function getDecisionPath(nodeId: string): Promise<StoryDecisionPath> {
  const response = await fetch(`/api/story-development/decisions/${nodeId}/path`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch decision path: ${response.statusText}`);
  }

  const data: DecisionPathResponse = await response.json();
  return {
    path_id: data.node.node_id,
    project_id: data.project_id,
    nodes: [...data.parent_path.map(n => n.node_id), data.node.node_id],
    created_at: data.node.created_at,
  };
}
