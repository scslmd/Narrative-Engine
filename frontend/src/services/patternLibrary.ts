import api from '../lib/api';
import type {
  PatternEntry,
  PatternEntryCreateRequest,
  PatternEntryType,
  PatternEntryUpdateRequest,
} from '../types/patterns';

export async function getPatternEntries(
  projectId: string,
  patternType?: PatternEntryType,
): Promise<PatternEntry[]> {
  const response = await api.get('/v1/patterns/entries', {
    params: {
      project_id: projectId,
      pattern_type: patternType,
    },
  });
  return response.data;
}

export async function createPatternEntry(request: PatternEntryCreateRequest): Promise<PatternEntry> {
  const response = await api.post('/v1/patterns/entries', request);
  return response.data;
}

export async function updatePatternEntry(
  patternId: string,
  projectId: string,
  updates: PatternEntryUpdateRequest,
): Promise<PatternEntry> {
  const response = await api.patch(`/v1/patterns/entries/${patternId}`, updates, {
    params: { project_id: projectId },
  });
  return response.data;
}

export async function deletePatternEntry(projectId: string, patternId: string): Promise<void> {
  await api.delete(`/v1/patterns/entries/${patternId}`, { params: { project_id: projectId } });
}

export async function materializePatternExtraction(
  projectId: string,
  extractionId: string,
): Promise<PatternEntry[]> {
  const response = await api.post('/v1/patterns/materialize-extraction', null, {
    params: {
      project_id: projectId,
      extraction_id: extractionId,
    },
  });
  return response.data;
}
