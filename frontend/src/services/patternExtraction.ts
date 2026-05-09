import type { ExtractPatternsRequest, PatternExtractionRequest } from '../types/patternExtraction';
import type { ExtractionSubmitResponse, ExtractionProgressResponse } from '../types/extractionProgress';
import api from '../lib/api';

export async function submitPatternExtraction(request: PatternExtractionRequest): Promise<ExtractionSubmitResponse> {
  const response = await api.post('/v1/projects/import-patterns', request);
  return response.data;
}

export async function submitProjectPatternExtraction(
  projectId: string,
  request: ExtractPatternsRequest,
): Promise<ExtractionSubmitResponse> {
  const response = await api.post(`/v1/projects/${projectId}/extract-patterns`, request);
  return response.data;
}

export async function getExtractionStatus(extractionId: string): Promise<ExtractionProgressResponse> {
  const response = await api.get(`/v1/projects/extraction/${extractionId}`);
  return response.data;
}

