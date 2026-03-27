import type { DraftArtifact, ManuscriptDocument, PromoteDraftToManuscriptRequest } from '../types/drafting';
import * as mockService from './mocks/draftingMock';
import api from '../lib/api';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

interface DraftArtifactListResponse {
  project_id: string;
  items: DraftArtifact[];
  meta: Record<string, string>;
}

export async function getDraftArtifacts(projectId: string): Promise<DraftArtifact[]> {
  if (USE_MOCKS) {
    return mockService.getDraftArtifacts(projectId);
  }
  
  const response = await api.get('/story-development/drafting/draft-artifacts', { params: { project_id: projectId } });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch draft artifacts: ${response.status}`);
  }

  const data: DraftArtifactListResponse = response.data;
  return data.items;
}

export async function promoteDraftToManuscript(request: PromoteDraftToManuscriptRequest): Promise<ManuscriptDocument> {
  if (USE_MOCKS) {
    const result = await mockService.promoteDraft(request.draft_artifact_id);
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
  
  const response = await api.post('/story-development/drafting/promote-draft', request);
  
  if (response.status !== 201) {
    throw new Error(`Failed to promote draft: ${response.status}`);
  }
  
  return response.data;
}

export function isMockMode(): boolean {
  return USE_MOCKS;
}
