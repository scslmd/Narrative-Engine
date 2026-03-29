import { useState, useEffect, useCallback } from 'react';
import type { StepRecord } from '../types/inspect';
import api from '../lib/api';

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
      const params: Record<string, string> = {};
      if (attemptNumber !== undefined) {
        params.attempt = attemptNumber.toString();
      }

      const endpoint = runKind === 'pipeline_job' 
        ? `/jobs/${jobId}/steps`
        : `/role-model-checker/${jobId}/steps`;
      
      const response = await api.get(endpoint, { params });
      
      if (response.status !== 200) {
        throw new Error(`Failed to fetch steps: ${response.status}`);
      }

      setSteps(response.data.items || []);
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
