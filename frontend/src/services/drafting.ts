import type { DraftArtifact, PromotedManuscript } from '../types/drafting';
import * as mockService from './mocks/draftingMock';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export async function getDraftArtifacts(projectId: string): Promise<DraftArtifact[]> {
  if (USE_MOCKS) {
    return mockService.getDraftArtifacts(projectId);
  }
  
  const response = await fetch(`/story-development/drafting/draft-artifacts?project_id=${projectId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch draft artifacts');
  }
  return response.json();
}

export async function promoteDraft(artifactId: string): Promise<PromotedManuscript> {
  if (USE_MOCKS) {
    const result = await mockService.promoteDraft(artifactId);
    console.log('Mock promotion successful:', result.document_id);
    return result;
  }
  
  throw new Error('Backend endpoint not yet available - use VITE_USE_MOCKS=true for mock mode');
}

export function isMockMode(): boolean {
  return USE_MOCKS;
}
