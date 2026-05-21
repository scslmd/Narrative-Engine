import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useStudioStore } from '../stores/studioStore';
import type { StudioPanelKey } from '../stores/studioStore';
import { useUIStore } from '../stores/uiStore';

interface PanelUrlSyncOptions {
  projectId: string | null;
  /** Called when URL contains ?jobId=XXX on mount */
  onJobId?: (jobId: string | null) => void;
  /** Called when URL contains ?chapterId=XXX on mount */
  onChapterId?: (chapterId: string | null) => void;
  /** Called when URL contains ?subtab=XXX on mount */
  onSubtab?: (subtab: string | null) => void;
}

/**
 * Syncs active panel to URL query params and reads deep-link params on mount.
 * - On mount: reads ?tab=, ?jobId=, ?chapterId=, ?subtab= from URL
 * - On active panel change: writes ?tab= to URL
 * - Uses replace: true to avoid polluting browser history on panel clicks
 */
export function usePanelUrlSync(options: PanelUrlSyncOptions) {
  const [searchParams, setSearchParams] = useSearchParams();
  const activePanel = useStudioStore((s) => s.activePanel);
  const addPanel = useStudioStore((s) => s.addPanel);
  const bringToFront = useStudioStore((s) => s.bringToFront);
  const setJobId = useUIStore((s) => s.setJobId);

  // READ: On mount, process deep-link params from URL
  useEffect(() => {
    if (!options.projectId) return;

    const tab = searchParams.get('tab');
    const jobId = searchParams.get('jobId');
    const chapterId = searchParams.get('chapterId');
    const subtab = searchParams.get('subtab');

    // Validate tab against known panel keys before casting
    const validKeys = ['structure', 'chapters', 'ideas', 'canon', 'generation', 'manuscripts', 'drafts', 'characters', 'relationships', 'worldBible', 'arcs', 'notes', 'jobs', 'suggestions', 'review', 'inspect'] as const;
    const panelKey = tab && validKeys.includes(tab as typeof validKeys[number])
      ? tab as StudioPanelKey
      : 'suggestions';

    // Read current layout from store at effect time (after loadLayout has run)
    const currentLayout = useStudioStore.getState().layout;
    const existingPanelId = Object.values(currentLayout.panels).find(
      (p) => p.key === panelKey && p.visible
    )?.id;

    if (existingPanelId) {
      bringToFront(existingPanelId);
    } else {
      // Only create if no panels exist at all (prevents duplicates with loadLayout)
      const anyPanel = Object.values(currentLayout.panels).find((p) => p.visible);
      if (!anyPanel) {
        addPanel(panelKey);
      }
    }

    // Pass through panel-specific params
    if (jobId) {
      setJobId(jobId);
      options.onJobId?.(jobId);
    }
    if (chapterId) {
      options.onChapterId?.(chapterId);
    }
    if (subtab) {
      options.onSubtab?.(subtab);
    }
    // NOTE: intentionally empty deps — this effect should only run on mount to read initial URL params
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only on mount

  // WRITE: When active panel changes, update URL ?tab= param
  // searchParams intentionally excluded from deps to prevent infinite loop
  // The updater function reads from `prev` (latest state), not from closure.
  useEffect(() => {
    if (!options.projectId || !activePanel) return;
    setSearchParams(
      (prev) => {
        prev.set('tab', activePanel);
        // Clean up panel-specific params that no longer apply
        // NOTE: read from `prev` everywhere to avoid stale closure over `searchParams`
        const currentTab = prev.get('tab');
        if (currentTab === 'inspect' && !prev.get('jobId')) {
          // Keep jobId if inspect is active
        } else if (currentTab !== 'inspect') {
          prev.delete('jobId');
        }
        if (currentTab !== 'manuscripts' && currentTab !== 'drafts') {
          prev.delete('chapterId');
        }
        if (currentTab !== 'canon') {
          prev.delete('subtab');
        }
        return prev;
      },
      { replace: true },
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePanel, setSearchParams]);
}
