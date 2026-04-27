import type { ExtractPatternsRequest, PatternExtractionRequest, PatternExtractionResponse } from '../types/patternExtraction';
import api from '../lib/api';

export async function importPatterns(request: PatternExtractionRequest): Promise<PatternExtractionResponse> {
  const response = await api.post('/projects/import-patterns', request);

  if (response.status !== 201) {
    throw new Error(`Failed to import patterns: ${response.status}`);
  }

  return response.data;
}

export async function extractPatternsPostImport(
  projectId: string,
  request: ExtractPatternsRequest,
): Promise<PatternExtractionResponse> {
  const response = await api.post(`/projects/${projectId}/extract-patterns`, request);

  if (response.status !== 201) {
    throw new Error(`Failed to extract patterns post-import: ${response.status}`);
  }

  return response.data;
}
