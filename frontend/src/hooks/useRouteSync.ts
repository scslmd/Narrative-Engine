import { useEffect } from 'react';
import { matchPath, useLocation } from 'react-router-dom';
import type { WorkspaceMode } from '../routes';
import { useUIStore } from '../stores/uiStore';

/**
 * Hook that synchronizes route state with UI store.
 * Route is the source of truth - this ensures deep links and refreshes work correctly.
 */
export function useRouteSync() {
  const location = useLocation();
  const { setMode, setProjectId, setChapterId, setJobId } = useUIStore();

  useEffect(() => {
    // Try inspect with jobId pattern first (most specific)
    let match: ReturnType<typeof matchPath> | null = null;
    
    match = matchPath('/workspace/:projectId/inspect/:jobId?', location.pathname);
    
    if (match) {
      const params = match.params as { projectId: string; jobId?: string };
      setProjectId(params.projectId);
      setMode('inspect');
      setJobId(params.jobId || null);
      return;
    }

    // Try write with chapterId pattern  
    match = matchPath('/workspace/:projectId/write/:chapterId?', location.pathname);
    
    if (match) {
      const params = match.params as { projectId: string; chapterId?: string };
      setProjectId(params.projectId);
      setMode('write');
      setChapterId(params.chapterId || null);
      return;
    }

    // Try standard pattern for plan/review
    match = matchPath('/workspace/:projectId/:mode?', location.pathname);

    if (match) {
      const params = match.params as { projectId: string; mode?: WorkspaceMode };
      
      // Set project ID
      setProjectId(params.projectId);
      
      // Derive mode from route segment or default to 'plan'
      const derivedMode: WorkspaceMode = (params.mode as WorkspaceMode) || 'plan';
      setMode(derivedMode);
    } else {
      // Not in workspace - reset state
      setProjectId(null);
      setMode('plan');
      setChapterId(null);
      setJobId(null);
    }
  }, [location.pathname, setMode, setProjectId, setChapterId, setJobId]);
}
