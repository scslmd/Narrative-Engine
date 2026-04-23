import type { StoryImportRequest, StoryImportResponse } from '../types/storyImport';
import api from '../lib/api';

export async function importStory(data: StoryImportRequest): Promise<StoryImportResponse> {
  const response = await api.post('/projects/import-story', data);

  if (response.status !== 201) {
    throw new Error(`Failed to import story: ${response.status}`);
  }

  return response.data;
}
