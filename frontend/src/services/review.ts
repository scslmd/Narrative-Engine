import type { CheckerFinding, ReviewDecision, FindingsFilter, ReviewDecisionCreateRequest } from '../types/review';
import api from '../lib/api';

interface FindingListResponse {
  project_id: string;
  items: CheckerFinding[];
  meta: Record<string, string>;
}

export async function getFindings(filter: FindingsFilter): Promise<CheckerFinding[]> {
  const params: Record<string, string | undefined> = {
    project_id: filter.project_id,
  };
  
  if (filter.source_object_kind) {
    params.source_object_kind = filter.source_object_kind;
  }

  if (filter.severity && filter.severity.length > 0) {
    params.severity = filter.severity.join(',');
  }

  const response = await api.get('/story-development/review/findings', { params });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch findings: ${response.status}`);
  }

  const data: FindingListResponse = response.data;
  return data.items;
}

export async function getFindingById(findingId: string): Promise<CheckerFinding> {
  const response = await api.get(`/story-development/review/findings/${findingId}`);
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch finding: ${response.status}`);
  }

  return response.data;
}

interface DecisionListResponse {
  project_id: string;
  items: ReviewDecision[];
  meta: Record<string, string>;
}

export async function getDecisionsForFinding(findingId: string): Promise<ReviewDecision[]> {
  const response = await api.get('/story-development/review/decisions', { params: { target_id: findingId } });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch decisions: ${response.status}`);
  }

  const data: DecisionListResponse = response.data;
  return data.items;
}

export async function createDecision(request: ReviewDecisionCreateRequest): Promise<ReviewDecision> {
  const response = await api.post('/story-development/review/decisions', request);

  if (response.status !== 201) {
    throw new Error(`Failed to create decision: ${response.status}`);
  }

  return response.data;
}
