import type { ProjectSummaryResponse, ProjectDetailResponse, ProjectCreateRequest } from '../types/project';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function getProjects(): Promise<ProjectSummaryResponse[]> {
  const response = await fetch(`${API_BASE}/projects`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch projects: ${response.status}`);
  }
  
  return response.json();
}

export async function getProject(projectId: string): Promise<ProjectDetailResponse> {
  const response = await fetch(`${API_BASE}/projects/${projectId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch project: ${response.status}`);
  }
  
  return response.json();
}

export async function createProject(data: ProjectCreateRequest): Promise<ProjectDetailResponse> {
  const response = await fetch(`${API_BASE}/projects/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create project: ${response.status}`);
  }
  
  return response.json();
}
