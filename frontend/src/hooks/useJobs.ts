import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, JobCreateRequest } from '../lib/jobsApi';
import { useToastStore } from '../stores/toastStore';

export function useJobs(projectId: string) {
  return useQuery({
    queryKey: ['jobs', projectId],
    queryFn: () => jobsApi.list(projectId),
    enabled: !!projectId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data || data.length === 0) return false;
      
      const hasProcessingJob = data.some(
        (job) => job.status === 'PROCESSING' || job.status === 'PENDING'
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
      
      if (data.status === 'PROCESSING' || data.status === 'PENDING') {
        return 1000;
      }
      return false;
    },
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  const addToast = useToastStore((state) => state.addToast);

  return useMutation({
    mutationFn: (data: JobCreateRequest) => jobsApi.create(data),
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
