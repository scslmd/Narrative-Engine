import type { StoryBranch, BranchComparisonRecord, BranchMergeDecision, BranchStateRef } from '../types/branches';
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

export async function createBranch(projectId: string, name: string, description?: string, parentBranchId?: string): Promise<StoryBranch> {
  const response = await api.post('/story-development/branches', { project_id: projectId, name, description, parent_branch_id: parentBranchId });

  if (response.status !== 201) {
    throw new Error(`Failed to create branch: ${response.status}`);
  }

  return response.data;
}

export async function getActiveBranch(projectId: string): Promise<StoryBranch | null> {
  const response = await api.get('/story-development/branches/active', { params: { project_id: projectId } });
  
  if (response.status === 404) {
    return null;
  }

  if (response.status !== 200) {
    throw new Error(`Failed to fetch active branch: ${response.status}`);
  }

  return response.data;
}

export async function setActiveBranch(projectId: string, branchId: string): Promise<StoryBranch> {
  const response = await api.post('/story-development/branches/active', { project_id: projectId, branch_id: branchId });

  if (response.status !== 200) {
    throw new Error(`Failed to set active branch: ${response.status}`);
  }

  return response.data;
}

export async function createBranchComparison(projectId: string, branchAId: string, branchBId: string): Promise<BranchComparisonRecord> {
  const response = await api.post('/story-development/branches/comparisons', { project_id: projectId, branch_a_id: branchAId, branch_b_id: branchBId });

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

export async function getComparison(comparisonId: string): Promise<BranchComparisonRecord> {
  const response = await api.get(`/story-development/branches/comparisons/${comparisonId}`);
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch comparison: ${response.status}`);
  }

  return response.data;
}

export async function createMergeDecision(projectId: string, sourceBranchId: string, targetBranchId: string, decision: 'merge' | 'reject' | 'defer', rationale?: string): Promise<BranchMergeDecision> {
  const response = await api.post('/story-development/branches/merge-decisions', { project_id: projectId, source_branch_id: sourceBranchId, target_branch_id: targetBranchId, decision, rationale });

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

export async function getBranchStateRefs(branchId: string): Promise<BranchStateRef[]> {
  const response = await api.get(`/story-development/branches/${branchId}/state-refs`);
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch branch state refs: ${response.status}`);
  }

  const data: StateRefListResponse = response.data;
  return data.items;
}
