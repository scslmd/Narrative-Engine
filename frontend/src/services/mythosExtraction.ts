import type { MythosExtractionRequest } from '../types/mythosExtraction';
import type { ExtractionSubmitResponse } from '../types/extractionProgress';
import api from '../lib/api';

export async function submitMythosExtraction(data: MythosExtractionRequest): Promise<ExtractionSubmitResponse> {
  const response = await api.post('/v1/projects/import-mythos', data);
  return response.data;
}

export { getExtractionStatus } from './patternExtraction';

