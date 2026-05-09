import type {
  StoryImportRequest,
  StoryImportResponse,
  ImportSubmitResponse,
  ImportProgress,
} from '../types/storyImport';
import api from '../lib/api';

export async function submitImport(
  formData: FormData,
): Promise<ImportSubmitResponse> {
  const response = await api.post('/v1/projects/import-story', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  if (response.status !== 202) {
    throw new Error(`Failed to submit import: ${response.status}`);
  }

  return response.data;
}

export async function getImportStatus(
  importId: string,
): Promise<ImportProgress> {
  const response = await api.get(`/v1/projects/import/${importId}`);

  if (response.status !== 200) {
    throw new Error(`Failed to get import status: ${response.status}`);
  }

  return response.data;
}

// Backward compatible â€” submits and polls until done
export async function importStory(
  data: StoryImportRequest,
): Promise<StoryImportResponse> {
  const formData = new FormData();
  formData.append('story_text', data.story_text);
  formData.append('project_name', data.project_name);
  if (data.genre) formData.append('genre', data.genre);
  if (data.tone) formData.append('tone', data.tone);
  if (data.project_id) formData.append('project_id', data.project_id);

  const submit = await submitImport(formData);
  return await _pollForCompletion(submit.import_id);
}

async function _pollForCompletion(
  importId: string,
  intervalMs: number = 2000,
  maxAttempts: number = 300,
): Promise<StoryImportResponse> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const progress = await getImportStatus(importId);

    if (progress.status === 'completed' && progress.result) {
      return progress.result;
    }

    if (progress.status === 'failed') {
      throw new Error(progress.error || 'Import failed');
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error('Import timed out');
}

