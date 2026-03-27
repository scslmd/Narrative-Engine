import { useState, useEffect, useCallback } from 'react';
import type { ArtifactLineageView } from '../types/inspect';
import api from '../lib/api';

interface UseJobLineageResult {
  artifacts: ArtifactLineageView[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useJobLineage(jobId: string, attemptNumber?: number): UseJobLineageResult {
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

      const response = await api.get(`/jobs/${jobId}/lineage`, { params });
      
      if (response.status !== 200) {
        throw new Error(`Failed to fetch lineage: ${response.status}`);
      }

      setArtifacts(response.data.artifacts || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setArtifacts([]);
    } finally {
      setLoading(false);
    }
  }, [jobId, attemptNumber]);

  useEffect(() => {
    fetchLineage();
  }, [fetchLineage]);

  return { artifacts, loading, error, refetch: fetchLineage };
}
