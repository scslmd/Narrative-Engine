import type { DraftArtifact, ManuscriptDocument, PromoteDraftToManuscriptRequest } from '../types/drafting';
import * as mockService from './mocks/draftingMock';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export async function getDraftArtifacts(projectId: string): Promise<DraftArtifact[]> {
  if (USE_MOCKS) {
    return mockService.getDraftArtifacts(projectId);
  }
  
  const response = await fetch(`${API_BASE}/v1/story-development/drafting/draft-artifacts?project_id=${projectId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch draft artifacts: ${response.status}`);
  }
  const data = await response.json();
  return data.items || [];
}

export async function promoteDraftToManuscript(request: PromoteDraftToManuscriptRequest): Promise<ManuscriptDocument> {
  if (USE_MOCKS) {
    const result = await mockService.promoteDraft(request.draft_artifact_id);
    console.log('Mock promotion successful:', result.document_id);
    return {
      document_id: result.document_id,
      project_id: request.project_id,
      title: result.title,
      content: result.content,
      chapter_id: null,
      scene_id: null,
      current_draft_artifact_id: request.draft_artifact_id,
      version: 1,
    };
  }
  
  const response = await fetch(`${API_BASE}/v1/story-development/drafting/promote-draft`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to promote draft: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export function isMockMode(): boolean {
  return USE_MOCKS;
}
