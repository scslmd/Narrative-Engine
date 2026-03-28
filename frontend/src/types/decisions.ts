export interface StoryDecisionNode {
  node_id: string;
  project_id: string;
  decision_point: string;
  parent_node_id?: string;  // null/undefined for root nodes
  options: Array<{
    option_id: string;
    label: string;
    next_node_id?: string;
  }>;
  created_at: string;
}

export interface StoryDecisionPath {
  path_id: string;
  project_id: string;
  nodes: string[];
  outcome?: string;
  created_at: string;
}
