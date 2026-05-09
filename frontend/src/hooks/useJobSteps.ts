import { useState, useEffect, useCallback } from 'react';
import type { StepRecord } from '../types/inspect';
import { getCheckerSteps } from '../services/checker';
import { getJobSteps } from '../services/jobs';

interface UseJobStepsResult {
  steps: StepRecord[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useJobSteps(jobId: string, runKind: 'pipeline_job' | 'role_model_check', attemptNumber?: number): UseJobStepsResult {
  const [steps, setSteps] = useState<StepRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSteps = useCallback(async () => {
    if (!jobId) return;

    setLoading(true);
    setError(null);

    try {
      const response = runKind === 'pipeline_job'
        ? await getJobSteps(jobId, attemptNumber)
        : await getCheckerSteps(jobId, attemptNumber);
      setSteps(response.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setSteps([]);
    } finally {
      setLoading(false);
    }
  }, [jobId, runKind, attemptNumber]);

  useEffect(() => {
    fetchSteps();
  }, [fetchSteps]);

  return { steps, loading, error, refetch: fetchSteps };
}
