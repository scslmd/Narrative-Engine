import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, JobPhase } from '../lib/jobsApi';
import { useToastStore } from '../stores/toastStore';

export function useJobs(projectId: string | undefined) {
  return useQuery({
    queryKey: ['jobs', projectId],
    queryFn: () => jobsApi.list(projectId!),
    enabled: !!projectId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data || data.length === 0) return false;
      
      const hasProcessingJob = data.some(
        (job) => job.status === 'RUNNING' || job.status === 'QUEUED'
      );
      return hasProcessingJob ? 2000 : false;
    },
  });
}

export function useJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ['jobs', jobId],
    queryFn: () => jobsApi.get(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      
      if (data.status === 'RUNNING' || data.status === 'QUEUED') {
        return 1000;
      }
      return false;
    },
  });
}

export function useCreateJob(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const addToast = useToastStore((state) => state.addToast);

  return useMutation({
    mutationFn: (phase: JobPhase) => {
      if (!projectId) {
        throw new Error('No project ID provided');
      }
      return jobsApi.create({ project_id: projectId, phase });
    },
    onSuccess: (data) => {
      addToast(`Job ${data.phase} started successfully`, 'success');
      queryClient.invalidateQueries({ queryKey: ['jobs', data.project_id] });
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to create job';
      addToast(message, 'error');
    },
  });
}

export function useJobLogs(jobId: string | undefined) {
  return useQuery({
    queryKey: ['jobs', jobId, 'logs'],
    queryFn: () => jobsApi.getLogs(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      
      return 2000;
    },
  });
}
