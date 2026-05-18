import api from '../lib/api';
import { idempotencyKey } from '../lib/idempotencyKey';
import type {
  ApplyAssistSuggestionRequest,
  ApplyAssistSuggestionResponse,
  AssistGateResult,
  LLMRevisionSuggestion,
  ManuscriptAssistRequest,
  ManuscriptAssistResult,
} from '../types/manuscriptAssist';

export async function submitManuscriptAssist(
  request: ManuscriptAssistRequest,
): Promise<ManuscriptAssistResult> {
  const idemKey = idempotencyKey(`assist:${request.project_id}:${request.document_id}:${request.assist_kind}`);
  const response = await api.post('/v1/manuscript-assist/runs', {
    ...request,
    idempotency_key: idemKey,
  });
  return response.data;
}

export async function getManuscriptAssist(assistId: string): Promise<ManuscriptAssistResult> {
  const response = await api.get(`/v1/manuscript-assist/runs/${assistId}`);
  return response.data;
}

export async function listManuscriptAssists(
  projectId: string,
  documentId?: string,
): Promise<ManuscriptAssistResult[]> {
  const response = await api.get('/v1/manuscript-assist/runs', {
    params: { project_id: projectId, document_id: documentId },
  });
  return response.data;
}

export async function retryManuscriptAssist(assistId: string): Promise<ManuscriptAssistResult> {
  const response = await api.post(`/v1/manuscript-assist/runs/${assistId}/retry`);
  return response.data;
}

export async function getManuscriptAssistGates(assistId: string): Promise<AssistGateResult[]> {
  const response = await api.get(`/v1/manuscript-assist/runs/${assistId}/gates`);
  return response.data.items;
}

export async function getLLMSuggestions(
  projectId: string,
  documentId: string,
  status?: string,
): Promise<LLMRevisionSuggestion[]> {
  const response = await api.get('/v1/manuscript-assist/suggestions', {
    params: { project_id: projectId, document_id: documentId, status },
  });
  return response.data.items;
}

export async function applyLLMSuggestion(
  request: ApplyAssistSuggestionRequest,
): Promise<ApplyAssistSuggestionResponse> {
  const response = await api.post(
    `/v1/manuscript-assist/suggestions/${request.suggestion_id}/apply`,
    request,
  );
  return response.data;
}

export async function rejectLLMSuggestion(
  projectId: string,
  suggestionId: string,
): Promise<LLMRevisionSuggestion> {
  const response = await api.post(
    `/v1/manuscript-assist/suggestions/${suggestionId}/reject`,
    null,
    { params: { project_id: projectId } },
  );
  return response.data;
}

export async function archiveLLMSuggestion(
  projectId: string,
  suggestionId: string,
): Promise<LLMRevisionSuggestion> {
  const response = await api.post(
    `/v1/manuscript-assist/suggestions/${suggestionId}/archive`,
    null,
    { params: { project_id: projectId } },
  );
  return response.data;
}
