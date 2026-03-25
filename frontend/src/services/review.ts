import type { CheckerFinding, ReviewDecision, FindingsFilter } from '../types/review';

interface FindingListResponse {
  project_id: string;
  items: CheckerFinding[];
  meta: Record<string, string>;
}

export async function getFindings(filter: FindingsFilter): Promise<CheckerFinding[]> {
  const params = new URLSearchParams();
  params.set('project_id', filter.project_id);
  
  if (filter.source_object_kind) {
    params.set('source_object_kind', filter.source_object_kind);
  }
  
  if (filter.severity && filter.severity.length > 0) {
    params.set('severity', filter.severity.join(','));
  }

  const response = await fetch(`/api/story-development/review/findings?${params}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch findings: ${response.statusText}`);
  }

  const data: FindingListResponse = await response.json();
  return data.items;
}

export async function getFindingById(findingId: string): Promise<CheckerFinding> {
  const response = await fetch(`/api/story-development/review/findings/${findingId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch finding: ${response.statusText}`);
  }

  return response.json();
}

interface DecisionListResponse {
  project_id: string;
  items: ReviewDecision[];
  meta: Record<string, string>;
}

export async function getDecisionsForFinding(findingId: string): Promise<ReviewDecision[]> {
  const params = new URLSearchParams();
  params.set('finding_id', findingId);

  const response = await fetch(`/api/story-development/review/decisions?${params}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch decisions: ${response.statusText}`);
  }

  const data: DecisionListResponse = await response.json();
  return data.items;
}

export async function createDecision(decision: Omit<ReviewDecision, 'decision_id' | 'created_at'>): Promise<ReviewDecision> {
  const response = await fetch('/api/story-development/review/decisions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(decision),
  });

  if (!response.ok) {
    throw new Error(`Failed to create decision: ${response.statusText}`);
  }

  return response.json();
}
