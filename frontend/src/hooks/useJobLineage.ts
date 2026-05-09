import { useState, useEffect, useCallback } from 'react';
import type { ArtifactLineageView } from '../types/inspect';
import { getCheckerLineage } from '../services/checker';
import { getJobLineage } from '../services/jobs';

interface UseJobLineageResult {
  artifacts: ArtifactLineageView[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useJobLineage(jobId: string, runKind: 'pipeline_job' | 'role_model_check', attemptNumber?: number): UseJobLineageResult {
  const [artifacts, setArtifacts] = useState<ArtifactLineageView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLineage = useCallback(async () => {
    if (!jobId) return;

    setLoading(true);
    setError(null);

    try {
      const response = runKind === 'pipeline_job'
        ? await getJobLineage(jobId, attemptNumber)
        : await getCheckerLineage(jobId, attemptNumber);
      setArtifacts(response.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setArtifacts([]);
    } finally {
      setLoading(false);
    }
  }, [jobId, runKind, attemptNumber]);

  useEffect(() => {
    fetchLineage();
  }, [fetchLineage]);

  return { artifacts, loading, error, refetch: fetchLineage };
}
