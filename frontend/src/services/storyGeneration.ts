import api from '../lib/api';
import type {
  CanonForkPreviewResponse,
  CanonGenerationPacket,
  CanonGenerationRequest,
  GenerationGateResult,
  GenerationRunResponse,
} from '../types/storyGeneration';

export async function createGenerationRun(
  request: CanonGenerationRequest,
): Promise<GenerationRunResponse> {
  const response = await api.post('/v1/story-generation/runs', request);
  return response.data;
}

export async function getGenerationRun(generationId: string): Promise<GenerationRunResponse> {
  const response = await api.get(`/v1/story-generation/runs/${generationId}`);
  return response.data;
}

export async function listGenerationRuns(projectId: string): Promise<GenerationRunResponse[]> {
  const response = await api.get('/v1/story-generation/runs', { params: { project_id: projectId } });
  return response.data;
}

export async function retryGenerationRun(generationId: string): Promise<GenerationRunResponse> {
  const response = await api.post(`/v1/story-generation/runs/${generationId}/retry`);
  return response.data;
}

export async function getGenerationPacket(generationId: string): Promise<CanonGenerationPacket> {
  const response = await api.get(`/v1/story-generation/runs/${generationId}/packet`);
  return response.data;
}

export async function getGenerationGates(generationId: string): Promise<GenerationGateResult[]> {
  const response = await api.get(`/v1/story-generation/runs/${generationId}/gates`);
  return response.data.items;
}

export async function previewFork(request: CanonGenerationRequest): Promise<CanonForkPreviewResponse> {
  const response = await api.post('/v1/story-generation/fork-preview', request);
  return response.data;
}

export async function createForkProject(request: CanonGenerationRequest): Promise<GenerationRunResponse> {
  const response = await api.post('/v1/story-generation/fork-project', request);
  return response.data;
}
