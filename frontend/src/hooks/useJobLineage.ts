import { useState, useEffect, useCallback } from 'react';
import type { ArtifactLineageView } from '../types/inspect';
import api from '../lib/api';

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
      const params: Record<string, string> = {};
      if (attemptNumber !== undefined) {
        params.attempt = attemptNumber.toString();
      }

      const endpoint = runKind === 'pipeline_job' 
        ? `/jobs/${jobId}/lineage`
        : `/role-model-checker/${jobId}/lineage`;
      
      const response = await api.get(endpoint, { params });
      
      if (response.status !== 200) {
        throw new Error(`Failed to fetch lineage: ${response.status}`);
      }

      setArtifacts(response.data.items || []);
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
