import api from '../lib/api';
import type {
  MythosEntry,
  MythosEntryCreateRequest,
  MythosEntryType,
  MythosEntryUpdateRequest,
} from '../types/mythos';

export async function getMythosEntries(projectId: string, entryType?: MythosEntryType): Promise<MythosEntry[]> {
  const response = await api.get('/v1/mythos/entries', {
    params: {
      project_id: projectId,
      entry_type: entryType,
    },
  });
  return response.data;
}

export async function createMythosEntry(request: MythosEntryCreateRequest): Promise<MythosEntry> {
  const response = await api.post('/v1/mythos/entries', request);
  return response.data;
}

export async function updateMythosEntry(
  mythosId: string,
  projectId: string,
  updates: MythosEntryUpdateRequest,
): Promise<MythosEntry> {
  const response = await api.patch(`/v1/mythos/entries/${mythosId}`, updates, {
    params: { project_id: projectId },
  });
  return response.data;
}

export async function deleteMythosEntry(projectId: string, mythosId: string): Promise<void> {
  await api.delete(`/v1/mythos/entries/${mythosId}`, { params: { project_id: projectId } });
}

export async function materializeMythosExtraction(
  projectId: string,
  extractionId: string,
): Promise<MythosEntry[]> {
  const response = await api.post('/v1/mythos/materialize-extraction', null, {
    params: {
      project_id: projectId,
      extraction_id: extractionId,
    },
  });
  return response.data;
}
