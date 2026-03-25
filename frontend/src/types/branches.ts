export interface StoryBranch {
  branch_id: string;
  project_id: string;
  name: string;
  description?: string;
  parent_branch_id?: string;
  state: 'active' | 'merged' | 'archived';
  created_at: string;
}

export interface BranchComparisonRecord {
  comparison_id: string;
  project_id: string;
  branch_a_id: string;
  branch_b_id: string;
  differences: Array<{
    object_kind: string;
    branch_a_value?: unknown;
    branch_b_value?: unknown;
  }>;
  created_at: string;
}

export interface BranchMergeDecision {
  merge_decision_id: string;
  project_id: string;
  source_branch_id: string;
  target_branch_id: string;
  decision: 'merge' | 'reject' | 'defer';
  rationale?: string;
  created_at: string;
}

export interface BranchStateRef {
  state_ref_id: string;
  branch_id: string;
  object_kind: string;
  object_id: string;
  created_at: string;
}
