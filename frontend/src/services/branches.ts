import type { StoryBranch, BranchComparisonRecord, BranchMergeDecision } from '../types/branches';
import api from '../lib/api';

interface BranchListResponse {
  project_id: string;
  items: StoryBranch[];
  meta: Record<string, string>;
}

export async function getBranches(projectId: string): Promise<StoryBranch[]> {
  const response = await api.get('/story-development/branches', { params: { project_id: projectId } });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch branches: ${response.status}`);
  }

  const data: BranchListResponse = response.data;
  return data.items;
}

export async function setActiveBranch(projectId: string, branchId: string): Promise<StoryBranch> {
  const response = await api.post('/story-development/branches/active', { 
    project_id: projectId, 
    branch_id: branchId 
  });

  if (response.status !== 200) {
    throw new Error(`Failed to set active branch: ${response.status}`);
  }

  return response.data;
}

export async function createBranchComparison(
  projectId: string,
  sourceBranchId: string,
  targetBranchId: string,
): Promise<BranchComparisonRecord> {
  const response = await api.post('/story-development/branches/comparisons', {
    project_id: projectId,
    comparison_id: crypto.randomUUID(),
    source_branch_id: sourceBranchId,
    target_branch_id: targetBranchId,
    review_notes: [],
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create comparison: ${response.status}`);
  }

  return response.data;
}

export async function createMergeDecision(
  projectId: string,
  sourceBranchId: string,
  targetBranchId: string,
  mergeRationale: string,
): Promise<BranchMergeDecision> {
  const response = await api.post('/story-development/branches/merge-decisions', {
    project_id: projectId,
    merge_decision_id: crypto.randomUUID(),
    source_branch_id: sourceBranchId,
    target_branch_id: targetBranchId,
    merge_rationale: mergeRationale,
    resulting_decision_node_ids: [],
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create merge decision: ${response.status}`);
  }

  return response.data;
}
