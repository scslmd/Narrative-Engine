import { useQuery } from '@tanstack/react-query';
import type { JobStatusResponse } from '../types/job';
import { getStatus } from '../services/jobs';

interface UseJobStatusResult {
  status: JobStatusResponse['status'] | null;
  phase: JobStatusResponse['phase'] | null;
  progress: number | null;
  error: string | null;
  isPolling: boolean;
  currentStep: string | null;
  currentPhase: string | null;
  attemptNumber: number | null;
}

export function useJobStatus(jobId: string | null): UseJobStatusResult {
  const isTerminal = (status: JobStatusResponse['status'] | null) => 
    status === 'COMPLETED' || status === 'FAILED';

  const { data, isLoading, isError } = useQuery<JobStatusResponse>({
    queryKey: ['job-status', jobId],
    queryFn: () => getStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      if (!query.state.data) return 600;
      
      const status = query.state.data.status;
      if (isTerminal(status)) return false;
      
      return 600;
    },
    retry: 3,
    refetchOnWindowFocus: false,
  });

  const progress = data?.progress_current !== undefined && data?.progress_total !== undefined 
    ? Math.round((data.progress_current / data.progress_total) * 100)
    : null;

  const status = data?.status || null;

  return {
    status,
    phase: data?.phase || null,
    progress,
    error: data?.error || (isError ? 'Failed to fetch job status' : null),
    isPolling: isLoading && status !== 'COMPLETED' && status !== 'FAILED',
    currentStep: data?.current_step || null,
    currentPhase: data?.current_phase || null,
    attemptNumber: data?.attempt_number || null,
  };
}
