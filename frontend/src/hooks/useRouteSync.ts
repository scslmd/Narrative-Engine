import { useEffect } from 'react';
import { matchPath, useLocation } from 'react-router-dom';
import type { WorkspaceMode } from '../routes';
import { useUIStore } from '../stores/uiStore';

/**
 * Hook that synchronizes route state with UI store.
 * After Phase 4 route migration, all workspace routes resolve to 'studio' mode.
 * Deep-link params (tab, jobId, chapterId) are handled by usePanelUrlSync in StudioView.
 */
export function useRouteSync() {
  const location = useLocation();
  const { setMode, setProjectId, setChapterId, setJobId } = useUIStore();

  useEffect(() => {
    const match = matchPath('/workspace/:projectId/:segment?', location.pathname);

    if (match) {
      const params = match.params as { projectId: string; segment?: string };
      setProjectId(params.projectId);
      // Keep mode derivation from `segment` for redirect routes to avoid flash:
      // redirect routes (plan, review, etc.) will render briefly before Navigate fires,
      // so mode should reflect the segment until the redirect completes.
      const segment = params.segment;
      if (segment === 'studio' || !segment) {
        setMode('studio');
      } else {
        setMode(segment as WorkspaceMode);
      }
      setChapterId(null);
      setJobId(null);
    } else {
      setProjectId(null);
      setMode('plan');
      setChapterId(null);
      setJobId(null);
    }
  }, [location.pathname, setMode, setProjectId, setChapterId, setJobId]);
}
