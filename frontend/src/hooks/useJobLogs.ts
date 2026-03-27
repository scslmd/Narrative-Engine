import { useQuery } from '@tanstack/react-query';
import { jobsService } from '../services/jobs';

interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR';
  message: string;
}

export function useJobLogs(jobId: string | null) {
  const { data, isLoading, error } = useQuery<{ id: string; entries: LogEntry[] }>({
    queryKey: ['job-logs', jobId],
    queryFn: () => jobsService.getLogs(jobId!),
    enabled: !!jobId,
    refetchInterval: 1000,
    retry: 3,
  });

  return {
    logs: data?.entries || [],
    isLoading,
    error: error instanceof Error ? error.message : null,
  };
}
