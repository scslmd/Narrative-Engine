import type { DraftArtifact, ManuscriptDocument, PromoteDraftToManuscriptRequest } from '../types/drafting';
import type { RevisionSuggestion } from '../types/aids';
import api from '../lib/api';

interface DraftArtifactListResponse {
  project_id: string;
  items: DraftArtifact[];
  meta: Record<string, string>;
}

interface ManuscriptDocumentListResponse {
  project_id: string;
  items: ManuscriptDocument[];
  meta: Record<string, string>;
}

interface RevisionSuggestionListResponse {
  project_id: string;
  items: RevisionSuggestion[];
  meta: Record<string, string>;
}

export async function getDraftArtifacts(projectId: string): Promise<DraftArtifact[]> {
  const response = await api.get('/story-development/drafting/draft-artifacts', { params: { project_id: projectId } });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch draft artifacts: ${response.status}`);
  }

  const data: DraftArtifactListResponse = response.data;
  return data.items;
}

export async function getDraftArtifact(artifactId: string, projectId: string): Promise<DraftArtifact> {
  const response = await api.get(`/story-development/drafting/draft-artifacts/${artifactId}`, { params: { project_id: projectId } });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch draft artifact: ${response.status}`);
  }

  return response.data;
}

export async function getManuscriptDocuments(projectId: string): Promise<ManuscriptDocument[]> {
  const response = await api.get('/story-development/drafting/manuscript-documents', { params: { project_id: projectId } });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch manuscript documents: ${response.status}`);
  }

  const data: ManuscriptDocumentListResponse = response.data;
  return data.items;
}

export async function getManuscriptDocument(documentId: string, projectId: string): Promise<ManuscriptDocument> {
  const response = await api.get(`/story-development/drafting/manuscript-documents/${documentId}`, { params: { project_id: projectId } });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch manuscript document: ${response.status}`);
  }

  return response.data;
}

export async function createManuscriptDocument(request: ManuscriptDocument): Promise<ManuscriptDocument> {
  const response = await api.post('/story-development/drafting/manuscript-documents', request);
  
  if (response.status !== 201) {
    throw new Error(`Failed to create manuscript document: ${response.status}`);
  }
  
  return response.data;
}

export async function promoteDraftToManuscript(request: PromoteDraftToManuscriptRequest): Promise<ManuscriptDocument> {
  const response = await api.post('/story-development/drafting/promote-draft', request);
  
  if (response.status !== 201) {
    throw new Error(`Failed to promote draft: ${response.status}`);
  }
  
  return response.data;
}

export async function getRevisionSuggestions(projectId: string, targetDocumentId?: string): Promise<RevisionSuggestion[]> {
  const params: Record<string, string> = { project_id: projectId };
  if (targetDocumentId) {
    params.target_document_id = targetDocumentId;
  }
  
  const response = await api.get('/story-development/drafting/revision-suggestions', { params });
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch revision suggestions: ${response.status}`);
  }

  const data: RevisionSuggestionListResponse = response.data;
  return data.items;
}

export async function createRevisionSuggestion(request: RevisionSuggestion): Promise<RevisionSuggestion> {
  const response = await api.post('/story-development/drafting/revision-suggestions', request);
  
  if (response.status !== 201) {
    throw new Error(`Failed to create revision suggestion: ${response.status}`);
  }
  
  return response.data;
}

export async function updateManuscriptContent(
  documentId: string,
  projectId: string,
  content: string,
): Promise<ManuscriptDocument> {
  const response = await api.patch(
    `/story-development/drafting/manuscript-documents/${documentId}`,
    { content },
    { params: { project_id: projectId } },
  );
  
  if (response.status !== 200) {
    throw new Error(`Failed to update manuscript content: ${response.status}`);
  }
  
  return response.data;
}

export async function triggerManuscriptReview(
  documentId: string,
  projectId: string,
): Promise<RevisionSuggestion[]> {
  const response = await api.post(
    `/story-development/drafting/manuscript-documents/${documentId}/review`,
    null,
    { params: { project_id: projectId } },
  );
  
  if (response.status !== 202) {
    throw new Error(`Failed to trigger manuscript review: ${response.status}`);
  }
  
  return response.data.findings ?? [];
}
