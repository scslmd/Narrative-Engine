import { useEffect, useState, useCallback } from 'react';
import { useToast } from './useToast';
import { checkHealth, HealthStatus } from '../services/health';

export function useHealthCheck() {
  const [status, setStatus] = useState<HealthStatus | null>(null);
  const { addToast } = useToast();

  useEffect(() => {
    let cancelled = false;
    checkHealth().then((result) => {
      if (cancelled) return;
      setStatus(result);
      if (!result.isLlmAvailable) {
        addToast(
          'No LLM backend detected — imports and extractions will fail. Configure NARRATIVE_INFERENCE_URL to enable.',
          'error',
        );
      }
    });
    return () => {
      cancelled = true;
    };
  }, [addToast]);

  const checkBeforeImport = useCallback(async (): Promise<boolean> => {
    const result = await checkHealth();
    setStatus(result);
    if (!result.isLlmAvailable) {
      addToast('LLM backend unavailable — import will likely fail.', 'error');
    }
    return true;
  }, [addToast]);

  return { isLlmAvailable: status?.isLlmAvailable ?? null, checkBeforeImport };
}
