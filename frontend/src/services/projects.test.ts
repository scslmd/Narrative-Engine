import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { getProjects, getProject, createProject, deleteProject } from './projects';
import type { ProjectSummaryResponse, ProjectDetailResponse } from '../types/project';

const mockSummary: ProjectSummaryResponse = {
  project_id: 'proj-1',
  project_name: 'Test Project',
  genre: 'sci-fi',
  tone_profile: { primary_tone: 'dark', secondary_tones: ['noir'] },
  story_structure: { structure_type: 'THREE_ACT' },
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const mockDetail: ProjectDetailResponse = {
  ...mockSummary,
  manifest_path: '/data/projects/proj-1/manifest.json',
  project_dir: '/data/projects/proj-1',
  database_exists: true,
  sequence_exists: true,
  chapter_exists: false,
};

describe('projects service', () => {
  describe('getProjects', () => {
    it('returns list of projects', async () => {
      server.use(
        http.get('/v1/projects', () => {
          return HttpResponse.json([mockSummary]);
        }),
      );

      const result = await getProjects();

      expect(result).toHaveLength(1);
      expect(result[0].project_id).toBe('proj-1');
    });

    it('returns empty array when no projects exist', async () => {
      server.use(
        http.get('/v1/projects', () => {
          return HttpResponse.json([]);
        }),
      );

      const result = await getProjects();

      expect(result).toEqual([]);
    });
  });

  describe('getProject', () => {
    it('returns project details by ID', async () => {
      server.use(
        http.get('/v1/projects/proj-1', () => {
          return HttpResponse.json(mockDetail);
        }),
      );

      const result = await getProject('proj-1');

      expect(result.project_id).toBe('proj-1');
      expect(result.database_exists).toBe(true);
    });

    it('throws ApiError on 404', async () => {
      server.use(
        http.get('/v1/projects/proj-missing', () => {
          return HttpResponse.json({ detail: 'Project not found' }, { status: 404 });
        }),
      );

      await expect(getProject('proj-missing')).rejects.toThrow('Project not found');
    });
  });

  describe('createProject', () => {
    it('creates a project with required fields (201)', async () => {
      server.use(
        http.post('/v1/projects/create', async ({ request }) => {
          const body = (await request.json()) as { project_name?: string };
          return HttpResponse.json({ ...mockDetail, project_name: body.project_name }, { status: 201 });
        }),
      );

      const result = await createProject({ project_name: 'New Project' });

      expect(result.project_name).toBe('New Project');
    });
  });

  describe('deleteProject', () => {
    it('deletes a project on 200 response', async () => {
      server.use(
        http.delete('/v1/projects/proj-1', () => {
          return new HttpResponse(null, { status: 200 });
        }),
      );

      await expect(deleteProject('proj-1')).resolves.toBeUndefined();
    });

    it('deletes a project on 204 response', async () => {
      server.use(
        http.delete('/v1/projects/proj-1', () => {
          return new HttpResponse(null, { status: 204 });
        }),
      );

      await expect(deleteProject('proj-1')).resolves.toBeUndefined();
    });

    it('throws ApiError on 404', async () => {
      server.use(
        http.delete('/v1/projects/proj-missing', () => {
          return HttpResponse.json({ detail: 'Project not found' }, { status: 404 });
        }),
      );

      await expect(deleteProject('proj-missing')).rejects.toThrow('Project not found');
    });

    it('throws ApiError on 409 active jobs', async () => {
      server.use(
        http.delete('/v1/projects/proj-1', () => {
          return HttpResponse.json({ detail: 'Cannot delete project with active jobs' }, { status: 409 });
        }),
      );

      await expect(deleteProject('proj-1')).rejects.toThrow();
    });
  });
});

