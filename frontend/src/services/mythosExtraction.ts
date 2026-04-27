import type { MythosExtractionRequest, MythosExtractionResponse } from '../types/mythosExtraction';
import api from '../lib/api';

export async function extractMythos(data: MythosExtractionRequest): Promise<MythosExtractionResponse> {
  const response = await api.post('/projects/import-mythos', data);

  if (response.status !== 201) {
    throw new Error(`Failed to extract mythos: ${response.status}`);
  }

  return response.data;
}
