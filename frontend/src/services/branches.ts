import type { StoryBranch, BranchComparisonRecord, BranchMergeDecision, BranchStateRef } from '../types/branches';
import api, { ApiError } from '../lib/api';

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

export async function createBranch(
  projectId: string,
  branchName: string,
  branchPointId: string,
): Promise<StoryBranch> {
  // Backend requires branch_id and branch_point_id, uses branch_name field
  const response = await api.post('/story-development/branches', {
    project_id: projectId,
    branch_id: crypto.randomUUID(),
    branch_point_id: branchPointId,
    branch_name: branchName,
    branch_state: 'ACTIVE',
  });

  if (response.status !== 201) {
    throw new Error(`Failed to create branch: ${response.status}`);
  }

  return response.data;
}

export async function getActiveBranch(projectId: string): Promise<StoryBranch | null> {
  try {
    const response = await api.get('/story-development/branches/active', { params: { project_id: projectId } });

    if (response.status !== 200) {
      throw new Error(`Failed to fetch active branch: ${response.status}`);
    }

    return response.data;
  } catch (error: unknown) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

export async function setActiveBranch(projectId: string, branchId: string): Promise<StoryBranch> {
  // Backend expects POST with body containing project_id and branch_id
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
  // Backend requires comparison_id, source_branch_id, and target_branch_id
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

interface ComparisonListResponse {
  project_id: string;
  items: BranchComparisonRecord[];
  meta: Record<string, string>;
}

export async function getComparisons(projectId: string): Promise<BranchComparisonRecord[]> {
  const response = await api.get('/story-development/branches/comparisons', { params: { project_id: projectId } });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch comparisons: ${response.status}`);
  }

  const data: ComparisonListResponse = response.data;
  return data.items;
}

export async function getComparison(comparisonId: string, projectId?: string): Promise<BranchComparisonRecord> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;
  
  const response = await api.get(`/story-development/branches/comparisons/${comparisonId}`, { params });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch comparison: ${response.status}`);
  }

  return response.data;
}

export async function createMergeDecision(
  projectId: string,
  sourceBranchId: string,
  targetBranchId: string,
  mergeRationale: string,
): Promise<BranchMergeDecision> {
  // Backend requires merge_decision_id and uses merge_rationale field
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

interface MergeDecisionListResponse {
  project_id: string;
  items: BranchMergeDecision[];
  meta: Record<string, string>;
}

export async function getMergeDecisions(projectId: string): Promise<BranchMergeDecision[]> {
  const response = await api.get('/story-development/branches/merge-decisions', { params: { project_id: projectId } });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch merge decisions: ${response.status}`);
  }

  const data: MergeDecisionListResponse = response.data;
  return data.items;
}

interface StateRefListResponse {
  project_id: string;
  items: BranchStateRef[];
  meta: Record<string, string>;
}

export async function getBranchStateRefs(branchId: string, projectId?: string): Promise<BranchStateRef[]> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;
  
  const response = await api.get(`/story-development/branches/${branchId}/state-refs`, { params });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch branch state refs: ${response.status}`);
  }

  const data: StateRefListResponse = response.data;
  return data.items;
}
