import type { StoryBranch, BranchComparisonRecord, BranchMergeDecision, BranchStateRef } from '../types/branches';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface BranchListResponse {
  project_id: string;
  items: StoryBranch[];
  meta: Record<string, string>;
}

export async function getBranches(projectId: string): Promise<StoryBranch[]> {
  const response = await fetch(`${API_BASE}/v1/story-development/branches?project_id=${projectId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch branches: ${response.statusText}`);
  }

  const data: BranchListResponse = await response.json();
  return data.items;
}

export async function createBranch(projectId: string, name: string, description?: string, parentBranchId?: string): Promise<StoryBranch> {
  const response = await fetch(`${API_BASE}/v1/story-development/branches`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ project_id: projectId, name, description, parent_branch_id: parentBranchId }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create branch: ${response.statusText}`);
  }

  return response.json();
}

export async function getActiveBranch(projectId: string): Promise<StoryBranch | null> {
  const response = await fetch(`${API_BASE}/v1/story-development/branches/active?project_id=${projectId}`);
  
  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch active branch: ${response.statusText}`);
  }

  return response.json();
}

export async function setActiveBranch(projectId: string, branchId: string): Promise<StoryBranch> {
  const response = await fetch(`${API_BASE}/v1/story-development/branches/active`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ project_id: projectId, branch_id: branchId }),
  });

  if (!response.ok) {
    throw new Error(`Failed to set active branch: ${response.statusText}`);
  }

  return response.json();
}

export async function createBranchComparison(projectId: string, branchAId: string, branchBId: string): Promise<BranchComparisonRecord> {
  const response = await fetch(`${API_BASE}/v1/story-development/branches/comparisons`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ project_id: projectId, branch_a_id: branchAId, branch_b_id: branchBId }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create comparison: ${response.statusText}`);
  }

  return response.json();
}

interface ComparisonListResponse {
  project_id: string;
  items: BranchComparisonRecord[];
  meta: Record<string, string>;
}

export async function getComparisons(projectId: string): Promise<BranchComparisonRecord[]> {
  const response = await fetch(`${API_BASE}/v1/story-development/branches/comparisons?project_id=${projectId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch comparisons: ${response.statusText}`);
  }

  const data: ComparisonListResponse = await response.json();
  return data.items;
}

export async function getComparison(comparisonId: string): Promise<BranchComparisonRecord> {
  const response = await fetch(`${API_BASE}/v1/story-development/branches/comparisons/${comparisonId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch comparison: ${response.statusText}`);
  }

  return response.json();
}

export async function createMergeDecision(projectId: string, sourceBranchId: string, targetBranchId: string, decision: 'merge' | 'reject' | 'defer', rationale?: string): Promise<BranchMergeDecision> {
  const response = await fetch(`${API_BASE}/v1/story-development/branches/merge-decisions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ project_id: projectId, source_branch_id: sourceBranchId, target_branch_id: targetBranchId, decision, rationale }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create merge decision: ${response.statusText}`);
  }

  return response.json();
}

interface MergeDecisionListResponse {
  project_id: string;
  items: BranchMergeDecision[];
  meta: Record<string, string>;
}

export async function getMergeDecisions(projectId: string): Promise<BranchMergeDecision[]> {
  const response = await fetch(`${API_BASE}/v1/story-development/branches/merge-decisions?project_id=${projectId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch merge decisions: ${response.statusText}`);
  }

  const data: MergeDecisionListResponse = await response.json();
  return data.items;
}

interface StateRefListResponse {
  project_id: string;
  items: BranchStateRef[];
  meta: Record<string, string>;
}

export async function getBranchStateRefs(branchId: string): Promise<BranchStateRef[]> {
  const response = await fetch(`${API_BASE}/v1/story-development/branches/${branchId}/state-refs`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch branch state refs: ${response.statusText}`);
  }

  const data: StateRefListResponse = await response.json();
  return data.items;
}
