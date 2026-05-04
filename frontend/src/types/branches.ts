export interface BranchRecord {
  branch_id: string;
  project_id: string;
  branch_point_id: string;
  branch_name: string;
  branch_state: 'ACTIVE' | 'ARCHIVED';
}

export interface StoryBranch {
  branch_id: string;
  project_id: string;
  branch_point_id: string;
  branch_name: string;
  branch_state: 'ACTIVE' | 'ARCHIVED';
}

export interface BranchComparisonRecord {
  comparison_id: string;
  project_id: string;
  source_branch_id: string;
  target_branch_id: string;
  review_notes: string[];
}

export interface MergeDecisionRecord {
  merge_decision_id: string;
  project_id: string;
  source_branch_id: string;
  target_branch_id: string;
  merge_rationale: string;
  resulting_decision_node_ids: string[];
}

export interface BranchMergeDecision {
  merge_decision_id: string;
  project_id: string;
  source_branch_id: string;
  target_branch_id: string;
  merge_rationale: string;
  resulting_decision_node_ids: string[];
}

export interface BranchStateRef {
  branch_state_ref_id: string;
  project_id: string;
  branch_id: string;
  state_object_type: string;
  state_object_id: string;
  decision_node_id: string | null;
}
