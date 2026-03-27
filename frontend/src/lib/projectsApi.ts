import api from './api';

export interface ManifestConfig {
  genre: string;
  tone_profile: string;
  pov: 'First' | 'Third_Limited' | 'Third_Omni';
  primary_language: string;
  secondary_language: string;
  story_structure: 'SAVE_THE_CAT' | 'THREE_ACT';
}

export interface ProjectCreateRequest {
  project_id?: string;
  project_name: string;
  config: ManifestConfig;
  constraints?: string[];
  premise_text?: string;
}

export interface ProjectSummary {
  project_id: string;
  project_name: string;
  genre: string;
  tone_profile: string;
  story_structure: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends ProjectSummary {
  manifest: {
    project_id: string;
    project_name: string;
    config: ManifestConfig;
    constraints: string[];
    premise_text?: string;
  };
  project_dir: string;
  database_exists: boolean;
  sequence_exists: boolean;
  chapter_exists: boolean;
  export_count: number;
}

export interface ProjectArtifact {
  project_id: string;
  artifact_name: string;
  content: string;
  updated_at: string;
}

export interface SequenceData {
  beats: Array<{
    beat_id?: string;
    beat_number: number;
    title: string;
    description: string;
    purpose?: string;
    emotional_tone?: string;
  }>;
  updated_at: string;
}

export interface ManifestData {
  project_id: string;
  project_name: string;
  config: ManifestConfig;
  constraints: string[];
  premise_text?: string;
  updated_at: string;
}

export interface ChapterSummary {
  chapter_id: string;
  chapter_number: number;
  title?: string;
  beat_count: number;
}

export interface ChapterContent {
  chapter_id: string;
  content: string;
  updated_at: string;
}

export const projectsApi = {
  list: async (): Promise<ProjectSummary[]> => {
    const response = await api.get('/projects');
    return response.data;
  },

  create: async (request: ProjectCreateRequest): Promise<ProjectDetail> => {
    const response = await api.post('/projects/create', request);
    return response.data;
  },

  get: async (projectId: string): Promise<ProjectDetail> => {
    const response = await api.get(`/projects/${projectId}`);
    return response.data;
  },

  getManifest: async (projectId: string): Promise<ManifestData> => {
    const response = await api.get(`/projects/${projectId}/manifest`);
    return response.data;
  },

  getSequence: async (projectId: string): Promise<SequenceData> => {
    const response = await api.get(`/projects/${projectId}/sequence`);
    return response.data;
  },

  getChapter: async (projectId: string): Promise<ProjectArtifact> => {
    const response = await api.get(`/projects/${projectId}/chapter-1`);
    return response.data;
  },

  getChapters: async (projectId: string): Promise<ChapterSummary[]> => {
    const response = await api.get(`/projects/${projectId}/chapters`);
    return response.data;
  },

  getChapterContent: async (chapterId: string): Promise<ChapterContent> => {
    const response = await api.get(`/chapters/${chapterId}`);
    return response.data;
  },
};
