import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, ProjectCreateRequest } from '../lib/projectsApi';
import { useToastStore } from '../stores/toastStore';

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  });
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId],
    queryFn: () => projectsApi.get(projectId),
    enabled: !!projectId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  const addToast = useToastStore((state) => state.addToast);

  return useMutation({
    mutationFn: (data: ProjectCreateRequest) => projectsApi.create(data),
    onSuccess: () => {
      addToast('Project created successfully', 'success');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to create project';
      addToast(message, 'error');
    },
  });
}

export function useProjectManifest(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId, 'manifest'],
    queryFn: () => projectsApi.getManifest(projectId),
    enabled: !!projectId,
  });
}

export function useProjectSequence(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId, 'sequence'],
    queryFn: () => projectsApi.getSequence(projectId),
    enabled: !!projectId,
  });
}

export function useProjectChapters(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId, 'chapters'],
    queryFn: () => projectsApi.getChapters(projectId),
    enabled: !!projectId,
  });
}

export function useChapterContent(chapterId: string) {
  return useQuery({
    queryKey: ['chapters', chapterId],
    queryFn: () => projectsApi.getChapterContent(chapterId),
    enabled: !!chapterId,
  });
}
