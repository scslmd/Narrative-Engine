import type { ProjectSummaryResponse, ProjectDetailResponse, ProjectCreateRequest } from '../types/project';
import api from '../lib/api';

export async function getProjects(): Promise<ProjectSummaryResponse[]> {
  const response = await api.get('/projects');

  if (response.status !== 200) {
    throw new Error(`Failed to fetch projects: ${response.status}`);
  }

  return response.data;
}

export async function generateProjectDescription(projectId: string): Promise<{ premise_text: string }> {
  const response = await api.post(`/projects/${projectId}/generate-description`);

  if (response.status !== 200) {
    throw new Error(`Failed to generate description: ${response.status}`);
  }

  return response.data;
}

export async function getProject(projectId: string): Promise<ProjectDetailResponse> {
  const response = await api.get(`/projects/${projectId}`);
  
  if (response.status !== 200) {
    throw new Error(`Failed to fetch project: ${response.status}`);
  }
  
  return response.data;
}

export async function createProject(data: ProjectCreateRequest): Promise<ProjectDetailResponse> {
  const response = await api.post('/projects/create', data);

  if (response.status !== 201) {
    throw new Error(`Failed to create project: ${response.status}`);
  }

  return response.data;
}

export async function deleteProject(projectId: string): Promise<void> {
  await api.delete(`/projects/${projectId}`);
}
