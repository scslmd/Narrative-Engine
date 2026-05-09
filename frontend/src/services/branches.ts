import type { BranchRecord, MergeDecisionRecord, StoryBranch, BranchComparisonRecord, BranchMergeDecision, BranchStateRef } from '../types/branches';
import api from '../lib/api';

interface BranchListResponse {
  project_id: string;
  items: StoryBranch[];
  meta: Record<string, string>;
}

export async function getBranches(projectId: string): Promise<StoryBranch[]> {
  const response = await api.get('/v1/story-development/branches', { params: { project_id: projectId } });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch branches: ${response.status}`);
  }

  const data: BranchListResponse = response.data;
  return data.items;
}

export async function setActiveBranch(projectId: string, branchId: string): Promise<StoryBranch> {
  const response = await api.post('/v1/story-development/branches/active', { 
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
  const response = await api.post('/v1/story-development/branches/comparisons', {
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
  const response = await api.post('/v1/story-development/branches/merge-decisions', {
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

export async function getBranch(
  branchId: string,
  projectId?: string,
): Promise<BranchRecord> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;

  const response = await api.get(`/v1/story-development/branches/${branchId}`, { params });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch branch: ${response.status}`);
  }

  return response.data;
}

export async function getBranchComparison(
  comparisonId: string,
  projectId?: string,
): Promise<BranchComparisonRecord> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;

  const response = await api.get(
    `/v1/story-development/branches/comparisons/${comparisonId}`,
    { params },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch comparison: ${response.status}`);
  }

  return response.data;
}

export async function getMergeDecision(
  decisionId: string,
  projectId?: string,
): Promise<MergeDecisionRecord> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;

  const response = await api.get(
    `/v1/story-development/branches/merge-decisions/${decisionId}`,
    { params },
  );

  if (response.status !== 200) {
    throw new Error(`Failed to fetch merge decision: ${response.status}`);
  }

  return response.data;
}

export async function getBranchStateRefs(
  branchId: string,
  projectId?: string,
): Promise<BranchStateRef[]> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;

  const response = await api.get(`/v1/story-development/branches/${branchId}/state-refs`, { params });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch state refs: ${response.status}`);
  }

  return response.data;
}

